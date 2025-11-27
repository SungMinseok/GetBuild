"""스케줄 생성/편집 다이얼로그"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QTimeEdit, QCheckBox, QGroupBox, 
                             QRadioButton, QButtonGroup, QMessageBox, QFormLayout, QFileDialog)
from PyQt5.QtCore import QTime, Qt
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime


class ScheduleDialog(QDialog):
    """스케줄 생성/편집 다이얼로그"""
    
    def __init__(self, parent=None, schedule: Optional[Dict[str, Any]] = None, 
                 buildnames: List[str] = None, options: List[str] = None,
                 default_src_path: str = '', default_dest_path: str = ''):
        """
        Args:
            parent: 부모 위젯
            schedule: 편집할 스케줄 (None이면 새로 생성)
            buildnames: 빌드명 목록
            options: 실행 옵션 목록
            default_src_path: 기본 소스 경로
            default_dest_path: 기본 로컬 경로
        """
        super().__init__(parent)
        self.schedule = schedule
        self.buildnames = buildnames or []
        self.options = options or []
        self.default_src_path = default_src_path
        self.default_dest_path = default_dest_path
        self.is_edit_mode = schedule is not None
        self.parent_window = parent  # 부모 윈도우 참조 저장 (find_latest_build 사용)
        
        self.setWindowTitle("스케줄 편집" if self.is_edit_mode else "스케줄 생성")
        self.setModal(True)
        self.setMinimumWidth(550)
        
        self.init_ui()
        
        if self.is_edit_mode:
            self.load_schedule_data()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 기본 정보
        basic_group = self.create_basic_info_group()
        layout.addWidget(basic_group)
        
        # 반복 설정
        repeat_group = self.create_repeat_settings_group()
        layout.addWidget(repeat_group)
        
        # 빌드 설정
        build_group = self.create_build_settings_group()
        layout.addWidget(build_group)
        
        # AWS 설정
        aws_group = self.create_aws_settings_group()
        layout.addWidget(aws_group)
        
        # 슬랙 알림 설정
        slack_group = self.create_slack_settings_group()
        layout.addWidget(slack_group)
        
        # 버튼
        button_layout = self.create_buttons()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_basic_info_group(self) -> QGroupBox:
        """기본 정보 그룹"""
        group = QGroupBox("기본 정보")
        layout = QFormLayout()
        
        # 스케줄 이름
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("스케줄 이름 (선택사항)")
        layout.addRow("이름:", self.name_edit)
        
        # 실행 시간
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        layout.addRow("실행 시간:", self.time_edit)
        
        # 실행 옵션
        self.option_combo = QComboBox()
        self.option_combo.addItems(self.options)
        self.option_combo.currentTextChanged.connect(self.on_option_changed)
        layout.addRow("실행 옵션:", self.option_combo)
        
        # 활성화
        self.enabled_checkbox = QCheckBox("활성화")
        self.enabled_checkbox.setChecked(True)
        layout.addRow("", self.enabled_checkbox)
        
        group.setLayout(layout)
        return group
    
    def create_repeat_settings_group(self) -> QGroupBox:
        """반복 설정 그룹"""
        group = QGroupBox("반복 설정")
        layout = QVBoxLayout()
        
        # 반복 유형 라디오 버튼
        self.repeat_group = QButtonGroup()
        
        self.once_radio = QRadioButton("일회성")
        self.once_radio.setChecked(True)
        self.repeat_group.addButton(self.once_radio, 0)
        layout.addWidget(self.once_radio)
        
        self.daily_radio = QRadioButton("매일 반복")
        self.repeat_group.addButton(self.daily_radio, 1)
        layout.addWidget(self.daily_radio)
        
        self.weekly_radio = QRadioButton("주간 반복 (특정 요일)")
        self.repeat_group.addButton(self.weekly_radio, 2)
        layout.addWidget(self.weekly_radio)
        
        # 요일 선택 (주간 반복용)
        weekday_layout = QHBoxLayout()
        weekday_layout.addWidget(QLabel("반복 요일:"))
        
        self.weekday_checkboxes = []
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        for i, day in enumerate(weekdays):
            checkbox = QCheckBox(day)
            checkbox.setEnabled(False)  # 기본적으로 비활성화
            self.weekday_checkboxes.append(checkbox)
            weekday_layout.addWidget(checkbox)
        
        weekday_layout.addStretch()
        layout.addLayout(weekday_layout)
        
        # 라디오 버튼 변경 시 요일 체크박스 활성화/비활성화
        self.weekly_radio.toggled.connect(self.on_weekly_toggled)
        
        group.setLayout(layout)
        return group
    
    def create_build_settings_group(self) -> QGroupBox:
        """빌드 설정 그룹"""
        group = QGroupBox("빌드 설정")
        layout = QFormLayout()
        
        # 빌드 소스 경로
        src_layout = QHBoxLayout()
        self.src_path_edit = QLineEdit()
        self.src_path_edit.setText(self.default_src_path)
        self.src_path_edit.setPlaceholderText(r"\\pubg-pds\PBB\Builds")
        src_layout.addWidget(self.src_path_edit)
        
        src_browse_btn = QPushButton("...")
        src_browse_btn.setFixedWidth(30)
        src_browse_btn.clicked.connect(self.browse_src_path)
        src_layout.addWidget(src_browse_btn)
        layout.addRow("소스 경로:", src_layout)
        
        # 로컬 저장 경로
        dest_layout = QHBoxLayout()
        self.dest_path_edit = QLineEdit()
        self.dest_path_edit.setText(self.default_dest_path)
        self.dest_path_edit.setPlaceholderText("C:/mybuild")
        dest_layout.addWidget(self.dest_path_edit)
        
        dest_browse_btn = QPushButton("...")
        dest_browse_btn.setFixedWidth(30)
        dest_browse_btn.clicked.connect(self.browse_dest_path)
        dest_layout.addWidget(dest_browse_btn)
        layout.addRow("로컬 경로:", dest_layout)
        
        # 빌드 선택 모드: 최신 / 지정
        mode_layout = QHBoxLayout()
        self.build_mode_group = QButtonGroup()
        
        self.build_mode_latest = QRadioButton("최신")
        self.build_mode_latest.setChecked(True)
        self.build_mode_latest.toggled.connect(self.on_build_mode_changed)
        self.build_mode_group.addButton(self.build_mode_latest, 0)
        mode_layout.addWidget(self.build_mode_latest)
        
        self.build_mode_fixed = QRadioButton("지정")
        self.build_mode_group.addButton(self.build_mode_fixed, 1)
        self.build_mode_fixed.toggled.connect(self.on_build_mode_changed)
        mode_layout.addWidget(self.build_mode_fixed)
        
        mode_layout.addStretch()
        layout.addRow("빌드 모드:", mode_layout)
        
        # Prefix (빌드명 필터) - 항상 활성화
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("예: game_SEL, game_progression")
        layout.addRow("Prefix:", self.prefix_edit)
        
        # 빌드명 드롭다운 + 새로고침 (우측에 배치)
        buildname_layout = QHBoxLayout()
        self.buildname_combo = QComboBox()
        self.buildname_combo.setEditable(True)
        self.buildname_combo.addItems(self.buildnames)
        self.buildname_combo.setEnabled(False)  # 기본적으로 '최신' 모드이므로 비활성화
        buildname_layout.addWidget(self.buildname_combo)
        
        self.refresh_builds_btn = QPushButton("🔄")
        self.refresh_builds_btn.setFixedWidth(40)
        self.refresh_builds_btn.setToolTip("Prefix 기준으로 빌드명 목록 새로고침")
        self.refresh_builds_btn.clicked.connect(self.refresh_build_list)
        buildname_layout.addWidget(self.refresh_builds_btn)
        
        layout.addRow("빌드명:", buildname_layout)
        
        group.setLayout(layout)
        return group
    
    def browse_src_path(self):
        """소스 경로 찾아보기"""
        current_path = self.src_path_edit.text() or self.default_src_path
        path = QFileDialog.getExistingDirectory(self, "소스 경로 선택", current_path)
        if path:
            self.src_path_edit.setText(path)
    
    def browse_dest_path(self):
        """로컬 경로 찾아보기"""
        current_path = self.dest_path_edit.text() or self.default_dest_path
        path = QFileDialog.getExistingDirectory(self, "로컬 경로 선택", current_path)
        if path:
            self.dest_path_edit.setText(path)
    
    def create_aws_settings_group(self) -> QGroupBox:
        """AWS 설정 그룹"""
        group = QGroupBox("AWS 설정 (선택사항)")
        layout = QFormLayout()
        
        # AWS URL
        self.awsurl_edit = QLineEdit()
        self.awsurl_edit.setPlaceholderText("https://awsdeploy.pbb-qa.pubg.io/environment/...")
        layout.addRow("AWS URL:", self.awsurl_edit)
        
        # Branch
        self.branch_edit = QLineEdit()
        self.branch_edit.setPlaceholderText("game, game_dev, etc.")
        layout.addRow("Branch:", self.branch_edit)
        
        group.setLayout(layout)
        return group
    
    def create_slack_settings_group(self) -> QGroupBox:
        """슬랙 알림 설정 그룹"""
        group = QGroupBox("슬랙 알림 (선택사항)")
        layout = QFormLayout()
        
        # 슬랙 알림 활성화 체크박스
        self.slack_enabled_checkbox = QCheckBox("슬랙 알림 사용")
        self.slack_enabled_checkbox.toggled.connect(self.on_slack_enabled_toggled)
        layout.addRow("", self.slack_enabled_checkbox)
        
        # 알림 타입 선택
        notification_type_layout = QHBoxLayout()
        self.notification_type_group = QButtonGroup()
        
        self.notification_standalone_radio = QRadioButton("단독 알림")
        self.notification_standalone_radio.setChecked(True)
        self.notification_standalone_radio.setEnabled(False)
        self.notification_standalone_radio.toggled.connect(self.on_notification_type_changed)
        self.notification_type_group.addButton(self.notification_standalone_radio, 0)
        notification_type_layout.addWidget(self.notification_standalone_radio)
        
        self.notification_thread_radio = QRadioButton("스레드 댓글 알림")
        self.notification_thread_radio.setEnabled(False)
        self.notification_type_group.addButton(self.notification_thread_radio, 1)
        notification_type_layout.addWidget(self.notification_thread_radio)
        
        notification_type_layout.addStretch()
        layout.addRow("알림 타입:", notification_type_layout)
        
        # Webhook URL 선택/입력 (더 이상 사용 안 함 - 호환성을 위해 숨김 처리)
        webhook_layout = QHBoxLayout()
        
        # 드롭다운 (hook.json에서 로드)
        self.webhook_combo = QComboBox()
        self.webhook_combo.setEditable(True)
        self.webhook_combo.setPlaceholderText("Webhook URL을 선택하거나 직접 입력하세요")
        self.webhook_combo.setEnabled(False)
        self.webhook_combo.setVisible(False)  # 숨김 처리
        self.load_webhook_urls()
        webhook_layout.addWidget(self.webhook_combo)
        
        # 새로고침 버튼
        refresh_webhook_btn = QPushButton("🔄")
        refresh_webhook_btn.setFixedWidth(40)
        refresh_webhook_btn.setToolTip("hook.json에서 Webhook URL 목록 새로고침")
        refresh_webhook_btn.clicked.connect(self.load_webhook_urls)
        refresh_webhook_btn.setVisible(False)  # 숨김 처리
        webhook_layout.addWidget(refresh_webhook_btn)
        
        # Webhook URL 라벨도 숨김 처리를 위해 따로 저장
        self.webhook_label = QLabel("Webhook URL:")
        self.webhook_label.setVisible(False)
        # layout.addRow은 아래에서 처리
        
        # Bot Token 입력 (단독 알림 및 스레드 댓글 모두 사용)
        self.bot_token_edit = QLineEdit()
        self.bot_token_edit.setPlaceholderText("xoxb-xxxxx... (필수)")
        self.bot_token_edit.setEnabled(False)
        #self.bot_token_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("Bot Token:", self.bot_token_edit)
        
        # 채널 ID 입력 (단독 알림 및 스레드 댓글 모두 사용)
        self.channel_id_edit = QLineEdit()
        self.channel_id_edit.setPlaceholderText("C0XXXXXXX (공개채널) 또는 G0XXXXXXX (비공개)")
        self.channel_id_edit.setEnabled(False)
        self.channel_id_edit.setToolTip(
            "채널 ID 찾는 방법:\n"
            "1. Slack 채널 클릭\n"
            "2. 오른쪽 상단 ⋮ 메뉴\n"
            "3. '채널 세부정보 보기'\n"
            "4. 하단에서 채널 ID 복사\n\n"
            "공개 채널: C로 시작\n"
            "비공개 채널: G로 시작\n"
            "DM: D로 시작 (권장하지 않음)"
        )
        layout.addRow("채널 ID:", self.channel_id_edit)
        
        # 스레드 검색 키워드 입력 (스레드 댓글용만 사용)
        self.thread_keyword_edit = QLineEdit()
        self.thread_keyword_edit.setPlaceholderText("예: 251110 빌드 세팅 스레드")
        self.thread_keyword_edit.setEnabled(False)
        self.thread_keyword_edit.setToolTip("스레드 댓글 알림 시에만 사용됩니다.")
        layout.addRow("스레드 키워드:", self.thread_keyword_edit)
        
        # 첫 메시지 입력 (알림에 포함될 메시지)
        first_message_layout = QVBoxLayout()
        self.first_message_edit = QLineEdit()
        self.first_message_edit.setPlaceholderText("알림에 포함될 메시지 (예: yymmdd 입력 시 현재 날짜로 변환)")
        self.first_message_edit.setEnabled(False)
        self.first_message_edit.textChanged.connect(self.on_first_message_changed)
        first_message_layout.addWidget(self.first_message_edit)
        
        # 미리보기 레이블
        self.first_message_preview = QLabel("")
        self.first_message_preview.setStyleSheet("color: gray; font-size: 10pt; padding-left: 5px;")
        self.first_message_preview.setWordWrap(True)
        first_message_layout.addWidget(self.first_message_preview)
        
        layout.addRow("첫 메시지:", first_message_layout)
        
        group.setLayout(layout)
        return group
    
    def load_webhook_urls(self):
        """hook.json에서 Webhook URL 목록 로드"""
        hook_file = 'hook.json'
        
        # 기존 항목 저장 (사용자가 직접 입력한 경우 보존)
        current_text = self.webhook_combo.currentText()
        
        self.webhook_combo.clear()
        self.webhook_combo.addItem("", "")  # 빈 항목
        
        if os.path.exists(hook_file):
            try:
                with open(hook_file, 'r', encoding='utf-8') as f:
                    hooks = json.load(f)
                
                if isinstance(hooks, list):
                    for hook in hooks:
                        if isinstance(hook, dict):
                            name = hook.get('name', '')
                            url = hook.get('url', '')
                            if name and url:
                                self.webhook_combo.addItem(f"{name} ({url[:30]}...)", url)
            except Exception as e:
                print(f"hook.json 로드 오류: {e}")
        
        # 이전 값 복원
        if current_text:
            self.webhook_combo.setEditText(current_text)
    
    def on_slack_enabled_toggled(self, checked: bool):
        """슬랙 알림 활성화 토글"""
        self.notification_standalone_radio.setEnabled(checked)
        self.notification_thread_radio.setEnabled(checked)
        
        # 알림 타입에 따라 필드 활성화
        if checked:
            self.on_notification_type_changed()
        else:
            # 모든 필드 비활성화
            self.webhook_combo.setEnabled(False)
            self.bot_token_edit.setEnabled(False)
            self.channel_id_edit.setEnabled(False)
            self.thread_keyword_edit.setEnabled(False)
            self.first_message_edit.setEnabled(False)
    
    def on_notification_type_changed(self):
        """알림 타입 변경 (단독/스레드)"""
        is_standalone = self.notification_standalone_radio.isChecked()
        
        if is_standalone:
            # 단독 알림: Webhook URL 대신 Bot Token과 채널 ID 사용
            self.webhook_combo.setEnabled(False)
            self.bot_token_edit.setEnabled(True)
            self.channel_id_edit.setEnabled(True)
            self.thread_keyword_edit.setEnabled(False)
            self.first_message_edit.setEnabled(True)
        else:
            # 스레드 댓글: 모든 필드 활성화
            self.webhook_combo.setEnabled(False)  # bot token 사용으로 변경됨
            self.bot_token_edit.setEnabled(True)
            self.channel_id_edit.setEnabled(True)
            self.thread_keyword_edit.setEnabled(True)
            self.first_message_edit.setEnabled(True)
    
    def convert_date_keywords(self, text: str) -> str:
        """
        메시지 내의 날짜 키워드를 실제 날짜로 변환
        
        Args:
            text: 변환할 텍스트 (예: "yymmdd 빌드 테스트")
        
        Returns:
            변환된 텍스트 (예: "251117 빌드 테스트")
        """
        if not text:
            return text
        
        now = datetime.now()
        
        # yymmdd -> 251117 (2자리 연도 + 월 + 일)
        if 'yymmdd' in text:
            date_str = now.strftime('%y%m%d')
            text = text.replace('yymmdd', date_str)
        
        # yyyymmdd -> 20251117 (4자리 연도 + 월 + 일)
        if 'yyyymmdd' in text:
            date_str = now.strftime('%Y%m%d')
            text = text.replace('yyyymmdd', date_str)
        
        # mmdd -> 1117 (월 + 일)
        if 'mmdd' in text:
            date_str = now.strftime('%m%d')
            text = text.replace('mmdd', date_str)
        
        return text
    
    def on_first_message_changed(self):
        """첫 메시지 입력 시 미리보기 업데이트"""
        original_text = self.first_message_edit.text()
        converted_text = self.convert_date_keywords(original_text)
        
        if original_text and original_text != converted_text:
            self.first_message_preview.setText(f"→ {converted_text}")
        else:
            self.first_message_preview.setText("")
    
    def create_buttons(self) -> QHBoxLayout:
        """버튼 생성"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # 취소 버튼
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # 저장 버튼
        save_btn = QPushButton("저장" if self.is_edit_mode else "생성")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.on_save)
        layout.addWidget(save_btn)
        
        return layout
    
    def on_weekly_toggled(self, checked: bool):
        """주간 반복 토글 시 요일 체크박스 활성화/비활성화"""
        for checkbox in self.weekday_checkboxes:
            checkbox.setEnabled(checked)
    
    def on_option_changed(self, option: str):
        """
        실행 옵션 변경 시 필요하지 않은 필드 비활성화
        단, 비활성화하되 값이 있으면 저장됨 (get_schedule_data에서 처리)
        """
        # 각 옵션별 필요한 필드 정의
        # True: 필요, False: 불필요
        field_requirements = {
            '클라복사': {
                'src_path': True,
                'dest_path': True,
                'buildname': True,
                'awsurl': False,
                'branch': False
            },
            '전체복사': {
                'src_path': True,
                'dest_path': True,
                'buildname': True,
                'awsurl': False,
                'branch': False
            },
            '서버복사': {
                'src_path': True,
                'dest_path': True,
                'buildname': True,
                'awsurl': False,
                'branch': False
            },
            '서버업로드': {
                'src_path': True,
                'dest_path': False,
                'buildname': True,
                'awsurl': False,
                'branch': True
            },
            '서버업로드및패치': {
                'src_path': True,
                'dest_path': False,
                'buildname': True,
                'awsurl': True,
                'branch': True
            },
            '서버패치': {
                'src_path': True,
                'dest_path': False,
                'buildname': True,
                'awsurl': True,
                'branch': True
            },
            '서버삭제': {
                'src_path': False,
                'dest_path': False,
                'buildname': False,
                'awsurl': True,
                'branch': False
            },
            '빌드굽기': {
                'src_path': False,
                'dest_path': False,
                'buildname': False,
                'awsurl': False,
                'branch': True
            },
            '테스트(로그)': {
                'src_path': False,
                'dest_path': False,
                'buildname': False,
                'awsurl': False,
                'branch': False
            },
            'TEST': {
                'src_path': False,
                'dest_path': False,
                'buildname': False,
                'awsurl': False,
                'branch': False
            }
        }
        
        # 현재 옵션의 필드 요구사항 가져오기
        requirements = field_requirements.get(option, {
            'src_path': True,
            'dest_path': True,
            'buildname': True,
            'awsurl': True,
            'branch': True
        })
        
        # 필드 활성화/비활성화 (값은 유지)
        self.src_path_edit.setEnabled(requirements.get('src_path', True))
        self.dest_path_edit.setEnabled(requirements.get('dest_path', True))
        self.awsurl_edit.setEnabled(requirements.get('awsurl', True))
        self.branch_edit.setEnabled(requirements.get('branch', True))
        
        # buildname 관련 필드들
        buildname_required = requirements.get('buildname', True)
        self.prefix_edit.setEnabled(buildname_required)
        # buildname_combo는 빌드 모드에 따라 제어되므로 여기서는 건드리지 않음
        # 단, 빌드 모드 라디오 버튼은 비활성화
        self.build_mode_latest.setEnabled(buildname_required)
        self.build_mode_fixed.setEnabled(buildname_required)
        self.refresh_builds_btn.setEnabled(buildname_required)
    
    def on_build_mode_changed(self):
        """빌드 모드 변경 (최신 / 지정)"""
        is_fixed_mode = self.build_mode_fixed.isChecked()
        # 지정 모드일 때만 빌드명 드롭다운 활성화
        self.buildname_combo.setEnabled(is_fixed_mode)
        # Prefix는 항상 활성화 (self.prefix_edit는 항상 사용 가능)
    
    def refresh_build_list(self):
        """Prefix 기준으로 빌드명 드롭다운 새로고침"""
        prefix = self.prefix_edit.text().strip()
        if not prefix:
            QMessageBox.warning(self, "입력 오류", "Prefix를 입력하세요.")
            return
        
        src_path = self.src_path_edit.text().strip()
        if not src_path:
            QMessageBox.warning(self, "입력 오류", "소스 경로를 입력하세요.")
            return
        
        import os
        import re
        
        if not os.path.isdir(src_path):
            QMessageBox.warning(self, "경로 오류", f"소스 경로가 존재하지 않습니다:\n{src_path}")
            return
        
        try:
            # Prefix 포함된 폴더 찾기
            matching_folders = []
            for folder in os.listdir(src_path):
                folder_path = os.path.join(src_path, folder)
                if os.path.isdir(folder_path) and prefix in folder:
                    matching_folders.append(folder)
            
            if not matching_folders:
                QMessageBox.information(self, "결과 없음", f"'{prefix}' Prefix를 포함한 빌드가 없습니다.")
                return
            
            # 리비전 기준 정렬 (최신순)
            def extract_revision(name: str) -> int:
                m = re.search(r'(?:^|_)r(\d+)(?:$|_)', name)
                if m:
                    return int(m.group(1))
                m2 = re.search(r'r(\d+)', name)
                return int(m2.group(1)) if m2 else -1
            
            matching_folders.sort(key=extract_revision, reverse=True)
            
            # 빌드명 드롭다운 업데이트
            self.buildname_combo.clear()
            self.buildname_combo.addItems(matching_folders)
            
            QMessageBox.information(self, "새로고침 완료", 
                                   f"{len(matching_folders)}개의 빌드를 찾았습니다.\n최신: {matching_folders[0]}")
        
        except Exception as e:
            QMessageBox.critical(self, "오류", f"빌드 목록 새로고침 오류:\n{e}")
    
    def load_schedule_data(self):
        """스케줄 데이터 로드 (편집 모드)"""
        if not self.schedule:
            return
        
        # 기본 정보
        self.name_edit.setText(self.schedule.get('name', ''))
        
        time_str = self.schedule.get('time', '')
        if time_str:
            time = QTime.fromString(time_str, 'HH:mm')
            self.time_edit.setTime(time)
        
        option = self.schedule.get('option', '')
        idx = self.option_combo.findText(option)
        if idx >= 0:
            self.option_combo.setCurrentIndex(idx)
        
        self.enabled_checkbox.setChecked(self.schedule.get('enabled', True))
        
        # 반복 설정
        repeat_type = self.schedule.get('repeat_type', 'once')
        if repeat_type == 'once':
            self.once_radio.setChecked(True)
        elif repeat_type == 'daily':
            self.daily_radio.setChecked(True)
        elif repeat_type == 'weekly':
            self.weekly_radio.setChecked(True)
            repeat_days = self.schedule.get('repeat_days', [])
            for day in repeat_days:
                if 0 <= day < len(self.weekday_checkboxes):
                    self.weekday_checkboxes[day].setChecked(True)
        
        # 빌드 설정 (경로 포함)
        src_path = self.schedule.get('src_path', '')
        if src_path:
            self.src_path_edit.setText(src_path)
        
        dest_path = self.schedule.get('dest_path', '')
        if dest_path:
            self.dest_path_edit.setText(dest_path)
        
        # 빌드 모드 (최신 / 지정)
        build_mode = self.schedule.get('build_mode', 'latest')
        if build_mode == 'fixed':
            self.build_mode_fixed.setChecked(True)
        else:
            self.build_mode_latest.setChecked(True)
        
        # Prefix
        prefix = self.schedule.get('prefix', '')
        self.prefix_edit.setText(prefix)
        
        # 빌드명
        buildname = self.schedule.get('buildname', '')
        idx = self.buildname_combo.findText(buildname)
        if idx >= 0:
            self.buildname_combo.setCurrentIndex(idx)
        else:
            self.buildname_combo.setEditText(buildname)
        
        # AWS 설정
        self.awsurl_edit.setText(self.schedule.get('awsurl', ''))
        self.branch_edit.setText(self.schedule.get('branch', ''))
        
        # 슬랙 알림 설정
        slack_webhook = self.schedule.get('slack_webhook', '')
        slack_enabled = self.schedule.get('slack_enabled', False)
        notification_type = self.schedule.get('notification_type', 'standalone')
        bot_token = self.schedule.get('bot_token', '')
        channel_id = self.schedule.get('channel_id', '')
        thread_keyword = self.schedule.get('thread_keyword', '')
        
        self.slack_enabled_checkbox.setChecked(slack_enabled)
        
        # 알림 타입 설정
        if notification_type == 'thread':
            self.notification_thread_radio.setChecked(True)
        else:
            self.notification_standalone_radio.setChecked(True)
        
        # Webhook URL
        if slack_webhook:
            # Webhook URL이 드롭다운에 있는지 확인
            idx = self.webhook_combo.findData(slack_webhook)
            if idx >= 0:
                self.webhook_combo.setCurrentIndex(idx)
            else:
                # 없으면 직접 입력된 것으로 설정
                self.webhook_combo.setEditText(slack_webhook)
        
        # 스레드 댓글 알림 설정
        self.bot_token_edit.setText(bot_token)
        self.channel_id_edit.setText(channel_id)
        self.thread_keyword_edit.setText(thread_keyword)
        
        # 첫 메시지
        first_message = self.schedule.get('first_message', '')
        self.first_message_edit.setText(first_message)
        # 미리보기 업데이트
        if first_message:
            self.on_first_message_changed()
    
    def on_save(self):
        """저장 버튼 클릭"""
        # 유효성 검사
        if not self.option_combo.currentText():
            QMessageBox.warning(self, "입력 오류", "실행 옵션을 선택하세요.")
            return
        
        # 주간 반복인 경우 최소 하나의 요일 선택 필요
        if self.weekly_radio.isChecked():
            if not any(cb.isChecked() for cb in self.weekday_checkboxes):
                QMessageBox.warning(self, "입력 오류", "주간 반복은 최소 하나의 요일을 선택해야 합니다.")
                return
        
        self.accept()
    
    def get_schedule_data(self) -> Dict[str, Any]:
        """입력된 스케줄 데이터 반환 (비활성화된 필드도 값이 있으면 저장)"""
        # 반복 유형
        if self.once_radio.isChecked():
            repeat_type = 'once'
            repeat_days = []
        elif self.daily_radio.isChecked():
            repeat_type = 'daily'
            repeat_days = []
        else:  # weekly
            repeat_type = 'weekly'
            repeat_days = [i for i, cb in enumerate(self.weekday_checkboxes) if cb.isChecked()]
        
        # 기본 이름 생성
        name = self.name_edit.text().strip()
        if not name:
            time_str = self.time_edit.time().toString('HH:mm')
            option = self.option_combo.currentText()
            name = f"{option} - {time_str}"
        
        # 빌드 모드
        build_mode = 'fixed' if self.build_mode_fixed.isChecked() else 'latest'
        
        # 슬랙 알림 설정 (비활성화 상태여도 값이 있으면 저장)
        slack_enabled = self.slack_enabled_checkbox.isChecked()
        notification_type = 'thread' if self.notification_thread_radio.isChecked() else 'standalone'
        
        # 모든 필드의 값을 가져옴 (활성화 여부와 무관)
        bot_token = self.bot_token_edit.text().strip()
        channel_id = self.channel_id_edit.text().strip()
        thread_keyword = self.thread_keyword_edit.text().strip()
        first_message = self.first_message_edit.text().strip()
        
        # webhook은 더 이상 사용하지 않지만 호환성을 위해 빈 값 저장
        slack_webhook = ''
        
        data = {
            'name': name,
            'time': self.time_edit.time().toString('HH:mm'),
            'option': self.option_combo.currentText(),
            'src_path': self.src_path_edit.text().strip(),
            'dest_path': self.dest_path_edit.text().strip(),
            'build_mode': build_mode,
            'prefix': self.prefix_edit.text().strip(),
            'buildname': self.buildname_combo.currentText(),
            'awsurl': self.awsurl_edit.text().strip(),
            'branch': self.branch_edit.text().strip(),
            'repeat_type': repeat_type,
            'repeat_days': repeat_days,
            'enabled': self.enabled_checkbox.isChecked(),
            'slack_enabled': slack_enabled,
            'slack_webhook': slack_webhook,  # 호환성
            'notification_type': notification_type,
            'bot_token': bot_token,
            'channel_id': channel_id,
            'thread_keyword': thread_keyword,
            'first_message': first_message
        }
        
        # 편집 모드면 ID 유지
        if self.is_edit_mode and self.schedule:
            data['id'] = self.schedule.get('id')
            data['created_at'] = self.schedule.get('created_at')
        
        return data

