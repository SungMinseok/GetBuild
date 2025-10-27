"""QuickBuild - 스케줄 중심 UI (v2)"""
import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QLabel, QMessageBox, QTextEdit,
                             QMenuBar, QAction, QSplitter, QFrame, QProgressDialog)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QIcon
from datetime import datetime
import subprocess
import zipfile

# Core 모듈 import
from core import ConfigManager, ScheduleManager, BuildOperations, ScheduleWorkerThread
from core.aws_manager import AWSManager

# UI 모듈 import
from ui import ScheduleDialog, ScheduleItemWidget

# 기존 모듈 import
from makelog import log_execution
from exporter import export_upload_result


class QuickBuildApp(QMainWindow):
    """QuickBuild 메인 애플리케이션 (스케줄 중심)"""
    
    def __init__(self):
        super().__init__()
        
        # 파일 경로
        self.settings_file = 'settings.json'
        self.config_file = 'config.json'
        self.schedule_file = 'schedule.json'
        
        # Core 매니저 초기화
        self.config_mgr = ConfigManager(self.config_file, self.settings_file)
        self.schedule_mgr = ScheduleManager(self.schedule_file)
        self.build_ops = BuildOperations()
        
        # 실행 중인 워커 스레드 관리
        self.running_workers = {}  # {schedule_id: worker_thread}
        
        # 스케줄 위젯 매핑 (상태 업데이트용)
        self.schedule_widgets = {}  # {schedule_id: ScheduleItemWidget}
        
        # 마지막 실행 시간 (중복 방지)
        self.last_check_time = None
        
        # 실행 옵션 목록
        self.execution_options = [
            '클라복사', '전체복사', '서버업로드및패치', '서버업로드', 
            '서버패치', '서버삭제', '서버복사', '빌드굽기', '테스트(로그)', 'TEST'
        ]
        
        # UI 초기화
        self.init_ui()
        
        # 타이머 시작 (스케줄 체크)
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_schedules)
        self.check_timer.start(1000)  # 1초마다 체크
        
        # 로그
        self.log("QuickBuild 시작")
    
    def init_ui(self):
        """UI 초기화"""
        # 개발/배포 모드 구분
        is_dev_mode = self.is_running_from_python()
        dev_tag = " [개발용]" if is_dev_mode else ""
        
        self.setWindowTitle(f'QuickBuild {self.read_version()}{dev_tag}')
        self.setWindowIcon(QIcon('ico.ico'))
        self.setGeometry(200, 200, 1000, 700)
        
        # 메뉴바 생성
        self.create_menu_bar()
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # 상단: 제목 + 버튼
        header = self.create_header()
        main_layout.addWidget(header)
        
        # 스플리터 (스케줄 리스트 + 로그)
        splitter = QSplitter(Qt.Vertical)
        
        # 스케줄 리스트 영역
        schedule_area = self.create_schedule_area()
        splitter.addWidget(schedule_area)
        
        # 로그 영역
        log_area = self.create_log_area()
        splitter.addWidget(log_area)
        
        splitter.setStretchFactor(0, 2)  # 스케줄 영역이 더 크게
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        central_widget.setLayout(main_layout)
        
        # 스케줄 목록 갱신
        self.refresh_schedule_list()
        
        # 스타일 적용
        #self.load_stylesheet()
    
    def create_menu_bar(self):
        """메뉴바 생성"""
        menu_bar = self.menuBar()
        
        # 메뉴
        menu = menu_bar.addMenu("메뉴")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        config_action = QAction("설정 파일 열기", self)
        config_action.triggered.connect(lambda: os.startfile(self.config_file))
        menu.addAction(config_action)
        
        update_action = QAction("업데이트 확인", self)
        update_action.triggered.connect(self.check_update)
        menu.addAction(update_action)
        
        # 버전 표시
        version_label = QLabel(f"Version: {self.read_version()}")
        version_label.setStyleSheet("color: #cccccc; margin-right: 10px; font-weight: bold;")
        menu_bar.setCornerWidget(version_label, Qt.TopRightCorner)
    
    def create_header(self) -> QWidget:
        """상단 헤더 생성"""
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)
        
        # 헤더
        header = QFrame()
        header.setFrameShape(QFrame.StyledPanel)
        header.setFixedHeight(40)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 제목
        title_label = QLabel("📅 스케줄")
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #2196F3;")
        layout.addWidget(title_label)
        
        # 실행 상태 요약
        self.status_summary_label = QLabel("실행 중: 0개")
        self.status_summary_label.setStyleSheet("""
            background-color: #E3F2FD;
            padding: 5px 15px;
            border-radius: 10px;
            font-weight: bold;
            color: #1976D2;
        """)
        layout.addWidget(self.status_summary_label)
        
        layout.addStretch()
        
        # 버튼들
        self.new_schedule_btn = QPushButton("➕ 새 스케줄")
        self.new_schedule_btn.setFixedSize(130, 30)
        self.new_schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.new_schedule_btn.clicked.connect(self.create_new_schedule)
        layout.addWidget(self.new_schedule_btn)

        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.setFixedSize(130, 30)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_schedule_list)
        layout.addWidget(self.refresh_btn)
        
        header.setLayout(layout)
        container_layout.addWidget(header)
        container.setLayout(container_layout)
        return container
    
    def create_schedule_area(self) -> QWidget:
        """스케줄 리스트 영역 생성"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # 스케줄 컨테이너
        self.schedule_container = QWidget()
        self.schedule_layout = QVBoxLayout()
        self.schedule_layout.setSpacing(10)
        self.schedule_layout.setContentsMargins(10, 10, 10, 10)
        self.schedule_container.setLayout(self.schedule_layout)
        
        scroll.setWidget(self.schedule_container)
        layout.addWidget(scroll)
        
        container.setLayout(layout)
        return container
    
    def create_log_area(self) -> QWidget:
        """로그 영역 생성"""
        container = QFrame()
        container.setFrameShape(QFrame.StyledPanel)

        container.setFixedHeight(300)
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 로그 제목
        log_label = QLabel("📋 실행 로그")
        log_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        layout.addWidget(log_label)
        
        # 로그 텍스트
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
       # self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        # 로그 클리어 버튼
        clear_btn = QPushButton("로그 지우기")
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        layout.addWidget(clear_btn, alignment=Qt.AlignRight)
        
        container.setLayout(layout)
        return container
    
    def refresh_schedule_list(self):
        """스케줄 목록 새로고침"""
        # 기존 위젯 모두 제거
        self.schedule_widgets.clear()
        while self.schedule_layout.count():
            child = self.schedule_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 스케줄 로드
        schedules = self.schedule_mgr.load_schedules()
        
        if not schedules:
            # 빈 상태 표시
            empty_label = QLabel("등록된 스케줄이 없습니다.\n'새 스케줄' 버튼을 클릭하여 스케줄을 추가하세요.")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #999; font-size: 12pt; padding: 50px;")
            self.schedule_layout.addWidget(empty_label)
        else:
            # 시간순 정렬
            schedules.sort(key=lambda x: x.get('time', ''))
            
            # 각 스케줄 위젯 추가
            for schedule in schedules:
                item_widget = ScheduleItemWidget(schedule)
                schedule_id = schedule.get('id', '')
                
                # 위젯 매핑 저장
                if schedule_id:
                    self.schedule_widgets[schedule_id] = item_widget
                
                # 시그널 연결
                item_widget.edit_requested.connect(self.edit_schedule)
                item_widget.delete_requested.connect(self.delete_schedule)
                item_widget.toggle_requested.connect(self.toggle_schedule)
                item_widget.run_requested.connect(self.run_schedule_manually)
                item_widget.copy_requested.connect(self.copy_schedule)
                
                # 현재 실행 중인 스케줄이면 상태 표시
                if schedule_id in self.running_workers:
                    item_widget.set_running_status(True, "실행 중...")
                
                self.schedule_layout.addWidget(item_widget)
        
        self.schedule_layout.addStretch()
        self.log(f"스케줄 목록 갱신 완료 ({len(schedules)}개)")
    
    def create_new_schedule(self):
        """새 스케줄 생성"""
        buildnames = self.config_mgr.get_buildnames()
        settings = self.config_mgr.load_settings()
        
        dialog = ScheduleDialog(
            parent=self,
            schedule=None,
            buildnames=buildnames,
            options=self.execution_options,
            default_src_path=settings.get('input_box1', r'\\pubg-pds\PBB\Builds'),
            default_dest_path=settings.get('input_box2', 'C:/mybuild')
        )
        
        if dialog.exec_() == dialog.Accepted:
            schedule_data = dialog.get_schedule_data()
            
            # 스케줄 추가 (경로 정보 포함)
            schedules = self.schedule_mgr.load_schedules()
            schedule_id = str(__import__('uuid').uuid4())
            
            new_schedule = {
                'id': schedule_id,
                'name': schedule_data['name'],
                'time': schedule_data['time'],
                'option': schedule_data['option'],
                'src_path': schedule_data['src_path'],
                'dest_path': schedule_data['dest_path'],
                'buildname': schedule_data['buildname'],
                'awsurl': schedule_data['awsurl'],
                'branch': schedule_data['branch'],
                'repeat_type': schedule_data['repeat_type'],
                'repeat_days': schedule_data['repeat_days'],
                'enabled': schedule_data['enabled'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            schedules.append(new_schedule)
            self.schedule_mgr.save_schedules(schedules)
            
            self.log(f"새 스케줄 생성: {schedule_data['name']}")
            self.refresh_schedule_list()
    
    def edit_schedule(self, schedule_id: str):
        """스케줄 편집"""
        schedule = self.schedule_mgr.get_schedule_by_id(schedule_id)
        if not schedule:
            QMessageBox.warning(self, "오류", "스케줄을 찾을 수 없습니다.")
            return
        
        buildnames = self.config_mgr.get_buildnames()
        settings = self.config_mgr.load_settings()
        
        dialog = ScheduleDialog(
            parent=self,
            schedule=schedule,
            buildnames=buildnames,
            options=self.execution_options,
            default_src_path=settings.get('input_box1', r'\\pubg-pds\PBB\Builds'),
            default_dest_path=settings.get('input_box2', 'C:/mybuild')
        )
        
        if dialog.exec_() == dialog.Accepted:
            schedule_data = dialog.get_schedule_data()
            self.schedule_mgr.update_schedule(schedule_id, schedule_data)
            self.log(f"스케줄 수정: {schedule_data['name']}")
            self.refresh_schedule_list()
    
    def delete_schedule(self, schedule_id: str):
        """스케줄 삭제"""
        schedule = self.schedule_mgr.get_schedule_by_id(schedule_id)
        schedule_name = schedule.get('name', 'Unknown') if schedule else 'Unknown'
        
        reply = QMessageBox.question(
            self,
            "스케줄 삭제",
            f"'{schedule_name}' 스케줄을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 일반 삭제 시도
                success = self.schedule_mgr.delete_schedule(schedule_id)
                if success:
                    self.log(f"스케줄 삭제: {schedule_name}")
                    self.refresh_schedule_list()
                else:
                    self.log(f"스케줄 삭제 실패: {schedule_name}")
            except Exception as e:
                # 오류 발생 시 강제 삭제 옵션 제공
                reply2 = QMessageBox.question(
                    self,
                    "삭제 오류",
                    f"스케줄 삭제 중 오류 발생:\n{str(e)}\n\n강제로 모든 스케줄을 초기화하시겠습니까?\n(백업이 생성됩니다)",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply2 == QMessageBox.Yes:
                    if self.schedule_mgr.delete_schedule(schedule_id, force=True):
                        self.log(f"[강제 삭제] 스케줄 파일 초기화됨")
                        self.refresh_schedule_list()
                    else:
                        QMessageBox.critical(self, "오류", "강제 삭제에 실패했습니다.")
    
    def copy_schedule(self, schedule_id: str):
        """스케줄 복사"""
        schedule = self.schedule_mgr.get_schedule_by_id(schedule_id)
        if not schedule:
            QMessageBox.warning(self, "오류", "스케줄을 찾을 수 없습니다.")
            return
        
        new_id = self.schedule_mgr.copy_schedule(schedule_id)
        if new_id:
            self.log(f"스케줄 복사: {schedule.get('name', 'Unknown')} → {schedule.get('name', 'Unknown')} (복사본)")
            self.refresh_schedule_list()
            QMessageBox.information(self, "복사 완료", f"스케줄이 복사되었습니다.\n새 스케줄: {schedule.get('name', 'Unknown')} (복사본)")
        else:
            QMessageBox.warning(self, "오류", "스케줄 복사에 실패했습니다.")
    
    def toggle_schedule(self, schedule_id: str):
        """스케줄 활성화/비활성화 토글"""
        new_state = self.schedule_mgr.toggle_schedule(schedule_id)
        if new_state is not None:
            state_str = "활성화" if new_state else "비활성화"
            self.log(f"스케줄 {state_str}: {schedule_id[:8]}...")
            self.refresh_schedule_list()
    
    def run_schedule_manually(self, schedule_id: str):
        """스케줄 수동 실행"""
        schedule = self.schedule_mgr.get_schedule_by_id(schedule_id)
        if not schedule:
            QMessageBox.warning(self, "오류", "스케줄을 찾을 수 없습니다.")
            return
        
        self.log(f"[수동 실행] {schedule.get('name', 'Unknown')}")
        self.execute_schedule(schedule)
    
    def check_schedules(self):
        """스케줄 체크 (1초마다 호출)"""
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        # 같은 분에는 한 번만 체크
        if self.last_check_time == current_time_str:
            return
        
        self.last_check_time = current_time_str
        
        # 실행할 스케줄 조회
        due_schedules = self.schedule_mgr.get_due_schedules(current_time_str, now)
        
        for schedule in due_schedules:
            self.log(f"[자동 실행] {schedule.get('name', 'Unknown')} - {current_time_str}")
            self.execute_schedule(schedule)
    
    def execute_schedule(self, schedule: dict):
        """스케줄 실행 (QThread)"""
        schedule_id = schedule.get('id', '')
        
        # 이미 실행 중이면 스킵
        if schedule_id in self.running_workers:
            self.log(f"[실행 중] {schedule.get('name', 'Unknown')} - 이미 실행 중입니다.")
            return
        
        # 작업 함수 생성
        option = schedule.get('option', '')
        buildname = schedule.get('buildname', '')
        awsurl = schedule.get('awsurl', '')
        branch = schedule.get('branch', '')
        src_path = schedule.get('src_path', '')
        dest_path = schedule.get('dest_path', '')
        
        # 실행할 함수 결정
        task_func = lambda: self.execute_option(option, buildname, awsurl, branch, src_path, dest_path)
        
        # 워커 스레드 생성
        worker = ScheduleWorkerThread(schedule, task_func)
        
        # 시그널 연결
        worker.log.connect(self.log)
        worker.schedule_finished.connect(self.on_schedule_finished)
        
        # 스레드 시작
        self.running_workers[schedule_id] = worker
        worker.start()
        
        # UI 상태 업데이트
        if schedule_id in self.schedule_widgets:
            self.schedule_widgets[schedule_id].set_running_status(True, f"{option} 실행 중...")
        
        # 상태 요약 업데이트
        self.update_status_summary()
    
    def find_latest_build(self, src_folder: str, buildname: str) -> str:
        """
        빌드명으로 최신 빌드 폴더 찾기
        
        Args:
            src_folder: 빌드 소스 경로
            buildname: 빌드명 (짧은 이름, 예: game_SEL, game_progression)
        
        Returns:
            전체 빌드 폴더명 (예: CompileBuild_DEV_game_SEL_271167_r306671)
        """
        if not os.path.isdir(src_folder):
            raise Exception(f'Source folder does not exist: {src_folder}')
        
        # src_folder에서 buildname이 포함된 폴더 찾기
        matching_folders = []
        try:
            for folder in os.listdir(src_folder):
                folder_path = os.path.join(src_folder, folder)
                if os.path.isdir(folder_path) and buildname in folder:
                    matching_folders.append(folder)
        except Exception as e:
            raise Exception(f'Failed to list folders in {src_folder}: {e}')
        
        if not matching_folders:
            raise Exception(f'No build folders found matching: {buildname}')
        
        # 최신 폴더 찾기 (수정 시간 기준)
        matching_folders.sort(key=lambda x: os.path.getmtime(os.path.join(src_folder, x)), reverse=True)
        latest_folder = matching_folders[0]
        
        print(f"[find_latest_build] Found {len(matching_folders)} matching folders, latest: {latest_folder}")
        return latest_folder
    
    def copy_folder_direct(self, src_folder: str, dest_folder: str, target_folder: str, target_name: str) -> str:
        """
        폴더 복사 (스레드 안전 버전)
        
        Args:
            src_folder: 빌드 소스 경로 (예: \\\\pubg-pds\\PBB\\Builds)
            dest_folder: 로컬 저장 경로 (예: C:/mybuild)
            target_folder: 빌드 전체명 (예: game_SEL_232323)
            target_name: 복사할 폴더명 (예: WindowsClient, WindowsServer, '' for all)
        """
        folder_to_copy = os.path.join(src_folder, target_folder, target_name) if target_name else os.path.join(src_folder, target_folder)
        
        print(f"[copy_folder_direct] src: {folder_to_copy}")
        print(f"[copy_folder_direct] dest: {os.path.join(dest_folder, target_folder, target_name)}")
        
        if not os.path.isdir(src_folder):
            raise Exception(f'Source path is not valid: {src_folder}')
        if not os.path.isdir(dest_folder):
            raise Exception(f'Destination path is not valid: {dest_folder}')
        if not os.path.isdir(folder_to_copy):
            raise Exception(f'Folder to copy does not exist: {folder_to_copy}')
        
        # 목적지 디렉토리 생성
        main_path = os.path.join(dest_folder, target_folder)
        if not os.path.exists(main_path):
            os.makedirs(main_path)
        
        dest_path = os.path.join(dest_folder, target_folder, target_name) if target_name else main_path
        
        # 파일 복사
        file_count = 0
        for root, dirs, files in os.walk(folder_to_copy):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(root, folder_to_copy)
                dest_dir = os.path.join(dest_path, rel_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                shutil.copy2(src_file, dest_dir)
                file_count += 1
        
        return f"{file_count} files copied"
    
    def execute_option(self, option: str, buildname: str, awsurl: str, branch: str, 
                      src_path: str = '', dest_path: str = '') -> str:
        """
        실행 옵션 처리 (실제 작업)
        이 함수는 QThread 내에서 실행됩니다.
        """
        log_execution()  # 실행 로그
        
        try:
            # 경로 정보: 스케줄에 지정된 경로 우선, 없으면 settings에서 가져오기
            if not src_path or not dest_path:
                settings = self.config_mgr.load_settings()
                src_folder = src_path or settings.get('input_box1', r'\\pubg-pds\PBB\Builds')
                dest_folder = dest_path or settings.get('input_box2', 'C:/mybuild')
            else:
                src_folder = src_path
                dest_folder = dest_path
            
            print(f"[execute_option] option: {option}, buildname: {buildname}")
            print(f"[execute_option] src_folder: {src_folder}, dest_folder: {dest_folder}")
            
            if option == "테스트(로그)":
                # 테스트 로그만 출력
                test_log = f"""
