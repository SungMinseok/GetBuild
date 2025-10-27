"""스케줄 아이템 위젯"""
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QCheckBox, QFrame, QGridLayout, QProgressBar)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from typing import Dict, Any


class ScheduleItemWidget(QFrame):
    """스케줄 리스트 아이템 위젯"""
    
    # 시그널
    edit_requested = pyqtSignal(str)  # 편집 요청 (schedule_id)
    delete_requested = pyqtSignal(str)  # 삭제 요청 (schedule_id)
    toggle_requested = pyqtSignal(str)  # 활성화 토글 요청 (schedule_id)
    run_requested = pyqtSignal(str)  # 수동 실행 요청 (schedule_id)
    copy_requested = pyqtSignal(str)  # 복사 요청 (schedule_id)
    
    def __init__(self, schedule: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.schedule = schedule
        self.schedule_id = schedule.get('id', '')
        self.is_running = False  # 실행 중 상태
        
        self.init_ui()
        self.update_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setMinimumHeight(100)
        self.setMaximumHeight(130)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 왼쪽: 활성화 체크박스
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(self.schedule.get('enabled', True))
        self.enabled_checkbox.clicked.connect(self.on_toggle_clicked)
        main_layout.addWidget(self.enabled_checkbox)
        
        # 중간: 스케줄 정보
        info_layout = QVBoxLayout()
        
        # 첫 번째 줄: 이름 + 시간
        top_layout = QHBoxLayout()
        
        self.name_label = QLabel()
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.name_label.setFont(font)
        top_layout.addWidget(self.name_label)
        
        top_layout.addStretch()
        
        self.time_label = QLabel()
        time_font = QFont()
        time_font.setPointSize(14)
        time_font.setBold(True)
        self.time_label.setFont(time_font)
        self.time_label.setStyleSheet("color: #2196F3;")
        top_layout.addWidget(self.time_label)
        
        info_layout.addLayout(top_layout)
        
        # 두 번째 줄: 반복 설정 + 빌드명
        middle_layout = QHBoxLayout()
        
        self.repeat_label = QLabel()
        self.repeat_label.setStyleSheet("color: #666;")
        middle_layout.addWidget(self.repeat_label)
        
        middle_layout.addWidget(QLabel("|"))
        
        self.buildname_label = QLabel()
        middle_layout.addWidget(self.buildname_label)
        
        middle_layout.addStretch()
        info_layout.addLayout(middle_layout)
        
        # 세 번째 줄: 옵션 + 브랜치
        bottom_layout = QHBoxLayout()
        
        self.option_label = QLabel()
        self.option_label.setStyleSheet("color: #888; font-size: 9pt;")
        bottom_layout.addWidget(self.option_label)
        
        bottom_layout.addStretch()
        info_layout.addLayout(bottom_layout)
        
        # 네 번째 줄: 진행 상태 (기본적으로 숨김)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 9pt;")
        self.status_label.setVisible(False)
        info_layout.addWidget(self.status_label)
        
        # 진행 바 (선택적으로 사용)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #E0E0E0;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        self.progress_bar.setVisible(False)
        info_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(info_layout, 1)
        
        # 오른쪽: 버튼들
        button_layout = QGridLayout()
        button_layout.setSpacing(3)
        
        self.run_button = QPushButton("▶ 실행")
        self.run_button.setFixedWidth(80)
        self.run_button.setFixedHeight(30)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.run_button.clicked.connect(self.on_run_clicked)
        button_layout.addWidget(self.run_button,0,0)
        
        self.copy_button = QPushButton("📋 복사")
        self.copy_button.setFixedWidth(80)
        self.copy_button.setFixedHeight(30)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        self.copy_button.clicked.connect(self.on_copy_clicked)
        button_layout.addWidget(self.copy_button,0,1)
        
        self.edit_button = QPushButton("✏ 편집")
        self.edit_button.setFixedWidth(80)
        self.edit_button.setFixedHeight(30)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.edit_button.clicked.connect(self.on_edit_clicked)
        button_layout.addWidget(self.edit_button,1,0)
        
        self.delete_button = QPushButton("🗑 삭제")
        self.delete_button.setFixedWidth(80)
        self.delete_button.setFixedHeight(30)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(self.delete_button,1,1)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def update_ui(self):
        """UI 업데이트"""
        # 이름
        name = self.schedule.get('name', 'Unnamed Schedule')
        self.name_label.setText(name)
        
        # 시간
        time = self.schedule.get('time', '00:00')
        self.time_label.setText(time)
        
        # 반복 설정
        repeat_type = self.schedule.get('repeat_type', 'once')
        if repeat_type == 'once':
            repeat_text = '일회성'
        elif repeat_type == 'daily':
            repeat_text = '매일 반복'
        elif repeat_type == 'weekly':
            days = self.schedule.get('repeat_days', [])
            day_names = ['월', '화', '수', '목', '금', '토', '일']
            repeat_text = '매주 ' + ', '.join([day_names[d] for d in days if 0 <= d < 7])
        else:
            repeat_text = repeat_type
        self.repeat_label.setText(f"🔁 {repeat_text}")
        
        # 빌드명
        buildname = self.schedule.get('buildname', '')
        self.buildname_label.setText(f"📦 {buildname}")
        
        # 옵션 + AWS URL + Branch
        option = self.schedule.get('option', '')
        
        # AWS URL - 마지막 슬래시 뒤 부분만 표시
        awsurl = self.schedule.get('awsurl', '').strip()
        if awsurl:
            # 마지막 슬래시 이후 부분 추출
            url_parts = awsurl.rstrip('/').split('/')
            aws_display = url_parts[-1] if url_parts else '없음'
        else:
            aws_display = '없음'
        
        # Branch
        branch = self.schedule.get('branch', '').strip()
        branch_display = branch if branch else '없음'
        
        option_text = f"⚙️ {option} | 🌐 AWS: {aws_display} | 🌿 Branch: {branch_display}"
        self.option_label.setText(option_text)
        
        # 활성화 상태
        enabled = self.schedule.get('enabled', True)
        self.enabled_checkbox.setChecked(enabled)
        
        # 비활성화 시 반투명 효과
        if not enabled:
            self.setStyleSheet("background-color: #f5f5f5; opacity: 0.7;")
        else:
            self.setStyleSheet("background-color: white;")
    
    def on_toggle_clicked(self):
        """활성화 토글 클릭"""
        self.toggle_requested.emit(self.schedule_id)
    
    def on_edit_clicked(self):
        """편집 버튼 클릭"""
        self.edit_requested.emit(self.schedule_id)
    
    def on_delete_clicked(self):
        """삭제 버튼 클릭"""
        self.delete_requested.emit(self.schedule_id)
    
    def on_run_clicked(self):
        """실행 버튼 클릭"""
        self.run_requested.emit(self.schedule_id)
    
    def on_copy_clicked(self):
        """복사 버튼 클릭"""
        self.copy_requested.emit(self.schedule_id)
    
    def update_schedule(self, schedule: Dict[str, Any]):
        """스케줄 데이터 업데이트"""
        self.schedule = schedule
        self.update_ui()
    
    def set_running_status(self, is_running: bool, status_message: str = ''):
        """
        실행 상태 설정
        
        Args:
            is_running: 실행 중 여부
            status_message: 상태 메시지 (예: '파일 복사 중...', '완료')
        """
        self.is_running = is_running
        
        if is_running:
            self.status_label.setText(f"🔄 {status_message or '실행 중...'}")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 9pt;")
            self.status_label.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 무한 진행 모드
            self.progress_bar.setVisible(True)
            self.run_button.setEnabled(False)
            self.setStyleSheet("background-color: #FFF3E0; border-left: 3px solid #FF9800;")
        else:
            if status_message:
                # 완료 메시지 표시 (3초 후 사라짐)
                self.status_label.setText(f"✅ {status_message}")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 9pt;")
            else:
                self.status_label.setVisible(False)
            
            self.progress_bar.setVisible(False)
            self.run_button.setEnabled(True)
            
            # 활성화 상태에 따라 스타일 복원
            enabled = self.schedule.get('enabled', True)
            if enabled:
                self.setStyleSheet("background-color: white;")
            else:
                self.setStyleSheet("background-color: #f5f5f5; opacity: 0.7;")

