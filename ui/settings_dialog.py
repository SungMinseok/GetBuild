"""Settings Dialog - 애플리케이션 설정"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
                             QPushButton, QLabel, QGroupBox, QMessageBox,
                             QProgressDialog, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import json
import os


class ChromeDriverDownloadThread(QThread):
    """ChromeDriver 다운로드 워커 스레드"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # (success, message)
    
    def run(self):
        try:
            from core.aws_manager import AWSManager
            
            def progress_callback(msg):
                self.progress.emit(msg)
            
            driver_path = AWSManager.download_latest_chromedriver(progress_callback)
            self.finished.emit(True, f"설치 완료!\n경로: {driver_path}")
        except Exception as e:
            self.finished.emit(False, str(e))


class SettingsDialog(QDialog):
    """설정 다이얼로그"""
    
    def __init__(self, parent=None, settings_file='settings.json'):
        super().__init__(parent)
        self.settings_file = settings_file
        self.settings = self.load_settings()
        self.download_thread = None
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Debug 모드 그룹
        debug_group = QGroupBox("Debug Options")
        debug_layout = QVBoxLayout()
        
        # Debug 모드 체크박스
        self.debug_checkbox = QCheckBox("Debug Mode (내부 로그 UI에 표시)")
        self.debug_checkbox.setChecked(self.settings.get('debug_mode', False))
        debug_layout.addWidget(self.debug_checkbox)
        
        debug_info = QLabel("활성화 시 [서버업로드], [서버패치] 등의 내부 로그가 실행 로그 영역에 표시됩니다.")
        debug_info.setWordWrap(True)
        debug_info.setStyleSheet("color: #888; font-size: 9pt;")
        debug_layout.addWidget(debug_info)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        # ChromeDriver 관리 그룹
        chrome_group = QGroupBox("ChromeDriver 관리")
        chrome_layout = QVBoxLayout()
        
        # ChromeDriver 자동 다운로드 버튼
        download_layout = QHBoxLayout()
        self.download_driver_btn = QPushButton("ChromeDriver 자동 다운로드")
        self.download_driver_btn.clicked.connect(self.download_chromedriver)
        download_layout.addWidget(self.download_driver_btn)
        download_layout.addStretch()
        chrome_layout.addLayout(download_layout)
        
        download_info = QLabel("시스템 Chrome 버전과 호환되는 ChromeDriver를 자동으로 다운로드합니다. (chromedriver_autoinstaller)")
        download_info.setWordWrap(True)
        download_info.setStyleSheet("color: #888; font-size: 9pt;")
        chrome_layout.addWidget(download_info)
        
        chrome_layout.addSpacing(10)
        
        # ChromeDriver 강제 종료 버튼
        kill_layout = QHBoxLayout()
        self.kill_driver_btn = QPushButton("ChromeDriver 강제 종료")
        self.kill_driver_btn.clicked.connect(self.kill_chromedrivers)
        kill_layout.addWidget(self.kill_driver_btn)
        kill_layout.addStretch()
        chrome_layout.addLayout(kill_layout)
        
        kill_info = QLabel("실행 중인 모든 ChromeDriver 프로세스를 종료합니다.")
        kill_info.setWordWrap(True)
        kill_info.setStyleSheet("color: #888; font-size: 9pt;")
        chrome_layout.addWidget(kill_info)
        
        chrome_layout.addSpacing(10)
        
        # Chrome 캐시 삭제 버튼
        cache_layout = QHBoxLayout()
        self.clear_cache_btn = QPushButton("Chrome 캐시 삭제")
        self.clear_cache_btn.clicked.connect(self.clear_chrome_cache)
        cache_layout.addWidget(self.clear_cache_btn)
        cache_layout.addStretch()
        chrome_layout.addLayout(cache_layout)
        
        cache_info = QLabel("Chrome 로그인 정보 및 캐시를 모두 삭제합니다. (C:\\ChromeTEMP)")
        cache_info.setWordWrap(True)
        cache_info.setStyleSheet("color: #888; font-size: 9pt;")
        chrome_layout.addWidget(cache_info)
        
        chrome_group.setLayout(chrome_layout)
        layout.addWidget(chrome_group)
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """설정 파일 로드"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"설정 파일 로드 오류: {e}")
                return {}
        return {}
    
    def save_and_close(self):
        """설정 저장 및 닫기"""
        self.settings['debug_mode'] = self.debug_checkbox.isChecked()
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            self.accept()
        except Exception as e:
            print(f"설정 저장 오류: {e}")
            self.reject()
    
    def get_debug_mode(self):
        """Debug 모드 상태 반환"""
        return self.debug_checkbox.isChecked()
    
    def download_chromedriver(self):
        """ChromeDriver 자동 다운로드"""
        reply = QMessageBox.question(
            self,
            "ChromeDriver 다운로드",
            "최신 ChromeDriver를 자동으로 다운로드하시겠습니까?\n\n"
            "- chromedriver_autoinstaller 라이브러리 사용\n"
            "- 시스템 Chrome 버전과 호환되는 버전 자동 선택\n"
            "- 다운로드 크기: 약 10MB\n"
            "- 소요 시간: 30초~1분",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # 진행 다이얼로그 생성
        progress_dialog = QProgressDialog("다운로드 준비 중...", "취소", 0, 0, self)
        progress_dialog.setWindowTitle("ChromeDriver 다운로드")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)  # 취소 버튼 비활성화
        progress_dialog.show()
        
        # 로그 텍스트 에디트 추가
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setMinimumHeight(100)
        
        # 다운로드 스레드 시작
        self.download_thread = ChromeDriverDownloadThread()
        
        def on_progress(msg):
            progress_dialog.setLabelText(msg)
            log_text.append(msg)
        
        def on_finished(success, message):
            progress_dialog.close()
            
            if success:
                QMessageBox.information(
                    self,
                    "다운로드 완료",
                    message
                )
            else:
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("다운로드 실패")
                msg_box.setText(message)
                msg_box.setDetailedText(log_text.toPlainText())
                msg_box.exec_()
        
        self.download_thread.progress.connect(on_progress)
        self.download_thread.finished.connect(on_finished)
        self.download_thread.start()
    
    def kill_chromedrivers(self):
        """ChromeDriver 프로세스 강제 종료"""
        reply = QMessageBox.question(
            self,
            "ChromeDriver 종료",
            "실행 중인 모든 ChromeDriver 프로세스를 종료하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        try:
            from core.aws_manager import AWSManager
            killed_count = AWSManager.kill_all_chromedrivers()
            
            if killed_count > 0:
                QMessageBox.information(
                    self,
                    "종료 완료",
                    f"{killed_count}개의 ChromeDriver 프로세스를 종료했습니다."
                )
            else:
                QMessageBox.information(
                    self,
                    "종료 완료",
                    "실행 중인 ChromeDriver 프로세스가 없습니다."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"ChromeDriver 종료 실패:\n{e}"
            )
    
    def clear_chrome_cache(self):
        """Chrome 캐시 삭제"""
        reply = QMessageBox.warning(
            self,
            "캐시 삭제 확인",
            "Chrome 사용자 데이터를 모두 삭제하시겠습니까?\n\n"
            "⚠️ 경고:\n"
            "- 로그인 정보가 모두 삭제됩니다.\n"
            "- 저장된 쿠키, 히스토리가 삭제됩니다.\n"
            "- Chrome이 실행 중이면 실패합니다.\n\n"
            "경로: C:\\ChromeTEMP",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        try:
            from core.aws_manager import AWSManager
            AWSManager.clear_chrome_cache()
            
            QMessageBox.information(
                self,
                "삭제 완료",
                "Chrome 캐시가 성공적으로 삭제되었습니다.\n\n"
                "다음 실행 시 다시 로그인해야 합니다."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"캐시 삭제 실패:\n{e}"
            )




