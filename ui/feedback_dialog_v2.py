"""피드백 및 버그 제보 다이얼로그 - 중앙 서버 방식"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QLineEdit, QRadioButton,
                             QButtonGroup, QMessageBox, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import json
import os
import requests
from datetime import datetime


class FeedbackSubmitThread(QThread):
    """피드백 제출 워커 스레드 - 중앙 서버 방식"""
    finished = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, feedback_type, reporter, title, content, app_version):
        super().__init__()
        self.feedback_type = feedback_type
        self.reporter = reporter
        self.title = title
        self.content = content
        self.app_version = app_version
        
        # 중앙 서버 엔드포인트
        # TODO: Lambda 배포 후 실제 API Gateway URL로 변경
        # 예: https://abc123.execute-api.ap-northeast-2.amazonaws.com/default/getbuild-feedback
        self.server_url = os.environ.get(
            'FEEDBACK_SERVER_URL',
            'https://your-lambda-url.execute-api.ap-northeast-2.amazonaws.com/default/getbuild-feedback'
        )
    
    def run(self):
        try:
            # 중앙 서버로 데이터 전송
            data = {
                "type": self.feedback_type,
                "reporter": self.reporter,
                "title": self.title,
                "content": self.content,
                "app_version": self.app_version,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                self.server_url,
                json=data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                message = "제출 완료!\n\n"
                
                if result.get('github_issue_url'):
                    message += f"GitHub Issue: {result['github_issue_url']}\n"
                if result.get('slack_sent'):
                    message += "Slack 알림: ✅ 전송됨\n"
                
                self.finished.emit(True, message)
            else:
                self.finished.emit(False, f"서버 오류 (Status: {response.status_code})")
                
        except requests.exceptions.Timeout:
            self.finished.emit(False, "서버 응답 시간 초과")
        except requests.exceptions.ConnectionError:
            self.finished.emit(False, "서버 연결 실패")
        except Exception as e:
            self.finished.emit(False, f"오류 발생: {str(e)}")


class FeedbackDialogV2(QDialog):
    """피드백 및 버그 제보 다이얼로그 - 중앙 서버 방식"""
    
    def __init__(self, parent=None, app_version="1.0.0"):
        super().__init__(parent)
        self.app_version = app_version
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("버그 및 피드백 제보")
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        
        layout = QVBoxLayout()
        
        # 안내 메시지
        info_label = QLabel(
            "💡 제출된 내용은 개발팀에 자동으로 전달됩니다.\n"
            "별도의 설정 없이 바로 사용하실 수 있습니다."
        )
        info_label.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # 유형 선택
        type_group = QGroupBox("제보 유형")
        type_layout = QHBoxLayout()
        
        self.type_group = QButtonGroup()
        self.bug_radio = QRadioButton("🐛 버그")
        self.feedback_radio = QRadioButton("💡 피드백")
        self.bug_radio.setChecked(True)
        
        self.type_group.addButton(self.bug_radio)
        self.type_group.addButton(self.feedback_radio)
        
        type_layout.addWidget(self.bug_radio)
        type_layout.addWidget(self.feedback_radio)
        type_layout.addStretch()
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # 제보자 정보
        form_group = QGroupBox("제보 정보")
        form_layout = QFormLayout()
        
        self.reporter_input = QLineEdit()
        self.reporter_input.setPlaceholderText("이름 또는 이메일")
        self.reporter_input.setText(self.load_last_reporter())
        form_layout.addRow("제보자:", self.reporter_input)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("간단한 제목을 입력하세요")
        form_layout.addRow("제목:", self.title_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 내용
        content_group = QGroupBox("상세 내용")
        content_layout = QVBoxLayout()
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText(
            "버그인 경우:\n"
            "- 발생 상황\n"
            "- 재현 방법\n"
            "- 예상 동작 vs 실제 동작\n\n"
            "피드백인 경우:\n"
            "- 개선 제안 사항\n"
            "- 기대하는 기능"
        )
        content_layout.addWidget(self.content_input)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.submit_btn = QPushButton("보내기")
        self.submit_btn.clicked.connect(self.submit_feedback)
        self.submit_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 8px 16px;")
        button_layout.addWidget(self.submit_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_last_reporter(self):
        """마지막 제보자 정보 로드"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get('last_feedback_reporter', '')
        except:
            pass
        return ''
    
    def save_last_reporter(self, reporter):
        """마지막 제보자 정보 저장"""
        try:
            settings = {}
            if os.path.exists('settings.json'):
                with open('settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            settings['last_feedback_reporter'] = reporter
            
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"제보자 정보 저장 오류: {e}")
    
    def submit_feedback(self):
        """피드백 제출"""
        # 입력 검증
        reporter = self.reporter_input.text().strip()
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        if not reporter:
            QMessageBox.warning(self, "입력 오류", "제보자를 입력하세요.")
            self.reporter_input.setFocus()
            return
        
        if not title:
            QMessageBox.warning(self, "입력 오류", "제목을 입력하세요.")
            self.title_input.setFocus()
            return
        
        if not content:
            QMessageBox.warning(self, "입력 오류", "내용을 입력하세요.")
            self.content_input.setFocus()
            return
        
        # 제출 확인
        feedback_type = "버그" if self.bug_radio.isChecked() else "피드백"
        
        reply = QMessageBox.question(
            self,
            "제출 확인",
            f"다음 내용을 제출하시겠습니까?\n\n"
            f"유형: {feedback_type}\n"
            f"제목: {title}\n"
            f"제보자: {reporter}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # 제보자 정보 저장
        self.save_last_reporter(reporter)
        
        # 버튼 비활성화
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("제출 중...")
        
        # 워커 스레드 시작
        self.submit_thread = FeedbackSubmitThread(
            feedback_type, reporter, title, content, self.app_version
        )
        self.submit_thread.finished.connect(self.on_submit_finished)
        self.submit_thread.start()
    
    def on_submit_finished(self, success, message):
        """제출 완료 처리"""
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("보내기")
        
        if success:
            QMessageBox.information(self, "제출 완료", message)
            self.accept()
        else:
            QMessageBox.warning(self, "제출 실패", message)