[테스트 로그 출력]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
실행 옵션: {option}
빌드명: {buildname}
AWS URL: {awsurl}
Branch: {branch}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                print(test_log)
                return "테스트 로그 출력 완료"
            
            elif option == "클라복사":
                # buildname이 짧은 이름이면 전체 빌드명 찾기
                full_buildname = self.find_latest_build(src_folder, buildname)
                print(f"[execute_option] 클라복사 - full_buildname: {full_buildname}")
                
                # 실제 클라이언트 복사 로직
                result = self.copy_folder_direct(src_folder, dest_folder, full_buildname, 'WindowsClient')
                return f"클라복사 완료: {full_buildname} ({result})"
            
            elif option == "서버복사":
                # buildname이 짧은 이름이면 전체 빌드명 찾기
                full_buildname = self.find_latest_build(src_folder, buildname)
                print(f"[execute_option] 서버복사 - full_buildname: {full_buildname}")
                
                # 실제 서버 복사 로직
                result = self.copy_folder_direct(src_folder, dest_folder, full_buildname, 'WindowsServer')
                return f"서버복사 완료: {full_buildname} ({result})"
            
            elif option == "전체복사":
                # buildname이 짧은 이름이면 전체 빌드명 찾기
                full_buildname = self.find_latest_build(src_folder, buildname)
                print(f"[execute_option] 전체복사 - full_buildname: {full_buildname}")
                
                # 실제 전체 복사 로직
                result = self.copy_folder_direct(src_folder, dest_folder, full_buildname, '')
                return f"전체복사 완료: {full_buildname} ({result})"
            
            elif option == "서버패치":
                # AWS 패치 실행
                if not awsurl:
                    raise Exception("AWS URL이 설정되지 않았습니다.")
                
                # Chrome 프로세스 종료
                os.system('taskkill /F /IM chrome.exe /T 2>nul')
                os.system('taskkill /F /IM chromedriver.exe /T 2>nul')
                import time
                time.sleep(2)
                
                # 리비전 번호 추출 필요 (buildname에서)
                revision = self.build_ops.extract_revision_number(buildname)
                buildType = buildname.split('_')[1] if '_' in buildname else 'DEV'
                
                AWSManager.update_server_container(
                    driver=None,
                    revision=revision,
                    aws_link=awsurl,
                    branch=branch,
                    build_type=buildType,
                    is_debug=False,
                    full_build_name=buildname
                )
                return f"서버패치 완료: {awsurl}"
            
            elif option == "서버업로드":
                # TODO: 서버 업로드 로직
                # self.zip_folder(...) + AWSManager.upload_server_build(...)
                return f"서버업로드 완료: {buildname}"
            
            elif option == "서버업로드및패치":
                # TODO: 서버 업로드 + 패치
                return f"서버업로드및패치 완료: {buildname}"
            
            elif option == "빌드굽기":
                # TeamCity 빌드 실행
                AWSManager.run_teamcity_build(driver=None, branch=branch or buildname)
                return f"빌드굽기 완료: {branch or buildname}"
            
            else:
                return f"{option} 실행 완료 (미구현)"
        
        except Exception as e:
            raise Exception(f"{option} 실행 오류: {str(e)}")
    
    def on_schedule_finished(self, schedule: dict, success: bool, message: str):
        """스케줄 실행 완료"""
        schedule_id = schedule.get('id', '')
        schedule_name = schedule.get('name', 'Unknown')
        
        # 워커 제거
        if schedule_id in self.running_workers:
            del self.running_workers[schedule_id]
        
        # UI 상태 업데이트
        if schedule_id in self.schedule_widgets:
            if success:
                self.schedule_widgets[schedule_id].set_running_status(False, message)
                # 3초 후 완료 메시지 숨기기
                QTimer.singleShot(3000, lambda: self.hide_status_message(schedule_id))
            else:
                self.schedule_widgets[schedule_id].set_running_status(False, f"오류: {message}")
                # 5초 후 오류 메시지 숨기기
                QTimer.singleShot(5000, lambda: self.hide_status_message(schedule_id))
        
        # 로그
        if success:
            self.log(f"✅ 완료: {schedule_name} - {message}")
        else:
            self.log(f"❌ 실패: {schedule_name} - {message}")
        
        # 상태 요약 업데이트
        self.update_status_summary()
    
    def hide_status_message(self, schedule_id: str):
        """상태 메시지 숨기기"""
        if schedule_id in self.schedule_widgets:
            widget = self.schedule_widgets[schedule_id]
            if not widget.is_running:  # 실행 중이 아닐 때만 숨김
                widget.status_label.setVisible(False)
    
    def update_status_summary(self):
        """상태 요약 업데이트"""
        running_count = len(self.running_workers)
        
        if running_count == 0:
            self.status_summary_label.setText("실행 중: 0개")
            self.status_summary_label.setStyleSheet("""
                background-color: #E3F2FD;
                padding: 5px 15px;
                border-radius: 10px;
                font-weight: bold;
                color: #1976D2;
            """)
        else:
            # 실행 중인 스케줄 목록 생성
            running_names = []
            for schedule_id in self.running_workers.keys():
                schedule = self.schedule_mgr.get_schedule_by_id(schedule_id)
                if schedule:
                    name = schedule.get('name', 'Unknown')
                    option = schedule.get('option', '')
                    running_names.append(f"{name} ({option})")
            
            summary_text = f"🔄 실행 중: {running_count}개"
            # if running_names:
            #     summary_text += f"\n{', '.join(running_names[:3])}"  # 최대 3개만 표시
            #     if len(running_names) > 3:
            #         summary_text += f" 외 {len(running_names) - 3}개"
            
            self.status_summary_label.setText(summary_text)
            self.status_summary_label.setStyleSheet("""
                background-color: #FFF3E0;
                padding: 5px 15px;
                border-radius: 10px;
                font-weight: bold;
                color: #F57C00;
            """)
    
    def log(self, message: str):
        """로그 출력 (화면 + 파일)"""
        now = datetime.now()
        timestamp = now.strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        
        # 화면 출력
        self.log_text.append(log_line)
        print(log_line)
        
        # 파일 저장 (날짜별)
        try:
            log_dir = 'log'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_filename = f"log_{now.strftime('%Y%m%d')}.txt"
            log_filepath = os.path.join(log_dir, log_filename)
            
            # 이어쓰기 모드로 저장
            with open(log_filepath, 'a', encoding='utf-8') as f:
                f.write(f"{log_line}\n")
        except Exception as e:
            print(f"로그 파일 저장 오류: {e}")
    
    def load_stylesheet(self):
        """스타일시트 로드"""
        try:
            with open("qss/pbb.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except:
            pass
    
    def read_version(self) -> str:
        """
        버전 읽기 및 포맷 변경
        기존: 2.0.1
        새로운: 3.0-YY.MM.DD.HHMM
        """
        try:
            with open("version.txt", "r", encoding="utf-8") as f:
                version_content = f.read().strip()
            
            # version.txt의 내용이 새 형식인지 확인 (하이픈 포함)
            if '-' in version_content:
                return version_content
            
            # 기존 형식이면 새 형식으로 변환하여 반환 (파일은 수정 안 함)
            # 현재 시각 기준으로 생성
            from datetime import datetime
            now = datetime.now()
            major_minor = version_content.split('.')[0] if '.' in version_content else version_content
            new_format = f"{major_minor}-{now.strftime('%y.%m.%d.%H%M')}"
            return new_format
        except:
            return "3.0-25.10.26.1805"
    
    def is_running_from_python(self) -> bool:
        """Python 스크립트로 실행 중인지 확인 (개발 모드)"""
        import sys
        # sys.frozen이 없거나 False면 Python 스크립트로 실행 중
        return not getattr(sys, 'frozen', False)
    
    def show_about(self):
        """About 다이얼로그"""
        QMessageBox.information(
            self,
            "About QuickBuild",
            f"QuickBuild v2\nVersion: {self.read_version()}\n\n스케줄 기반 빌드 관리 도구"
        )
    
    def check_update(self):
        """업데이트 확인"""
        if os.path.exists("QuickBuild_updater.exe"):
            subprocess.call(["QuickBuild_updater.exe"])
        else:
            subprocess.call([sys.executable, "updater.py"])


if __name__ == '__main__':
    # 업데이터 실행 (silent)
    if os.path.exists("QuickBuild_updater.exe"):
        subprocess.call(["QuickBuild_updater.exe", "--silent"])
    else:
        subprocess.call([sys.executable, "updater.py", "--silent"])
    
    app = QApplication(sys.argv)
    main_window = QuickBuildApp()
    main_window.show()
    sys.exit(app.exec_())

