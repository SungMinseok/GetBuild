"""QuickBuild - 스케줄 중심 UI (v2)"""
import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QLabel, QMessageBox, QTextEdit,
                             QMenuBar, QAction, QSplitter, QFrame, QProgressDialog, QLineEdit, QComboBox, QDialog)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt5.QtGui import QIcon
from datetime import datetime
import subprocess
import zipfile
import time
import re

# Core 모듈 import
from core import ConfigManager, ScheduleManager, BuildOperations, ScheduleWorkerThread
from core.aws_manager import AWSManager
from core.worker_thread import simplify_error_message

# UI 모듈 import
from ui import ScheduleDialog, ScheduleItemWidget, SettingsDialog
# 피드백 다이얼로그 - Slack 직접 전송 방식 (암호화된 토큰 사용)
try:
    from ui.feedback_dialog_slack import FeedbackDialogSlack as FeedbackDialog
except ImportError:
    from ui.feedback_dialog import FeedbackDialog

# 기존 모듈 import
from makelog import log_execution
from exporter import export_upload_result
from slack import send_schedule_notification

# 업데이트 모듈 import
try:
    from updater import AutoUpdater
    from update_dialogs import UpdateNotificationDialog, DownloadProgressDialog, AboutDialog
except ImportError:
    AutoUpdater = None
    UpdateNotificationDialog = None
    DownloadProgressDialog = None
    AboutDialog = None
# Qt 플랫폼 플러그인 경로 설정 (PyQt5 import 전에 설정 필요)
if hasattr(sys, '_MEIPASS'):
    # PyInstaller로 빌드된 실행 파일인 경우
    qt_plugin_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt5', 'plugins')
else:
    # 개발 환경인 경우
    venv_path = os.path.join(os.path.dirname(__file__), '.venv')
    qt_plugin_path = os.path.join(venv_path, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins')

os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt_plugin_path, 'platforms')

