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
    
    def __init__(self, version_type, changelog_message, skip_github):
        super().__init__()
        self.version_type = version_type
        self.changelog_message = changelog_message
        self.skip_github = skip_github
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
            
            # build.py 실행 (비대화형 모드)
            # 버전 타입과 changelog를 환경변수로 전달
            env['BUILD_VERSION_TYPE'] = self.version_type
            env['BUILD_CHANGELOG'] = self.changelog_message
            
            build_process = subprocess.Popen(
                [sys.executable, 'build.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                cwd=os.getcwd()
            )
            
            # 빌드 로그 실시간 출력
            for line in iter(build_process.stdout.readline, ''):
                if self.cancelled:
                    build_process.terminate()
                    return
                
                line = line.rstrip()
                if line:
                    self.log_signal.emit(line)
                    
                    # 진행률 추정
                    if "Creating version file" in line:
                        self.progress_signal.emit(20, "버전 파일 생성 중...")
                    elif "Creating spec file" in line:
                        self.progress_signal.emit(30, "Spec 파일 생성 중...")
                    elif "Building EXE" in line:
                        self.progress_signal.emit(40, "EXE 빌드 중...")
                    elif "Cleaning up" in line:
                        self.progress_signal.emit(80, "정리 중...")
            
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
            
            deploy_process = subprocess.Popen(
                [sys.executable, 'deploy_local.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=deploy_env,
                cwd=os.getcwd()
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
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
        
        # 설정 그룹
        settings_group = QGroupBox("배포 설정")
        settings_layout = QVBoxLayout()
        
        # 버전 타입 선택
        version_layout = QHBoxLayout()
        version_label = QLabel("버전 타입:")
        version_label.setFixedWidth(100)
        self.version_combo = QComboBox()
        self.version_combo.addItem("PATCH (버그 수정)", "patch")
        self.version_combo.addItem("MINOR (새 기능)", "minor")
        self.version_combo.addItem("MAJOR (Breaking changes)", "major")
        self.version_combo.addItem("테스트 빌드 (버전 변경 없음)", "test")
        self.version_combo.setCurrentIndex(0)
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_combo)
        settings_layout.addLayout(version_layout)
        
        # 변경사항 입력
        changelog_label = QLabel("변경사항:")
        self.changelog_input = QTextEdit()
        self.changelog_input.setPlaceholderText("변경사항을 입력하세요 (비워두면 '버그 수정 및 성능 개선' 사용)")
        self.changelog_input.setMaximumHeight(80)
        settings_layout.addWidget(changelog_label)
        settings_layout.addWidget(self.changelog_input)
        
        # GitHub 배포 건너뛰기 옵션
        skip_layout = QHBoxLayout()
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
        skip_layout.addWidget(self.skip_github_btn)
        skip_layout.addStretch()
        settings_layout.addLayout(skip_layout)
        
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
        
        # 확인 메시지
        if version_type == "test":
            confirm_msg = "테스트 빌드를 시작하시겠습니까?\n\n버전 변경 없이 빌드만 수행됩니다."
        elif skip_github:
            confirm_msg = f"로컬 빌드를 시작하시겠습니까?\n\n버전 타입: {self.version_combo.currentText()}\n변경사항: {changelog_message}\n\n※ GitHub 배포는 건너뜁니다."
        else:
            confirm_msg = f"빌드 및 배포를 시작하시겠습니까?\n\n버전 타입: {self.version_combo.currentText()}\n변경사항: {changelog_message}\n\n※ GitHub에 자동으로 배포됩니다."
        
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
        self.skip_github_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("시작 중...")
        
        # 워커 스레드 생성 및 시작
        self.worker = DeployWorkerThread(version_type, changelog_message, skip_github)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
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
    
    def on_finished(self, success, message):
        """배포 완료"""
        # UI 상태 복원
        self.start_btn.setEnabled(True)
        self.version_combo.setEnabled(True)
        self.changelog_input.setEnabled(True)
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

