"""
배포 다이얼로그 - Dev 모드에서 빠른 빌드 및 배포
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QTextEdit, QGroupBox,
                             QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import os
import sys


class DeployWorkerThread(QThread):
    """배포 작업 스레드"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, str)  # (진행률, 상태 메시지)
    finished_signal = pyqtSignal(bool, str)  # (성공 여부, 메시지)
    heartbeat_signal = pyqtSignal(str)  # 하트비트 (프로세스 살아있음 확인)
    
    def __init__(self, version_type, changelog_message, skip_github, force_rebuild):
        super().__init__()
        self.version_type = version_type
        self.changelog_message = changelog_message
        self.skip_github = skip_github
        self.force_rebuild = force_rebuild
        self.cancelled = False
    
    def run(self):
        """배포 작업 실행"""
        try:
            import subprocess
            import json
            
            # 1단계: 빌드 (build.py)
            self.log_signal.emit("=" * 60)
            self.log_signal.emit("1단계: 빌드 시작 (build.py)")
            self.log_signal.emit("=" * 60)
            self.progress_signal.emit(10, "빌드 준비 중...")
            
            if self.cancelled:
                return
            
            # 환경변수 설정 (버전 업데이트 건너뛰기)
            env = os.environ.copy()
            env['SKIP_VERSION_UPDATE'] = '0'  # 버전 업데이트 수행
            env['PYTHONUNBUFFERED'] = '1'  # Python 출력 버퍼링 비활성화
            
            # build.py 실행 (비대화형 모드)
            # 버전 타입과 changelog를 환경변수로 전달
            env['BUILD_VERSION_TYPE'] = self.version_type
            env['BUILD_CHANGELOG'] = self.changelog_message
            env['BUILD_FORCE_REBUILD'] = '1' if self.force_rebuild else '0'
            
            build_process = subprocess.Popen(
                [sys.executable, '-u', 'scripts/build.py'],  # -u: unbuffered 모드
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,  # 버퍼링 완전 비활성화
                env=env,
                cwd=os.getcwd(),
                encoding='utf-8',
                errors='replace'  # 디코딩 에러 시 대체 문자 사용
            )
            
            # 빌드 로그 실시간 출력 (논블로킹 방식)
            import time
            import select
            
            last_output_time = time.time()
            building_exe = False
            no_output_count = 0
            
            while True:
                # 프로세스 종료 확인
                if build_process.poll() is not None:
                    # 남은 출력 읽기
                    remaining = build_process.stdout.read()
                    if remaining:
                        for line in remaining.splitlines():
                            if line.strip():
                                self.log_signal.emit(line.rstrip())
                    break
                
                # 취소 확인
                if self.cancelled:
                    build_process.terminate()
                    return
                
                # 출력 읽기 (타임아웃 1초)
                line = build_process.stdout.readline()
                
                if line:
                    line = line.rstrip()
                    if line:
                        self.log_signal.emit(line)
                        last_output_time = time.time()
                        no_output_count = 0
                        
                        # 진행률 추정
                        if "Creating version file" in line:
                            self.progress_signal.emit(20, "버전 파일 생성 중...")
                        elif "Creating spec file" in line:
                            self.progress_signal.emit(30, "Spec 파일 생성 중...")
                        elif "Building EXE" in line:
                            self.progress_signal.emit(40, "EXE 빌드 중... (수 분 소요)")
                            building_exe = True
                        elif "Cleaning up" in line:
                            self.progress_signal.emit(80, "정리 중...")
                            building_exe = False
                        
                        # PyInstaller 진행 상황 로그
                        if building_exe:
                            if "INFO: PyInstaller" in line or "INFO: Building" in line:
                                self.progress_signal.emit(50, "PyInstaller 실행 중...")
                            elif "INFO: Analyzing" in line:
                                self.progress_signal.emit(55, "의존성 분석 중...")
                            elif "INFO: Processing" in line:
                                self.progress_signal.emit(60, "파일 처리 중...")
                            elif "INFO: Building EXE" in line or "Building EXE from" in line:
                                self.progress_signal.emit(70, "EXE 생성 중...")
                else:
                    # 출력이 없을 때 하트비트
                    time.sleep(0.5)
                    no_output_count += 1
                    
                    # 30초마다 하트비트 메시지
                    if building_exe and no_output_count >= 60:  # 0.5초 * 60 = 30초
                        elapsed = int(time.time() - last_output_time)
                        self.heartbeat_signal.emit(f"⏳ 빌드 진행 중... (마지막 출력: {elapsed}초 전)")
                        no_output_count = 0
            
            build_process.wait()
            
            if build_process.returncode != 0:
                self.finished_signal.emit(False, f"빌드 실패 (exit code: {build_process.returncode})")
                return
            
            self.log_signal.emit("✅ 빌드 완료!")
            self.progress_signal.emit(85, "빌드 완료")
            
            if self.cancelled or self.skip_github:
                if self.skip_github:
                    self.log_signal.emit("\n로컬 빌드만 완료 (GitHub 배포 건너뛰기)")
                    self.finished_signal.emit(True, "로컬 빌드 완료")
                return
            
            # 2단계: GitHub 배포 (deploy_local.py)
            self.log_signal.emit("\n" + "=" * 60)
            self.log_signal.emit("2단계: GitHub 배포 시작 (deploy_local.py)")
            self.log_signal.emit("=" * 60)
            self.progress_signal.emit(90, "GitHub 배포 중...")
            
            if self.cancelled:
                return
            
            # deploy_local.py 실행 (비대화형 모드)
            deploy_env = os.environ.copy()
            deploy_env['DEPLOY_AUTO_MODE'] = '1'  # 자동 모드 플래그
            deploy_env['PYTHONUNBUFFERED'] = '1'  # Python 출력 버퍼링 비활성화
            
            deploy_process = subprocess.Popen(
                [sys.executable, '-u', 'scripts/deploy_local.py'],  # -u: unbuffered 모드
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,  # 버퍼링 완전 비활성화
                env=deploy_env,
                cwd=os.getcwd(),
                encoding='utf-8',
                errors='replace'  # 디코딩 에러 시 대체 문자 사용
            )
            
            # 배포 로그 실시간 출력
            for line in iter(deploy_process.stdout.readline, ''):
                if self.cancelled:
                    deploy_process.terminate()
                    return
                
                line = line.rstrip()
                if line:
                    self.log_signal.emit(line)
                    
                    # 진행률 추정
                    if "ZIP 패키지 생성" in line:
                        self.progress_signal.emit(92, "ZIP 패키지 생성 중...")
                    elif "GitHub 릴리즈 생성" in line:
                        self.progress_signal.emit(95, "GitHub 릴리즈 생성 중...")
                    elif "ZIP 파일 업로드" in line:
                        self.progress_signal.emit(97, "파일 업로드 중...")
            
            deploy_process.wait()
            
            if deploy_process.returncode != 0:
                self.finished_signal.emit(False, f"배포 실패 (exit code: {deploy_process.returncode})")
                return
            
            self.log_signal.emit("✅ 배포 완료!")
            self.progress_signal.emit(100, "완료")
            self.finished_signal.emit(True, "빌드 및 배포 완료!")
            
        except Exception as e:
            self.log_signal.emit(f"\n❌ 오류 발생: {e}")
            import traceback
            self.log_signal.emit(traceback.format_exc())
            self.finished_signal.emit(False, str(e))
    
    def cancel(self):
        """작업 취소"""
        self.cancelled = True


