"""슬랙 토큰 및 채널 추가 다이얼로그"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt
import json
import os


class AddSlackItemDialog(QDialog):
    """슬랙 Bot Token 또는 채널 ID 추가 다이얼로그"""
    
    def __init__(self, parent=None, item_type='bot_token'):
        """
        Args:
            parent: 부모 위젯
            item_type: 'bot_token' 또는 'channel'
        """
        super().__init__(parent)
        self.item_type = item_type
        
        if item_type == 'bot_token':
            self.setWindowTitle("Bot Token 추가")
        else:
            self.setWindowTitle("채널 ID 추가")
        
        self.setModal(True)
        self.setMinimumWidth(450)
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 설명 레이블
        if self.item_type == 'bot_token':
            description = "새로운 Bot Token을 추가합니다.\n이름과 토큰 값을 입력하세요.\n보안상 pbb 봇토큰은 기본 빌드에 포함되어 있지 않습니다. 성민석에게 문의 부탁드립니다."
        else:
            description = "새로운 채널을 추가합니다.\n채널 이름과 채널 ID를 입력하세요."
        
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        
        # 이름 입력
        self.name_edit = QLineEdit()
        if self.item_type == 'bot_token':
            self.name_edit.setPlaceholderText("예: QA팀 Bot")
        else:
            self.name_edit.setPlaceholderText("예: 빌드 공지 채널")
        form_layout.addRow("이름:", self.name_edit)
        
        # 값 입력 (Token 또는 Channel ID)
        self.value_edit = QLineEdit()
        if self.item_type == 'bot_token':
            self.value_edit.setPlaceholderText("xoxb-xxxxx...")
            #self.value_edit.setEchoMode(QLineEdit.Password)
            form_layout.addRow("Bot Token:", self.value_edit)
        else:
            self.value_edit.setPlaceholderText("C0XXXXXXX 또는 G0XXXXXXX")
            form_layout.addRow("채널 ID:", self.value_edit)
            
            # 채널 ID 안내
            help_text = QLabel(
                "채널 ID 찾는 방법:\n"
                "1. Slack 채널 클릭\n"
                "2. 오른쪽 상단 ⋮ 메뉴\n"
                "3. '채널 세부정보 보기'\n"
                "4. 하단에서 채널 ID 복사"
            )
            help_text.setStyleSheet("color: #888; font-size: 9pt; margin-top: 5px;")
            help_text.setWordWrap(True)
            form_layout.addRow("", help_text)
        
        layout.addLayout(form_layout)
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("저장")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.on_save)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_save(self):
        """저장 버튼 클릭"""
        name = self.name_edit.text().strip()
        value = self.value_edit.text().strip()
        
        # 유효성 검사
        if not name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력하세요.")
            return
        
        if not value:
            if self.item_type == 'bot_token':
                QMessageBox.warning(self, "입력 오류", "Bot Token을 입력하세요.")
            else:
                QMessageBox.warning(self, "입력 오류", "채널 ID를 입력하세요.")
            return
        
        # 채널 ID 형식 검사 (간단한 검증)
        if self.item_type == 'channel':
            if not (value.startswith('C') or value.startswith('G') or value.startswith('D')):
                result = QMessageBox.question(
                    self, 
                    "형식 확인", 
                    "채널 ID가 일반적인 형식(C, G, D로 시작)이 아닙니다.\n계속하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if result != QMessageBox.Yes:
                    return
        
        self.accept()
    
    def get_data(self):
        """입력된 데이터 반환"""
        return {
            'name': self.name_edit.text().strip(),
            'value': self.value_edit.text().strip()
        }


class SlackTokenManager:
    """슬랙 토큰 및 채널 정보 관리 클래스"""
    
    TOKENS_FILE = 'slack_tokens.json'
    
    @staticmethod
    def load_tokens():
        """slack_tokens.json에서 Bot Token 목록 로드"""
        if not os.path.exists(SlackTokenManager.TOKENS_FILE):
            return []
        
        try:
            with open(SlackTokenManager.TOKENS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('bot_tokens', [])
        except Exception as e:
            print(f"Bot Token 로드 오류: {e}")
            return []
    
    @staticmethod
    def load_channels():
        """slack_tokens.json에서 채널 목록 로드"""
        if not os.path.exists(SlackTokenManager.TOKENS_FILE):
            return []
        
        try:
            with open(SlackTokenManager.TOKENS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('channels', [])
        except Exception as e:
            print(f"채널 로드 오류: {e}")
            return []
    
    @staticmethod
    def save_token(name, token):
        """새 Bot Token 저장"""
        data = SlackTokenManager._load_all_data()
        
        # 중복 체크
        for item in data['bot_tokens']:
            if item['name'] == name:
                raise ValueError(f"이미 '{name}' 이름의 Bot Token이 존재합니다.")
        
        data['bot_tokens'].append({
            'name': name,
            'token': token
        })
        
        SlackTokenManager._save_all_data(data)
    
    @staticmethod
    def save_channel(name, channel_id):
        """새 채널 저장"""
        data = SlackTokenManager._load_all_data()
        
        # 중복 체크
        for item in data['channels']:
            if item['name'] == name:
                raise ValueError(f"이미 '{name}' 이름의 채널이 존재합니다.")
        
        data['channels'].append({
            'name': name,
            'channel_id': channel_id
        })
        
        SlackTokenManager._save_all_data(data)
    
    @staticmethod
    def delete_token(name):
        """Bot Token 삭제"""
        data = SlackTokenManager._load_all_data()
        data['bot_tokens'] = [item for item in data['bot_tokens'] if item['name'] != name]
        SlackTokenManager._save_all_data(data)
    
    @staticmethod
    def delete_channel(name):
        """채널 삭제"""
        data = SlackTokenManager._load_all_data()
        data['channels'] = [item for item in data['channels'] if item['name'] != name]
        SlackTokenManager._save_all_data(data)
    
    @staticmethod
    def get_token_by_name(name):
        """이름으로 Bot Token 검색"""
        tokens = SlackTokenManager.load_tokens()
        for item in tokens:
            if item['name'] == name:
                return item['token']
        return None
    
    @staticmethod
    def get_channel_by_name(name):
        """이름으로 채널 ID 검색"""
        channels = SlackTokenManager.load_channels()
        for item in channels:
            if item['name'] == name:
                return item['channel_id']
        return None
    
    @staticmethod
    def _load_all_data():
        """전체 데이터 로드"""
        if not os.path.exists(SlackTokenManager.TOKENS_FILE):
            return {
                'bot_tokens': [],
                'channels': []
            }
        
        try:
            with open(SlackTokenManager.TOKENS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            return {
                'bot_tokens': [],
                'channels': []
            }
    
    @staticmethod
    def _save_all_data(data):
        """전체 데이터 저장"""
        try:
            with open(SlackTokenManager.TOKENS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise Exception(f"데이터 저장 오류: {e}")

