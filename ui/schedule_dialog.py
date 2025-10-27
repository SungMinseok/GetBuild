"""스케줄 생성/편집 다이얼로그"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QTimeEdit, QCheckBox, QGroupBox, 
                             QRadioButton, QButtonGroup, QMessageBox, QFormLayout, QFileDialog)
from PyQt5.QtCore import QTime, Qt
from typing import Dict, Any, Optional, List


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
        
        self.setWindowTitle("스케줄 편집" if self.is_edit_mode else "스케줄 생성")
        self.setModal(True)
        self.setMinimumWidth(500)
        
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
        
        # 빌드명
        self.buildname_combo = QComboBox()
        self.buildname_combo.setEditable(True)
        self.buildname_combo.addItems(self.buildnames)
        layout.addRow("빌드명:", self.buildname_combo)
        
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
        """실행 옵션 변경 시 (필요시 추가 처리)"""
        pass
    
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
        
        buildname = self.schedule.get('buildname', '')
        idx = self.buildname_combo.findText(buildname)
        if idx >= 0:
            self.buildname_combo.setCurrentIndex(idx)
        else:
            self.buildname_combo.setEditText(buildname)
        
        # AWS 설정
        self.awsurl_edit.setText(self.schedule.get('awsurl', ''))
        self.branch_edit.setText(self.schedule.get('branch', ''))
    
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
        """입력된 스케줄 데이터 반환"""
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
        
        data = {
            'name': name,
            'time': self.time_edit.time().toString('HH:mm'),
            'option': self.option_combo.currentText(),
            'src_path': self.src_path_edit.text().strip(),
            'dest_path': self.dest_path_edit.text().strip(),
            'buildname': self.buildname_combo.currentText(),
            'awsurl': self.awsurl_edit.text().strip(),
            'branch': self.branch_edit.text().strip(),
            'repeat_type': repeat_type,
            'repeat_days': repeat_days,
            'enabled': self.enabled_checkbox.isChecked()
        }
        
        # 편집 모드면 ID 유지
        if self.is_edit_mode and self.schedule:
            data['id'] = self.schedule.get('id')
            data['created_at'] = self.schedule.get('created_at')
        
        return data

