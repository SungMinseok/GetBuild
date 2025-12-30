"""
QuickBuild 업데이트 다이얼로그 모듈
- UpdateNotificationDialog: 업데이트 알림 다이얼로그
- DownloadProgressDialog: 다운로드 진행률 다이얼로그  
- AboutDialog: About 다이얼로그 (버전 정보 및 업데이트 체크)
"""

import json
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap


class UpdateNotificationDialog(QDialog):
    """업데이트 알림 다이얼로그"""
    
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("업데이트 사용 가능")
        self.resize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 제목
        title_label = QLabel("🎉 새로운 버전이 출시되었습니다!")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 버전 정보
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("새 버전:"))
        version_label = QLabel(self.update_info.get('version', '알 수 없음'))
        version_label.setStyleSheet("color: #0066CC; font-weight: bold;")
        version_layout.addWidget(version_label)
        version_layout.addStretch()
        layout.addLayout(version_layout)
        
        # 발행일
        if 'published_at' in self.update_info:
            date_str = self.update_info['published_at'][:10]  # YYYY-MM-DD
            layout.addWidget(QLabel(f"발행일: {date_str}"))
        
        # 변경사항 (스크롤 가능)
        layout.addWidget(QLabel("\n📝 변경사항:"))
        
        changelog = QTextEdit()
        changelog.setReadOnly(True)
        changelog.setPlainText(self.update_info.get('release_notes', '변경사항이 없습니다.'))
        changelog.setMaximumHeight(200)
        layout.addWidget(changelog)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        self.update_now_btn = QPushButton("지금 업데이트")
        self.update_now_btn.setStyleSheet(
            "QPushButton { background-color: #0066CC; color: white; padding: 8px 16px; }"
        )
        self.update_now_btn.clicked.connect(self.accept)
        
        self.later_btn = QPushButton("나중에")
        self.later_btn.clicked.connect(self.reject)
        
        self.skip_btn = QPushButton("이 버전 건너뛰기")
        self.skip_btn.clicked.connect(self.skip_version)
        
        button_layout.addWidget(self.later_btn)
        button_layout.addWidget(self.skip_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.update_now_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def skip_version(self):
        """이 버전 건너뛰기"""
        self.done(2)  # 2 = Skip (사용자 정의 리턴 코드)


class DownloadProgressDialog(QDialog):
    """다운로드 진행률 다이얼로그 (스레드 안전)"""
    
    # 시그널 정의 (스레드 간 통신용)
    progress_updated = pyqtSignal(int, int)  # received, total
    download_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("업데이트 다운로드 중")
        self.resize(400, 150)
        
        # 모달 설정 및 최상단 표시
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        
        self.init_ui()
        self.cancelled = False
        
        # 시그널 연결 (메인 스레드에서 처리)
        self.progress_updated.connect(self._update_progress_safe)
        self.download_completed.connect(self._download_complete_safe)
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 상태 메시지
        self.status_label = QLabel("업데이트 파일 다운로드 중...")
        layout.addWidget(self.status_label)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 크기 정보
        self.size_label = QLabel("0 MB / 0 MB")
        self.size_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.size_label)
        
        # 취소 버튼
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.cancel_download)
        layout.addWidget(self.cancel_btn)
        
        self.setLayout(layout)
    
    def update_progress(self, received, total):
        """
        진행률 업데이트 (스레드 안전 - 시그널 발생)
        다운로드 스레드에서 호출
        """
        self.progress_updated.emit(received, total)
    
    def _update_progress_safe(self, received, total):
        """
        실제 진행률 업데이트 (메인 스레드에서 실행)
        시그널에 의해 자동 호출됨
        """
        if total > 0:
            percentage = int((received / total) * 100)
            self.progress_bar.setValue(percentage)
            
            received_mb = received / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.size_label.setText(f"{received_mb:.1f} MB / {total_mb:.1f} MB")
    
    def cancel_download(self):
        """다운로드 취소"""
        reply = QMessageBox.question(
            self, 
            "다운로드 취소", 
            "다운로드를 취소하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cancelled = True
            self.reject()
    
    def download_complete(self):
        """다운로드 완료 (스레드 안전 - 시그널 발생)"""
        self.download_completed.emit()
    
    def _download_complete_safe(self):
        """실제 다운로드 완료 처리 (메인 스레드에서 실행)"""
        self.status_label.setText("다운로드 완료! 설치 중...")
        self.progress_bar.setValue(100)
        self.cancel_btn.setEnabled(False)


class AboutDialog(QDialog):
    """About 다이얼로그 - 버전 정보 및 업데이트 체크"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QuickBuild 정보")
        self.resize(450, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 앱 아이콘 및 제목
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        
        # 아이콘 로드 시도
        icon_path = "ico.ico"
        if os.path.exists(icon_path):
            try:
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    icon_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception as e:
                print(f"아이콘 로드 실패: {e}")
        
        title_layout.addWidget(icon_label)
        
        title_label = QLabel("QuickBuild")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 부제목
        subtitle_label = QLabel("PUBG 빌드 자동화 도구")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        layout.addWidget(QLabel(""))  # 공백
        
        # 버전 정보 로드
        version_info = self._load_version_info()
        
        # 현재 버전
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("버전:"))
        version_label = QLabel(version_info.get('version', '알 수 없음'))
        version_label.setStyleSheet("font-weight: bold;")
        version_layout.addWidget(version_label)
        version_layout.addStretch()
        layout.addLayout(version_layout)
        
        # 빌드 날짜
        build_layout = QHBoxLayout()
        build_layout.addWidget(QLabel("빌드 날짜:"))
        build_label = QLabel(version_info.get('build_date', '알 수 없음'))
        build_layout.addWidget(build_label)
        build_layout.addStretch()
        layout.addLayout(build_layout)
        
        layout.addWidget(QLabel(""))  # 공백
        
        # 변경 이력 (스크롤 가능)
        layout.addWidget(QLabel("📝 최근 변경사항:"))
        
        changelog_text = QTextEdit()
        changelog_text.setReadOnly(True)
        changelog_text.setMaximumHeight(150)
        
        # version.json에서 모든 변경사항 표시 (최신순)
        changelog = version_info.get('changelog', [])
        if changelog:
            changelog_texts = []
            for item in sorted(changelog, key=lambda x: x.get('date', ''), reverse=True):
                build_name = item.get('version', 'Unknown')
                changes = item.get('changes', [])
                formatted_changes = "\n".join(f"• {change}" for change in changes)
                changelog_texts.append(f"v{build_name}\n{formatted_changes}")
            changelog_text.setPlainText("\n\n".join(changelog_texts))
        else:
            changelog_text.setPlainText("변경사항이 없습니다.")
        
        layout.addWidget(changelog_text)
        
        layout.addWidget(QLabel(""))  # 공백
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 업데이트 확인 버튼
        update_btn = QPushButton("업데이트 확인")
        update_btn.clicked.connect(self.check_updates)
        button_layout.addWidget(update_btn)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _load_version_info(self):
        """version.json 파일에서 버전 정보 로드"""
        try:
            version_file = "version.json"
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"버전 정보 로드 실패: {e}")
        
        return {
            'version': '알 수 없음',
            'build_date': '알 수 없음',
            'changelog': []
        }
    
    def check_updates(self):
        """업데이트 확인 - 부모 위젯의 메서드 호출"""
        try:
            if self.parent() and hasattr(self.parent(), 'check_for_updates'):
                # About 다이얼로그 닫기
                self.accept()
                
                # 부모에서 업데이트 확인 실행
                self.parent().check_for_updates()
            else:
                QMessageBox.information(
                    self,
                    "업데이트 확인",
                    "업데이트를 확인하려면 메뉴에서 '업데이트 확인'을 선택하세요."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"업데이트 확인 중 오류가 발생했습니다.\n\n{e}"
            )