class DeployDialog(QDialog):
    """배포 다이얼로그"""
    
    def __init__(self, parent=None, current_version=None):
        super().__init__(parent)
        self.worker = None
        self.current_version = current_version or "3.0.0"
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("빠른 빌드 및 배포")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # 제목
        title_label = QLabel("🚀 빠른 빌드 및 배포")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title_label)
        
        # 현재 버전 표시
        version_info_label = QLabel(f"현재 버전: {self.current_version}")
        version_info_label.setStyleSheet("""
            background-color: #E3F2FD;
            color: #1976D2;
            padding: 8px 15px;
            border-radius: 5px;
            font-size: 11pt;
            font-weight: bold;
            margin: 5px 0px;
        """)
        layout.addWidget(version_info_label)
        
        # 설정 그룹
        settings_group = QGroupBox("배포 설정")
        settings_layout = QVBoxLayout()
        
        # 버전 타입 선택
        version_layout = QHBoxLayout()
        version_label = QLabel("버전 타입:")
        version_label.setFixedWidth(100)
        self.version_combo = QComboBox()
        
        # 현재 버전 파싱
        try:
            parts = self.current_version.split('.')
            major = int(parts[0]) if len(parts) > 0 else 3
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
        except:
            major, minor, patch = 3, 0, 0
        
        # 각 버전 타입별 예상 버전 표시
        self.version_combo.addItem(f"PATCH (버그 수정) → {major}.{minor}.{patch + 1}", "patch")
        self.version_combo.addItem(f"MINOR (새 기능) → {major}.{minor + 1}.0", "minor")
        self.version_combo.addItem(f"MAJOR (Breaking changes) → {major + 1}.0.0", "major")
        self.version_combo.addItem(f"테스트 빌드 (버전 변경 없음) → {self.current_version}", "test")
        self.version_combo.setCurrentIndex(0)
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_combo)
        settings_layout.addLayout(version_layout)
        
        # 버전 타입 설명
        version_desc_label = QLabel(
            "• PATCH: 세 번째 숫자 증가 (버그 수정, 작은 개선)\n"
            "• MINOR: 두 번째 숫자 증가 (새 기능 추가, 하위 호환)\n"
            "• MAJOR: 첫 번째 숫자 증가 (Breaking changes, 호환성 깨짐)"
        )
        version_desc_label.setStyleSheet("""
            color: #757575;
            font-size: 9pt;
            padding: 5px 10px;
            background-color: #F5F5F5;
            border-radius: 3px;
            margin: 5px 0px;
        """)
        settings_layout.addWidget(version_desc_label)
        
        # 변경사항 입력
        changelog_label = QLabel("변경사항:")
        self.changelog_input = QTextEdit()
        self.changelog_input.setPlaceholderText("변경사항을 입력하세요 (비워두면 '버그 수정 및 성능 개선' 사용)")
        self.changelog_input.setMaximumHeight(80)
        settings_layout.addWidget(changelog_label)
        settings_layout.addWidget(self.changelog_input)
        
        # 빌드 옵션
        build_options_layout = QHBoxLayout()
        
        # 기존 EXE 덮어쓰기 옵션
        self.force_rebuild_btn = QPushButton("기존 EXE 덮어쓰기")
        self.force_rebuild_btn.setCheckable(True)
        self.force_rebuild_btn.setChecked(True)  # 기본값: 덮어쓰기
        self.force_rebuild_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:checked {
                background-color: #1976D2;
            }
        """)
        self.force_rebuild_btn.setToolTip("체크: dist/QuickBuild.exe가 있어도 다시 빌드\n체크 해제: 기존 EXE가 있으면 재사용")
        build_options_layout.addWidget(self.force_rebuild_btn)
        
        # GitHub 배포 건너뛰기 옵션
        self.skip_github_btn = QPushButton("로컬 빌드만 (GitHub 배포 건너뛰기)")
        self.skip_github_btn.setCheckable(True)
        self.skip_github_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:checked {
                background-color: #FF9800;
            }
        """)
        build_options_layout.addWidget(self.skip_github_btn)
        build_options_layout.addStretch()
        settings_layout.addLayout(build_options_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 진행 상태 그룹
        progress_group = QGroupBox("진행 상황")
        progress_layout = QVBoxLayout()
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        # 상태 라벨
        self.status_label = QLabel("대기 중...")
        self.status_label.setStyleSheet("color: #757575; padding: 5px;")
        progress_layout.addWidget(self.status_label)
        
        # 로그 출력
        log_label = QLabel("실행 로그:")
        progress_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #3C3C3C;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.log_text)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.start_btn = QPushButton("시작")
        self.start_btn.setFixedSize(100, 35)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.start_btn.clicked.connect(self.start_deploy)
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setFixedSize(100, 35)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_deploy)
        button_layout.addWidget(self.cancel_btn)
        
        self.close_btn = QPushButton("닫기")
        self.close_btn.setFixedSize(100, 35)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def start_deploy(self):
        """배포 시작"""
        # 입력값 가져오기
        version_type = self.version_combo.currentData()
        changelog_message = self.changelog_input.toPlainText().strip() or "버그 수정 및 성능 개선"
        skip_github = self.skip_github_btn.isChecked()
        force_rebuild = self.force_rebuild_btn.isChecked()
        
        # 확인 메시지
        rebuild_msg = "기존 EXE 덮어쓰기" if force_rebuild else "기존 EXE 재사용"
        
        if version_type == "test":
            confirm_msg = f"테스트 빌드를 시작하시겠습니까?\n\n버전 변경 없이 빌드만 수행됩니다.\n빌드 옵션: {rebuild_msg}"
        elif skip_github:
            confirm_msg = f"로컬 빌드를 시작하시겠습니까?\n\n버전 타입: {self.version_combo.currentText()}\n변경사항: {changelog_message}\n빌드 옵션: {rebuild_msg}\n\n※ GitHub 배포는 건너뜁니다."
        else:
            confirm_msg = f"빌드 및 배포를 시작하시겠습니까?\n\n버전 타입: {self.version_combo.currentText()}\n변경사항: {changelog_message}\n빌드 옵션: {rebuild_msg}\n\n※ GitHub에 자동으로 배포됩니다."
        
        reply = QMessageBox.question(
            self,
            "배포 확인",
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # UI 상태 변경
        self.start_btn.setEnabled(False)
        self.version_combo.setEnabled(False)
        self.changelog_input.setEnabled(False)
        self.force_rebuild_btn.setEnabled(False)
        self.skip_github_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("시작 중...")
        
        # 워커 스레드 생성 및 시작
        self.worker = DeployWorkerThread(version_type, changelog_message, skip_github, force_rebuild)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.heartbeat_signal.connect(self.on_heartbeat)
        self.worker.start()
    
    def cancel_deploy(self):
        """배포 취소"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "취소 확인",
                "배포를 취소하시겠습니까?\n\n진행 중인 작업이 중단됩니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.append_log("\n❌ 사용자가 취소했습니다...")
                self.worker.cancel()
                self.worker.wait(2000)
                
                # UI 상태 복원
                self.start_btn.setEnabled(True)
                self.version_combo.setEnabled(True)
                self.changelog_input.setEnabled(True)
                self.force_rebuild_btn.setEnabled(True)
                self.skip_github_btn.setEnabled(True)
                self.close_btn.setEnabled(True)
                self.cancel_btn.setEnabled(False)
                self.status_label.setText("취소됨")
    
    def append_log(self, message):
        """로그 추가"""
        self.log_text.append(message)
        # 자동 스크롤
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_progress(self, value, status):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
    
    def on_heartbeat(self, message):
        """하트비트 메시지 (프로세스 살아있음 확인)"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #FF9800; padding: 5px; font-style: italic;")
    
    def on_finished(self, success, message):
        """배포 완료"""
        # UI 상태 복원
        self.start_btn.setEnabled(True)
        self.version_combo.setEnabled(True)
        self.changelog_input.setEnabled(True)
        self.force_rebuild_btn.setEnabled(True)
        self.skip_github_btn.setEnabled(True)
        self.close_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        if success:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
            
            QMessageBox.information(
                self,
                "완료",
                f"{message}\n\n로그를 확인하세요."
            )
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: #F44336; padding: 5px; font-weight: bold;")
            
            QMessageBox.critical(
                self,
                "오류",
                f"배포 중 오류가 발생했습니다:\n\n{message}\n\n로그를 확인하세요."
            )
    
    def closeEvent(self, event):
        """다이얼로그 닫기"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "닫기 확인",
                "배포가 진행 중입니다.\n정말 닫으시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            self.worker.cancel()
            self.worker.wait(2000)
        
        event.accept()

