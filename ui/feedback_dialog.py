"""피드백 및 버그 제보 다이얼로그"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QLineEdit, QRadioButton,
                             QButtonGroup, QMessageBox, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import json
import os
import requests
from datetime import datetime


class FeedbackSubmitThread(QThread):
    """피드백 제출 워커 스레드"""
    finished = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, feedback_type, reporter, title, content, tokens_config):
        super().__init__()
        self.feedback_type = feedback_type
        self.reporter = reporter
        self.title = title
        self.content = content
        self.tokens_config = tokens_config
    
    def run(self):
        try:
            results = []
            
            # GitHub Issue 등록
            if self.tokens_config.get('github', {}).get('enabled', False):
                github_result = self._submit_to_github()
                results.append(f"GitHub: {github_result}")
            
            # Slack 알림
            if self.tokens_config.get('slack', {}).get('enabled', False):
                slack_result = self._submit_to_slack()
                results.append(f"Slack: {slack_result}")
            
            if not results:
                self.finished.emit(False, "GitHub 또는 Slack 설정이 활성화되지 않았습니다.\n\nfeedback_tokens.json 파일을 확인하세요.")
                return
            
            message = "제출 완료!\n\n" + "\n".join(results)
            self.finished.emit(True, message)
            
        except Exception as e:
            self.finished.emit(False, f"오류 발생: {str(e)}")
    
    def _submit_to_github(self):
        """GitHub Issue 생성"""
        try:
            github_config = self.tokens_config['github']
            token = github_config['token']
            repo_owner = github_config['repo_owner']
            repo_name = github_config['repo_name']
            
            # GitHub API 엔드포인트
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
            
            # Issue 제목 및 본문
            issue_title = f"[{self.feedback_type}] {self.title}"
            issue_body = f"""## 제보자
{self.reporter}

## 유형
{self.feedback_type}

## 내용
{self.content}

---
*자동 제출: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            
            # 라벨 설정
            labels = ['feedback'] if self.feedback_type == '피드백' else ['bug']
            
            # API 요청
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            data = {
                'title': issue_title,
                'body': issue_body,
                'labels': labels
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 201:
                issue_number = response.json()['number']
                issue_url = response.json()['html_url']
                return f"✅ Issue #{issue_number} 생성됨\n{issue_url}"
            else:
                return f"❌ 실패 (Status: {response.status_code})"
                
        except Exception as e:
            return f"❌ 오류: {str(e)}"
    
    def _submit_to_slack(self):
        """Slack 알림 전송"""
        try:
            slack_config = self.tokens_config['slack']
            webhook_url = slack_config['webhook_url']
            
            # Slack 메시지 포맷
            emoji = "🐛" if self.feedback_type == '버그' else "💡"
            color = "#ff0000" if self.feedback_type == '버그' else "#36a64f"
            
            message = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"{emoji} [{self.feedback_type}] {self.title}",
                        "fields": [
                            {
                                "title": "제보자",
                                "value": self.reporter,
                                "short": True
                            },
                            {
                                "title": "유형",
                                "value": self.feedback_type,
                                "short": True
                            },
                            {
                                "title": "내용",
                                "value": self.content,
                                "short": False
                            }
                        ],
                        "footer": "GetBuild 피드백 시스템",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=message, timeout=10)
            
            if response.status_code == 200:
                return "✅ 알림 전송됨"
            else:
                return f"❌ 실패 (Status: {response.status_code})"
                
        except Exception as e:
            return f"❌ 오류: {str(e)}"


class FeedbackDialog(QDialog):
    """피드백 및 버그 제보 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tokens_config = self.load_tokens_config()
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("버그 및 피드백 제보")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout()
        
        # 설정 상태 표시
        status_group = QGroupBox("제출 설정 상태")
        status_layout = QVBoxLayout()
        
        github_enabled = self.tokens_config.get('github', {}).get('enabled', False)
        slack_enabled = self.tokens_config.get('slack', {}).get('enabled', False)
        
        github_status = "✅ 활성화" if github_enabled else "❌ 비활성화"
        slack_status = "✅ 활성화" if slack_enabled else "❌ 비활성화"
        
        status_layout.addWidget(QLabel(f"GitHub Issue: {github_status}"))
        status_layout.addWidget(QLabel(f"Slack 알림: {slack_status}"))
        
        if not github_enabled and not slack_enabled:
            warning_label = QLabel("⚠️ 제출 기능을 사용하려면 feedback_tokens.json 파일을 설정하세요.")
            warning_label.setStyleSheet("color: orange; font-weight: bold;")
            status_layout.addWidget(warning_label)
            
            config_btn = QPushButton("설정 파일 열기")
            config_btn.clicked.connect(self.open_config_file)
            status_layout.addWidget(config_btn)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
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
        #self.title_input.setPlaceholderText("간단한 제목을 입력하세요")
        form_layout.addRow("제목:", self.title_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 내용
        content_group = QGroupBox("상세 내용")
        content_layout = QVBoxLayout()
        
        self.content_input = QTextEdit()
        # self.content_input.setPlaceholderText(
        #     "버그인 경우:\n"
        #     "- 발생 상황\n"
        #     "- 재현 방법\n"
        #     "- 예상 동작 vs 실제 동작\n\n"
        #     "피드백인 경우:\n"
        #     "- 개선 제안 사항\n"
        #     "- 기대하는 기능\n"
        #     "- 사용 시나리오"
        # )
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
    
    def load_tokens_config(self):
        """토큰 설정 로드"""
        config_file = 'feedback_tokens.json'
        
        if not os.path.exists(config_file):
            # 샘플 파일이 있으면 복사 안내
            if os.path.exists('feedback_tokens.json.example'):
                return {}
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"토큰 설정 로드 오류: {e}")
            return {}
    
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
    
    def open_config_file(self):
        """설정 파일 열기"""
        config_file = 'feedback_tokens.json'
        example_file = 'feedback_tokens.json.example'
        
        if not os.path.exists(config_file):
            if os.path.exists(example_file):
                reply = QMessageBox.question(
                    self,
                    "설정 파일 생성",
                    "feedback_tokens.json 파일이 없습니다.\n\n"
                    "예제 파일(feedback_tokens.json.example)을 복사하여 생성하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    import shutil
                    shutil.copy(example_file, config_file)
                    QMessageBox.information(
                        self,
                        "파일 생성 완료",
                        "feedback_tokens.json 파일이 생성되었습니다.\n\n"
                        "파일을 열어서 GitHub Token과 Slack Webhook URL을 설정하세요."
                    )
                else:
                    return
            else:
                QMessageBox.warning(
                    self,
                    "파일 없음",
                    "feedback_tokens.json.example 파일이 없습니다.\n\n"
                    "수동으로 feedback_tokens.json 파일을 생성하세요."
                )
                return
        
        # 파일 열기
        try:
            os.startfile(config_file)
        except Exception as e:
            QMessageBox.warning(self, "오류", f"파일 열기 실패: {e}")
    
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
            feedback_type, reporter, title, content, self.tokens_config
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