class QuickBuildApp(QMainWindow):
    """QuickBuild 메인 애플리케이션 (스케줄 중심)"""
    
    # 업데이트 시그널
    update_check_result = pyqtSignal(bool, object, str)  # has_update, info, error_msg
    
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
        
        # 자동 업데이트 관리자
        self.auto_updater = AutoUpdater() if AutoUpdater else None
        if self.auto_updater:
            self.auto_updater.set_main_app(self)
            # 시그널 연결
            self.update_check_result.connect(self.on_update_check_result)
        
        # Debug 모드 플래그
        self.debug_mode = self.load_debug_mode()
        
        # 실행 옵션 목록
        self.execution_options = [
            '클라복사', '전체복사', '서버업로드및패치', '서버업로드', 
            '서버패치', '서버삭제', '서버복사', '빌드굽기', '테스트(로그)', 
            'Chrome프로세스정리', 'TEST'
        ]
        
        # UI 초기화
        self.init_ui()
        
        # 타이머 시작 (스케줄 체크)
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_schedules)
        self.check_timer.start(1000)  # 1초마다 체크
        
        # 로그
        self.log("QuickBuild 시작")
        
        # 앱 시작 500ms 후 업데이트 체크 (백그라운드) - 먼저 실행
        if self.auto_updater:
            QTimer.singleShot(500, self.check_for_updates_on_startup)
        
        # ChromeDriver 최초 설치 확인 (비동기) - 업데이트 확인 후 실행
        QTimer.singleShot(3000, self.check_chromedriver_on_startup)
    
    def init_ui(self):
        """UI 초기화"""
        # 개발/배포 모드 구분
        is_dev_mode = self.is_running_from_python()
        dev_tag = " [DEV]" if is_dev_mode else ""
        
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
        
        # config_action = QAction("설정 파일 열기", self)
        # config_action.triggered.connect(lambda: os.startfile(self.config_file))
        # menu.addAction(config_action)
        
        # Settings 메뉴 추가
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        update_action = QAction("업데이트 확인", self)
        update_action.triggered.connect(self.check_update)
        menu.addAction(update_action)
        
        # 버그 및 피드백 메뉴
        feedback_action = QAction("버그 및 피드백", self)
        feedback_action.triggered.connect(self.show_feedback_dialog)
        menu.addAction(feedback_action)
        
        # Dev 모드일 때만 배포 메뉴 추가
        if self.is_running_from_python():
            menu.addSeparator()
            deploy_action = QAction("🚀 빠른 빌드 및 배포", self)
            deploy_action.triggered.connect(self.show_deploy_dialog)
            menu.addAction(deploy_action)
        
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
        
        # 헤더 (첫 번째 줄)
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
        
        # 피드백 버튼 추가
        self.feedback_btn = QPushButton("💬 피드백")
        self.feedback_btn.setFixedSize(130, 30)
        self.feedback_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.feedback_btn.clicked.connect(self.show_feedback_dialog)
        layout.addWidget(self.feedback_btn)
        
        header.setLayout(layout)
        container_layout.addWidget(header)
        
        # 검색 영역 (두 번째 줄)
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.StyledPanel)
        search_frame.setFixedHeight(45)
        
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)
        
        # 검색 아이콘 라벨
        search_icon_label = QLabel("🔍")
        search_icon_label.setStyleSheet("font-size: 14pt;")
        search_layout.addWidget(search_icon_label)
        
        # 검색창
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("스케줄 이름으로 검색... (실시간 필터링)")
        self.search_input.setFixedHeight(30)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 2px solid #BDBDBD;
                border-radius: 5px;
                font-size: 10pt;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        # 텍스트 변경 시 실시간 필터링
        self.search_input.textChanged.connect(self.apply_filters)
        search_layout.addWidget(self.search_input, 1)
        
        # 실행 옵션 필터
        self.option_filter_combo = QComboBox()
        self.option_filter_combo.setFixedHeight(30)
        self.option_filter_combo.setFixedWidth(180)
        self.option_filter_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 2px solid #BDBDBD;
                border-radius: 5px;
                font-size: 10pt;
                background-color: white;
            }
            QComboBox:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.option_filter_combo.addItem("모든 옵션", "")
        for option in self.execution_options:
            self.option_filter_combo.addItem(option, option)
        self.option_filter_combo.currentIndexChanged.connect(self.apply_filters)
        search_layout.addWidget(self.option_filter_combo)
        
        # 활성화 여부 필터
        self.enabled_filter_combo = QComboBox()
        self.enabled_filter_combo.setFixedHeight(30)
        self.enabled_filter_combo.setFixedWidth(120)
        self.enabled_filter_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 2px solid #BDBDBD;
                border-radius: 5px;
                font-size: 10pt;
                background-color: white;
            }
            QComboBox:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.enabled_filter_combo.addItem("전체", "all")
        self.enabled_filter_combo.addItem("활성화", "enabled")
        self.enabled_filter_combo.addItem("비활성화", "disabled")
        self.enabled_filter_combo.currentIndexChanged.connect(self.apply_filters)
        search_layout.addWidget(self.enabled_filter_combo)
        
        # 검색 결과 카운트
        self.search_result_label = QLabel("")
        self.search_result_label.setStyleSheet("""
            color: #757575;
            font-size: 9pt;
            padding: 0 10px;
        """)
        search_layout.addWidget(self.search_result_label)
        
        # 초기화 버튼
        clear_btn = QPushButton("✖ 초기화")
        clear_btn.setFixedSize(80, 30)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        clear_btn.clicked.connect(self.clear_filters)
        search_layout.addWidget(clear_btn)
        
        search_frame.setLayout(search_layout)
        container_layout.addWidget(search_frame)
        
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
                item_widget.stop_requested.connect(self.stop_schedule)
                item_widget.copy_requested.connect(self.copy_schedule)
                
                # 현재 실행 중인 스케줄이면 상태 표시
                if schedule_id in self.running_workers:
                    item_widget.set_running_status(True, "실행 중...")
                
                self.schedule_layout.addWidget(item_widget)
        
        self.schedule_layout.addStretch()
        self.log(f"스케줄 목록 갱신 완료 ({len(schedules)}개)")
        
        # 필터가 있으면 필터링 적용
        if hasattr(self, 'search_input'):
            self.apply_filters()
    
    def apply_filters(self):
        """스케줄 필터링 (이름, 실행 옵션, 활성화 여부)"""
        search_text = self.search_input.text().strip().lower() if hasattr(self, 'search_input') else ""
        
        # 실행 옵션 필터
        option_filter = ""
        if hasattr(self, 'option_filter_combo'):
            option_filter = self.option_filter_combo.currentData()
        
        # 활성화 여부 필터
        enabled_filter = "all"
        if hasattr(self, 'enabled_filter_combo'):
            enabled_filter = self.enabled_filter_combo.currentData()
        
        visible_count = 0
        total_count = 0
        
        # 모든 스케줄 위젯 순회
        for i in range(self.schedule_layout.count()):
            item = self.schedule_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                
                # ScheduleItemWidget만 필터링
                if isinstance(widget, ScheduleItemWidget):
                    total_count += 1
                    
                    # 각 필터 조건 확인
                    schedule_name = widget.schedule.get('name', '').lower()
                    schedule_option = widget.schedule.get('option', '')
                    schedule_enabled = widget.schedule.get('enabled', True)
                    
                    # 이름 필터
                    name_match = not search_text or search_text in schedule_name
                    
                    # 실행 옵션 필터
                    option_match = not option_filter or schedule_option == option_filter
                    
                    # 활성화 여부 필터
                    if enabled_filter == "all":
                        enabled_match = True
                    elif enabled_filter == "enabled":
                        enabled_match = schedule_enabled == True
                    elif enabled_filter == "disabled":
                        enabled_match = schedule_enabled == False
                    else:
                        enabled_match = True
                    
                    # 모든 조건이 만족되면 표시
                    if name_match and option_match and enabled_match:
                        widget.setVisible(True)
                        visible_count += 1
                    else:
                        widget.setVisible(False)
        
        # 검색 결과 표시
        if search_text or option_filter or enabled_filter != "all":
            self.search_result_label.setText(f"{visible_count}/{total_count}개 표시")
            if visible_count == 0:
                filter_desc = []
                if search_text:
                    filter_desc.append(f"이름:'{search_text}'")
                if option_filter:
                    filter_desc.append(f"옵션:'{option_filter}'")
                if enabled_filter != "all":
                    filter_desc.append(f"상태:'{enabled_filter}'")
                self.log(f"🔍 필터 결과 없음: {', '.join(filter_desc)}")
        else:
            self.search_result_label.setText("")
    
    def clear_filters(self):
        """모든 필터 초기화"""
        self.search_input.clear()
        self.option_filter_combo.setCurrentIndex(0)
        self.enabled_filter_combo.setCurrentIndex(0)
        self.search_result_label.setText("")
        self.log("🔍 모든 필터 초기화")
    
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
    
    def stop_schedule(self, schedule_id: str):
        """스케줄 중지"""
        if schedule_id not in self.running_workers:
            QMessageBox.warning(self, "경고", "실행 중인 스케줄이 아닙니다.")
            return
        
        worker = self.running_workers[schedule_id]
        schedule = self.schedule_mgr.get_schedule_by_id(schedule_id)
        schedule_name = schedule.get('name', 'Unknown') if schedule else 'Unknown'
        
        # 중지 확인
        reply = QMessageBox.question(
            self,
            "스케줄 중지",
            f"'{schedule_name}' 스케줄을 중지하시겠습니까?\n\n진행 중인 작업이 중단됩니다.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.log(f"[중지 요청] {schedule_name}")
            
            # 워커 스레드 중지 (강제 종료)
            if worker.isRunning():
                worker.terminate()  # 스레드 강제 종료
                worker.wait(1000)  # 1초 대기
            
            # 워커 제거
            if schedule_id in self.running_workers:
                del self.running_workers[schedule_id]
            
            # UI 업데이트
            if schedule_id in self.schedule_widgets:
                self.schedule_widgets[schedule_id].set_running_status(False, "중지됨")
            
            # 상태 요약 업데이트
            self.update_status_summary()
            
            self.log(f"❌ 중지됨: {schedule_name}")
    
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
        
        # 빌드 모드 확인: 'latest' 또는 'fixed'
        build_mode = schedule.get('build_mode', 'latest')
        prefix = schedule.get('prefix', '')
        
        # 최신 모드일 경우 prefix로 최신 빌드 찾기
        if build_mode == 'latest' and prefix:
            try:
                # 경로 확인
                settings = self.config_mgr.load_settings()
                check_src = src_path or settings.get('input_box1', r'\\pubg-pds\PBB\Builds')
                
                # prefix 기준 최신 빌드 찾기
                buildname = self.find_latest_build(check_src, prefix)
                self.log(f"[최신 빌드 탐색] Prefix '{prefix}' → {buildname}")
            except Exception as e:
                self.log(f"[오류] 최신 빌드 탐색 실패: {e}")
                return
        
        # 실행할 함수 결정
        task_func = lambda: self.execute_option(option, buildname, awsurl, branch, src_path, dest_path)
        
        # 워커 스레드 생성 (Debug 모드이면 stdout 캡처)
        worker = ScheduleWorkerThread(schedule, task_func, capture_stdout=self.debug_mode)
        
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
        
        # 슬랙 알림 전송 (시작)
        # self.send_slack_notification_if_enabled(schedule, '시작', 
        #                                        f"옵션: {option}\n빌드: {buildname}")
    
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
        
        # 최신 폴더 찾기 (리비전 r 값 기준)
        def extract_revision_from_name(name: str) -> int:
            m = re.search(r'(?:^|_)r(\d+)(?:$|_)', name)
            if m:
                return int(m.group(1))
            m2 = re.search(r'r(\d+)', name)
            return int(m2.group(1)) if m2 else -1

        matching_folders.sort(
            key=lambda x: (
                extract_revision_from_name(x),
                os.path.getmtime(os.path.join(src_folder, x))
            ),
            reverse=True
        )
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
        
        # 파일 복사 (재시도 로직 포함)
        file_count = 0
        failed_files = []
        
        dir_count = 0
        for root, dirs, files in os.walk(folder_to_copy):
            # 디렉터리(빈 폴더 포함) 생성
            rel_path = os.path.relpath(root, folder_to_copy)
            current_dest_dir = os.path.join(dest_path, rel_path) if rel_path != '.' else dest_path
            if not os.path.exists(current_dest_dir):
                os.makedirs(current_dest_dir)
                dir_count += 1

            for d in dirs:
                sub_dir = os.path.join(current_dest_dir, d)
                if not os.path.exists(sub_dir):
                    os.makedirs(sub_dir)
                    dir_count += 1

            # 파일 복사
            for file in files:
                src_file = os.path.join(root, file)
                dest_dir = current_dest_dir
                
                # 파일 복사 시도 (최대 1번: 파일 사용중 등은 스킵)
                max_retries = 1
                success = False
                
                for attempt in range(max_retries):
                    try:
                        # 목적지 파일이 이미 존재하고 읽기 전용이면 속성 제거
                        dest_file = os.path.join(dest_dir, os.path.basename(src_file))
                        if os.path.exists(dest_file):
                            try:
                                os.chmod(dest_file, 0o777)
                            except:
                                pass
                        
                        # 파일 복사
                        shutil.copy2(src_file, dest_dir)
                        file_count += 1
                        success = True
                        break
                    except PermissionError as e:
                        if attempt < max_retries - 1:
                            retry_delay = (attempt + 1) * 0.5
                            print(f"[재시도 {attempt + 1}/{max_retries}] {file}: 파일 사용 중, {retry_delay}초 대기...")
                            time.sleep(retry_delay)
                        else:
                            print(f"[경고] {file}: 복사 실패 (파일 사용 중)")
                            failed_files.append(f"{file}")
                    except Exception as e:
                        print(f"[오류] {file}: {type(e).__name__}: {e}")
                        failed_files.append(f"{file}")
                        break
        
        # 결과 메시지 생성
        result = f"{file_count} files copied, {dir_count} dirs created"
        if failed_files:
            result += f" ⚠️ {len(failed_files)} files skipped (in use)"
            if len(failed_files) <= 5:
                result += f": {', '.join(failed_files)}"
        
        return result
    
    def execute_option(self, option: str, buildname: str, awsurl: str, branch: str, 
                      src_path: str = '', dest_path: str = '') -> str:
        """
        실행 옵션 처리 (실제 작업)
        이 함수는 QThread 내에서 실행됩니다.
        
        Args:
            buildname: 빌드명 (Prefix 또는 전체 빌드명)
                - 짧은 이름(예: game_SEL): find_latest_build로 최신 빌드 찾음
                - 전체 빌드명(예: CompileBuild_DEV_game_SEL_...): 그대로 사용
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
            
            # buildname이 실제 폴더인지 확인 (전체 빌드명인지 Prefix인지 판단)
            def is_full_buildname(name: str) -> bool:
                """전체 빌드명인지 확인 (실제 폴더 존재 여부로 판단)"""
                if not name:
                    return False
                full_path = os.path.join(src_folder, name)
                return os.path.isdir(full_path)
            
            # 전체 빌드명 결정
            def get_full_buildname(name: str) -> str:
                """buildname이 Prefix면 최신 빌드 찾기, 전체 빌드명이면 그대로 사용"""
                if is_full_buildname(name):
                    print(f"[get_full_buildname] 전체 빌드명 사용: {name}")
                    return name
                else:
                    print(f"[get_full_buildname] Prefix로 최신 빌드 탐색: {name}")
                    return self.find_latest_build(src_folder, name)
            
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
                return ""
            
            elif option == "클라복사":
                full_buildname = get_full_buildname(buildname)
                print(f"[execute_option] 클라복사 - full_buildname: {full_buildname}")
                
                # 실제 클라이언트 복사 로직
                result = self.copy_folder_direct(src_folder, dest_folder, full_buildname, 'WindowsClient')
                return f"클라복사 완료: {full_buildname} ({result})"
            
            elif option == "서버복사":
                full_buildname = get_full_buildname(buildname)
                print(f"[execute_option] 서버복사 - full_buildname: {full_buildname}")
                
                # 실제 서버 복사 로직
                result = self.copy_folder_direct(src_folder, dest_folder, full_buildname, 'WindowsServer')
                return f"서버복사 완료: {full_buildname} ({result})"
            
            elif option == "전체복사":
                full_buildname = get_full_buildname(buildname)
                print(f"[execute_option] 전체복사 - full_buildname: {full_buildname}")
                
                # 실제 전체 복사 로직
                result = self.copy_folder_direct(src_folder, dest_folder, full_buildname, '')
                return f"전체복사 완료: {full_buildname} ({result})"
            
            elif option == "서버패치":
                # AWS 패치 실행
                if not awsurl:
                    raise Exception("AWS URL이 설정되지 않았습니다.")
                
                # buildname이 이미 full_buildname이면 그대로 사용 (폴더 검색 없이)
                # 그렇지 않으면 get_full_buildname으로 폴더 검색
                if buildname and ('CompileBuild' in buildname or 'Compilebuild' in buildname):
                    # 이미 전체 빌드 이름임 (예: CompileBuild_DEV_game_SEL_25000_r300001)
                    full_buildname = buildname
                    print(f"[서버패치] 지정된 full_buildname 사용: {full_buildname}")
                else:
                    # 폴더에서 검색
                    full_buildname = get_full_buildname(buildname)
                    print(f"[서버패치] 검색된 full_buildname: {full_buildname}")
                
                # 리비전/타입 추출
                revision = self.build_ops.extract_revision_number(full_buildname)
                buildType = full_buildname.split('_')[1] if '_' in full_buildname else 'DEV'
                
                print(f"[서버패치] revision: {revision}, buildType: {buildType}, branch: {branch}")
                print(f"[서버패치] AWS URL: {awsurl}")
                
                # Chrome 프로세스 종료 후 재시작 (디버깅 포트 재활용 안정화)
                # print("[서버패치] Chrome 프로세스 종료 중...")
                # os.system('taskkill /F /IM chrome.exe /T 2>nul')
                # os.system('taskkill /F /IM chromedriver.exe /T 2>nul')
                # time.sleep(3)
                
                print("[서버패치] AWS Manager 실행 중...")
                AWSManager.update_server_container(
                    driver=None,
                    revision=revision,
                    aws_link=awsurl,
                    branch=branch,
                    build_type=buildType,
                    is_debug=False,
                    full_build_name=full_buildname
                )
                print("[서버패치] AWS Manager 완료")
                return f"서버패치 완료: {awsurl} ({full_buildname})"
            
            elif option == "서버삭제":
                # AWS 서버 컨테이너 삭제
                if not awsurl:
                    raise Exception("AWS URL이 설정되지 않았습니다.")
                
                print(f"[서버삭제] AWS URL: {awsurl}")
                
                print("[서버삭제] AWS Manager 실행 중...")
                AWSManager.delete_server_container(
                    driver=None,
                    aws_link=awsurl
                )
                print("[서버삭제] AWS Manager 완료")
                return f"서버삭제 완료: {awsurl}"
            
            elif option == "서버업로드":
                # if not awsurl:
                #     raise Exception("AWS URL이 설정되지 않았습니다.")
                
                # Chrome 프로세스 종료 후 재시작 (디버깅 포트 재활용 안정화)
                # print("[서버패치] Chrome 프로세스 종료 중...")
                # os.system('taskkill /F /IM chrome.exe /T 2>nul')
                # os.system('taskkill /F /IM chromedriver.exe /T 2>nul')
                # time.sleep(3)
                
                
                full_buildname = get_full_buildname(buildname)
                
                # 빌드 경로 확인 (NAS 경로)
                build_path = os.path.join(src_folder, full_buildname)
                if not os.path.isdir(build_path):
                    raise Exception(f"빌드 폴더가 없습니다: {build_path}")
                
                # 리비전/타입 추출
                revision = self.build_ops.extract_revision_number(full_buildname)
                buildType = full_buildname.split('_')[1] if '_' in full_buildname else 'DEV'
                
                # Teamcity 로그인 정보 가져오기
                teamcity_id, teamcity_pw = self.config_mgr.get_teamcity_credentials()
                
                # TeamCity를 통한 서버 배포 실행
                AWSManager.upload_server_build(
                    driver=None,
                    revision=revision,
                    zip_path="",  # TeamCity 방식에서는 사용하지 않음
                    aws_link=awsurl,
                    branch=branch,
                    build_type=buildType,
                    full_build_name=full_buildname,
                    teamcity_id=teamcity_id,
                    teamcity_pw=teamcity_pw
                )
                return f"서버업로드 완료: {full_buildname}"
            
            elif option == "서버업로드및패치":
                if not awsurl:
                    raise Exception("AWS URL이 설정되지 않았습니다.")
                
                full_buildname = get_full_buildname(buildname)
                
                # 빌드 경로 확인 (NAS 경로)
                build_path = os.path.join(src_folder, full_buildname)
                if not os.path.isdir(build_path):
                    raise Exception(f"빌드 폴더가 없습니다: {build_path}")
                
                # 리비전/타입 추출
                revision = self.build_ops.extract_revision_number(full_buildname)
                buildType = full_buildname.split('_')[1] if '_' in full_buildname else 'DEV'
                
                # Chrome 프로세스 초기화
                os.system('taskkill /F /IM chrome.exe /T 2>nul')
                os.system('taskkill /F /IM chromedriver.exe /T 2>nul')
                time.sleep(2)
                
                # Teamcity 로그인 정보 가져오기
                teamcity_id, teamcity_pw = self.config_mgr.get_teamcity_credentials()
                
                # TeamCity를 통한 서버 배포 실행
                AWSManager.upload_server_build(
                    driver=None,
                    revision=revision,
                    zip_path="",  # TeamCity 방식에서는 사용하지 않음
                    aws_link=awsurl,
                    branch=branch,
                    build_type=buildType,
                    full_build_name=full_buildname,
                    teamcity_id=teamcity_id,
                    teamcity_pw=teamcity_pw
                )
                
                # 패치
                AWSManager.update_server_container(
                    driver=None,
                    revision=revision,
                    aws_link=awsurl,
                    branch=branch,
                    build_type=buildType,
                    is_debug=False,
                    full_build_name=full_buildname
                )
                return f"서버업로드및패치 완료: {awsurl} ({full_buildname})"
            
            elif option == "빌드굽기":
                # Teamcity 로그인 정보 가져오기
                teamcity_id, teamcity_pw = self.config_mgr.get_teamcity_credentials()
                
                # TeamCity 빌드 실행
                AWSManager.run_teamcity_build(
                    driver=None, 
                    branch=branch or buildname,
                    teamcity_id=teamcity_id,
                    teamcity_pw=teamcity_pw
                )
                return f"빌드굽기 완료: {branch or buildname}"
            
            elif option == "Chrome프로세스정리":
                # Chrome 및 ChromeDriver 프로세스 정리
                print("[Chrome프로세스정리] 시작")
                
                # ChromeDriver 프로세스 종료
                chromedriver_killed = AWSManager.kill_all_chromedrivers()
                print(f"[Chrome프로세스정리] ChromeDriver 프로세스 {chromedriver_killed}개 종료")
                
                # Chrome 프로세스 종료
                chrome_result = os.system('taskkill /F /IM chrome.exe /T 2>nul')
                chrome_killed = "성공" if chrome_result == 0 else "없음"
                print(f"[Chrome프로세스정리] Chrome 프로세스 종료: {chrome_killed}")
                
                # ChromeTEMP 캐시 정리 (선택적)
                try:
                    cache_dir = AWSManager.CHROME_USER_DATA_DIR
                    if os.path.exists(cache_dir):
                        import shutil
                        shutil.rmtree(cache_dir)
                        print(f"[Chrome프로세스정리] 캐시 디렉터리 삭제: {cache_dir}")
                        cache_cleaned = "✅ 캐시 정리 완료"
                    else:
                        cache_cleaned = "캐시 없음"
                except Exception as e:
                    cache_cleaned = f"⚠️ 캐시 정리 실패: {e}"
                    print(f"[Chrome프로세스정리] {cache_cleaned}")
                
                # 결과 요약
                summary = f"ChromeDriver: {chromedriver_killed}개 종료, Chrome: {chrome_killed}, {cache_cleaned}"
                print(f"[Chrome프로세스정리] 완료 - {summary}")
                return f"Chrome프로세스정리 완료 - {summary}"
            
            else:
                return f"{option} 실행 완료 (미구현)"
        
        except Exception as e:
            # 에러 메시지를 간결하게 만들어서 재발생
            simplified_msg = simplify_error_message(str(e))
            raise Exception(f"{option} 실행 오류: {simplified_msg}")
    
    def on_schedule_finished(self, schedule: dict, success: bool, message: str):
        """스케줄 실행 완료"""
        schedule_id = schedule.get('id', '')
        schedule_name = schedule.get('name', 'Unknown')
        
        # 워커 제거 (스레드가 완전히 종료된 후 안전하게 삭제)
        if schedule_id in self.running_workers:
            worker = self.running_workers.pop(schedule_id)
            worker.finished.connect(worker.deleteLater)  # 스레드 종료 후 삭제
        
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
        
        # 슬랙 알림 전송 (완료/실패)
        status = '완료' if success else '실패'
        self.send_slack_notification_if_enabled(schedule, status, message)
    
    def hide_status_message(self, schedule_id: str):
        """상태 메시지 숨기기"""
        if schedule_id in self.schedule_widgets:
            widget = self.schedule_widgets[schedule_id]
            if not widget.is_running:  # 실행 중이 아닐 때만 숨김
                widget.status_label.setVisible(False)
    
    def send_slack_notification_if_enabled(self, schedule: dict, status: str, details: str = None):
        """
        스케줄에 슬랙 알림이 활성화되어 있으면 알림 전송
        
        Args:
            schedule: 스케줄 정보
            status: 상태 (시작, 완료, 실패)
            details: 추가 상세 정보
        """
        try:
            # 슬랙 알림이 활성화되어 있는지 확인
            slack_enabled = schedule.get('slack_enabled', False)
            bot_token = schedule.get('bot_token', '').strip()
            channel_id = schedule.get('channel_id', '').strip()
            
            if not slack_enabled or not bot_token or not channel_id:
                return
            
            # 스케줄 이름
            schedule_name = schedule.get('name', 'Unknown')
            
            # 알림 타입 및 추가 정보
            notification_type = schedule.get('notification_type', 'standalone')
            thread_keyword = schedule.get('thread_keyword', '').strip()
            first_message = schedule.get('first_message', '').strip()
            
            # 테스트(로그) 옵션 처리
            option = schedule.get('option', '')
            if option == '테스트(로그)':
                # first_message가 있으면 그것만 전송, 없으면 알림 안 보냄
                if first_message:
                    details = None  # 상태값(완료/실패) 제거
                else:
                    return  # 알림 전송 안 함
            
            # 알림 전송
            if notification_type == 'thread' and thread_keyword:
                self.log(f"[슬랙 알림] 스레드 댓글 모드: '{thread_keyword}' 검색 중...")
            
            send_schedule_notification(
                webhook_url='',  # 더 이상 사용 안 함 (호환성용)
                schedule_name=schedule_name,
                status=status,
                details=details,
                notification_type=notification_type,
                bot_token=bot_token,
                channel_id=channel_id,
                thread_keyword=thread_keyword if notification_type == 'thread' else None,
                first_message=first_message if first_message else None
            )
            
        except Exception as e:
            # 슬랙 알림 실패는 로그만 남기고 계속 진행
            self.log(f"[슬랙 알림 오류] {e}")
    
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
        # print는 제거: UI에 이미 출력되고, Debug 모드에서 무한 재귀 발생
        
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
        버전 읽기 (version.json에서)
        형식: 3.0-YY.MM.DD.HHMM
        """
        try:
            # version.json 읽기
            import json
            with open("version.json", "r", encoding="utf-8") as f:
                version_data = json.load(f)
            return version_data.get('version', '3.0.0')
        except FileNotFoundError:
            # version.json이 없으면 version.txt 시도 (하위 호환성)
            try:
                with open("version.txt", "r", encoding="utf-8") as f:
                    return f.read().strip()
            except:
                return "3.0.0"
        except:
            return "3.0.0"
    
    def is_running_from_python(self) -> bool:
        """Python 스크립트로 실행 중인지 확인 (개발 모드)"""
        import sys
        # sys.frozen이 없거나 False면 Python 스크립트로 실행 중
        return not getattr(sys, 'frozen', False)
    
    def show_about(self):
        """About 다이얼로그"""
        if AboutDialog:
            dialog = AboutDialog(self)
            dialog.exec_()
        else:
            QMessageBox.information(
                self,
                "About QuickBuild",
                f"QuickBuild v2\nVersion: {self.read_version()}\n\n스케줄 기반 빌드 관리 도구"
            )
    
    def check_update(self):
        """업데이트 확인 (메뉴에서 수동 실행) - check_for_updates로 리다이렉트"""
        self.check_for_updates()
    
    def check_for_updates(self):
        """업데이트 확인 (메뉴 또는 About에서 호출)"""
        if not self.auto_updater:
            QMessageBox.warning(self, "업데이트 오류", "업데이트 모듈을 불러올 수 없습니다.")
            return
        
        self.log("🔍 서버에서 업데이트 확인 중...")
        
        # 동기적으로 업데이트 확인
        has_update, info, error_msg = self.auto_updater.check_updates_sync()
        
        if error_msg:
            QMessageBox.warning(self, "업데이트 확인 실패", f"오류: {error_msg}")
            return
        
        if not has_update:
            QMessageBox.information(self, "최신 버전", "현재 최신 버전을 사용 중입니다.")
            return
        
        # 새로운 업데이트 알림 다이얼로그 표시
        self._show_update_notification(info)
    
    def check_for_updates_on_startup(self):
        """앱 시작 시 백그라운드에서 업데이트 확인"""
        def callback(has_update, info, error_msg):
            # 메인 스레드로 결과 전달
            self.update_check_result.emit(has_update, info, error_msg or "")
        
        # 동기 방식으로 체크
        has_update, info, error_msg = self.auto_updater.check_updates_sync()
        callback(has_update, info, error_msg)
    
    def on_update_check_result(self, has_update, info, error_msg):
        """업데이트 체크 결과 처리 (메인 스레드)"""
        if error_msg:
            self.log(f"⚠️ 업데이트 확인 실패: {error_msg}")
            return
        
        if has_update:
            self.log(f"🎉 새 버전 발견: {info['version']}")
            # 업데이트 알림 다이얼로그 표시
            self._show_update_notification(info)
        else:
            self.log("✅ 현재 최신 버전을 사용 중입니다")
    
    def _show_update_notification(self, info):
        """업데이트 알림 다이얼로그 표시"""
        if not UpdateNotificationDialog:
            # 다이얼로그 모듈이 없으면 기본 메시지박스 사용
            version = info['version']
            release_notes = info.get('release_notes', '변경 사항 없음')
            
            msg = f"새로운 버전이 있습니다!\n\n"
            msg += f"현재 버전: {self.read_version()}\n"
            msg += f"최신 버전: {version}\n\n"
            msg += f"변경 사항:\n{release_notes[:300]}\n\n"
            msg += "지금 업데이트 하시겠습니까?"
            
            reply = QMessageBox.question(
                self,
                "업데이트 가능",
                msg,
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.start_update_download(info)
            return
        
        # 새로운 업데이트 알림 다이얼로그 사용
        dialog = UpdateNotificationDialog(info, self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:  # 지금 업데이트
            self.log(f"업데이트 시작: {info['version']}")
            self.start_update_download(info)
        elif result == 2:  # 건너뛰기
            self.log(f"버전 {info['version']} 건너뛰기")
            # TODO: 건너뛴 버전 설정 파일에 저장
        else:  # 나중에
            self.log("업데이트 나중에 하기")
    
    def start_update_download(self, info):
        """업데이트 다운로드 시작"""
        if not self.auto_updater:
            return
        
        # 새로운 진행률 다이얼로그 사용
        if DownloadProgressDialog:
            self.download_dialog = DownloadProgressDialog(self)
            
            def progress_callback(received, total):
                """다운로드 진행률 업데이트"""
                self.download_dialog.update_progress(received, total)
            
            def completion_callback(success):
                """다운로드/설치 완료 콜백"""
                if success:
                    self.log("✅ 업데이트 설치 완료")
                    # 배치 스크립트가 재시작 처리 (여기까지 오지 않음)
                else:
                    self.log("❌ 업데이트 실패")
                    self.download_dialog.reject()
                    QMessageBox.critical(
                        self,
                        "업데이트 실패",
                        "업데이트 설치 중 오류가 발생했습니다."
                    )
            
            # 다운로드 시작 (비동기)
            self.auto_updater.download_and_install(progress_callback, completion_callback)
            
            # 진행률 다이얼로그 표시 (모달)
            result = self.download_dialog.exec_()
            
            if result == QDialog.Rejected and self.download_dialog.cancelled:
                # 사용자가 취소
                self.auto_updater.downloader.cancel()
                self.log("업데이트 취소됨")
        else:
            # 기본 프로그레스 다이얼로그 사용
            progress_dialog = QProgressDialog("업데이트 다운로드 중...", "취소", 0, 100, self)
            progress_dialog.setWindowTitle("업데이트")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)
            
            def progress_callback(received, total):
                if total > 0:
                    percent = int((received / total) * 100)
                    progress_dialog.setValue(percent)
                    progress_dialog.setLabelText(
                        f"업데이트 다운로드 중...\n{received / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB"
                    )
            
            def completion_callback(success):
                progress_dialog.close()
                if not success:
                    QMessageBox.critical(self, "업데이트 실패", "업데이트 다운로드 또는 설치에 실패했습니다.")
            
            # 취소 버튼 연결
            progress_dialog.canceled.connect(self.auto_updater.downloader.cancel)
            
            # 다운로드 및 설치 시작 (비동기)
            self.auto_updater.download_and_install(progress_callback, completion_callback)
            
            progress_dialog.exec_()
    
    def show_settings(self):
        """설정 다이얼로그 표시"""
        dialog = SettingsDialog(self, self.settings_file)
        if dialog.exec_():
            # 설정 저장됨
            self.debug_mode = dialog.get_debug_mode()
            self.log("설정이 저장되었습니다")
    
    def show_feedback_dialog(self):
        """버그 및 피드백 다이얼로그 표시"""
        # 앱 버전 전달
        app_version = self.read_version()
        dialog = FeedbackDialog(self, app_version)
        dialog.exec_()
    
    def show_deploy_dialog(self):
        """배포 다이얼로그 표시 (Dev 모드 전용)"""
        try:
            from ui.deploy_dialog import DeployDialog
            current_version = self.read_version()
            dialog = DeployDialog(self, current_version)
            dialog.exec_()
        except ImportError as e:
            QMessageBox.warning(self, "오류", f"배포 다이얼로그를 불러올 수 없습니다:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"배포 다이얼로그 실행 중 오류:\n{e}")
    
    def load_debug_mode(self):
        """settings.json에서 debug_mode 로드"""
        try:
            import json
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get('debug_mode', False)
        except Exception as e:
            print(f"Debug 모드 로드 오류: {e}")
        return False
    
    def check_chromedriver_on_startup(self):
        """앱 시작 시 ChromeDriver 존재 여부 확인 및 자동 설치"""
        try:
            self.log("=== ChromeDriver 확인 중 ===")
            
            # ChromeDriver 경로 확인 시도
            try:
                chromedriver_path = AWSManager.get_chromedriver_path()
                self.log(f"✅ ChromeDriver 발견: {chromedriver_path}")
                return
            except FileNotFoundError as e:
                # ChromeDriver가 없음
                self.log("⚠️ ChromeDriver가 설치되어 있지 않습니다.")
                self.log(str(e))
                
                # 사용자에게 자동 설치 여부 확인
                reply = QMessageBox.question(
                    self,
                    "ChromeDriver 설치 필요",
                    "ChromeDriver가 설치되어 있지 않습니다.\n\n"
                    "서버 업로드/패치 기능을 사용하려면 ChromeDriver가 필요합니다.\n"
                    "지금 자동으로 설치하시겠습니까?\n\n"
                    "• chromedriver_autoinstaller 사용\n"
                    "• 시스템 Chrome 버전과 호환되는 버전 자동 선택\n"
                    "• 소요 시간: 약 30초~1분",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.No:
                    self.log("ChromeDriver 설치를 건너뛰었습니다.")
                    self.log("나중에 Settings 메뉴에서 설치할 수 있습니다.")
                    return
                
                # 자동 설치 시작
                self.log("=== ChromeDriver 자동 설치 시작 ===")
                self.install_chromedriver_on_startup()
                
        except Exception as e:
            self.log(f"ChromeDriver 확인 중 오류: {e}")
    
    def install_chromedriver_on_startup(self):
        """앱 시작 시 ChromeDriver 자동 설치"""
        from PyQt5.QtCore import QThread, pyqtSignal
        
        class ChromeDriverInstallThread(QThread):
            """ChromeDriver 설치 스레드"""
            progress = pyqtSignal(str)
            finished = pyqtSignal(bool, str)
            
            def run(self):
                try:
                    def progress_callback(msg):
                        self.progress.emit(msg)
                    
                    driver_path = AWSManager.download_latest_chromedriver(progress_callback)
                    self.finished.emit(True, driver_path)
                except Exception as e:
                    self.finished.emit(False, str(e))
        
        # 진행 다이얼로그
        progress_dialog = QProgressDialog("ChromeDriver 설치 준비 중...", None, 0, 0, self)
        progress_dialog.setWindowTitle("ChromeDriver 설치")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.show()
        
        # 설치 스레드 시작
        install_thread = ChromeDriverInstallThread()
        
        def on_progress(msg):
            progress_dialog.setLabelText(msg)
            self.log(msg)
        
        def on_finished(success, message):
            progress_dialog.close()
            
            if success:
                self.log(f"✅ ChromeDriver 설치 완료: {message}")
                QMessageBox.information(
                    self,
                    "설치 완료",
                    f"ChromeDriver가 성공적으로 설치되었습니다!\n\n경로: {message}"
                )
            else:
                self.log(f"❌ ChromeDriver 설치 실패: {message}")
                QMessageBox.critical(
                    self,
                    "설치 실패",
                    f"ChromeDriver 설치에 실패했습니다.\n\n{message}\n\n"
                    "Settings 메뉴에서 다시 시도하거나 수동으로 설치해주세요."
                )
        
        install_thread.progress.connect(on_progress)
        install_thread.finished.connect(on_finished)
        install_thread.start()
        
        # 스레드 참조 유지
        self.chromedriver_install_thread = install_thread


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = QuickBuildApp()
    main_window.show()
    
    # 앱 시작 시 자동 업데이트 확인은 __init__에서 QTimer로 처리됨
    
    sys.exit(app.exec_())

