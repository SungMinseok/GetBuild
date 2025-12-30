"""피드백 및 버그 제보 다이얼로그 - Slack 직접 전송 방식"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QLineEdit, QRadioButton,
                             QButtonGroup, QMessageBox, QGroupBox, QFormLayout,
                             QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QBuffer, QIODevice
from PyQt5.QtGui import QPixmap, QImage, QKeySequence
import json
import os
import requests
from datetime import datetime
import io
import base64


class SlackFeedbackThread(QThread):
    """Slack 피드백 제출 워커 스레드"""
    finished = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, feedback_type, reporter, title, content, app_version, screenshots=None):
        super().__init__()
        self.feedback_type = feedback_type
        self.reporter = reporter
        self.title = title
        self.content = content
        self.app_version = app_version
        self.screenshots = screenshots or []  # QPixmap 리스트
    
    def run(self):
        try:
            # 암호화된 설정 로드
            config = self.load_encrypted_config()
            
            # Slack 메시지 전송
            result = self.send_to_slack(config)
            
            if result['success']:
                message = "✅ 피드백이 성공적으로 전송되었습니다!\n\n"
                message += "확인 후 빠르게 답변드리겠습니다."
                self.finished.emit(True, message)
            else:
                self.finished.emit(False, f"전송 실패: {result.get('error', '알 수 없는 오류')}")
                
        except FileNotFoundError:
            self.finished.emit(False, 
                "설정 파일이 없습니다.\n\n"
                "관리자에게 문의하세요.")
        except Exception as e:
            self.finished.emit(False, f"오류 발생: {str(e)}")
    
    def load_encrypted_config(self):
        """암호화된 설정 로드"""
        # 폴백 1: 환경 변수에서 로드 (최우선)
        bot_token = os.environ.get('SLACK_BOT_TOKEN')
        channel_id = os.environ.get('SLACK_CHANNEL_ID')
        
        if bot_token and channel_id:
            print(f"[Feedback] 환경 변수에서 설정 로드")
            return {'bot_token': bot_token, 'channel_id': channel_id}
        
        # 폴백 2: 하드코딩된 기본값 사용 (개발/배포용)
        # 보안: 이 값들은 Git에 커밋되지만, 실제 사용 시 환경 변수로 오버라이드 권장
        default_token = os.environ.get('DEFAULT_SLACK_BOT_TOKEN', 'xoxb-YOUR-BOT-TOKEN-HERE')
        default_channel = os.environ.get('DEFAULT_SLACK_CHANNEL_ID', 'C09RYABRECB')
        
        print(f"[Feedback] 기본 내장 설정 사용")
        return {
            'bot_token': default_token,
            'channel_id': default_channel
        }
        
        # 참고: 암호화 방식은 cryptography 모듈 의존성 문제로 비활성화
        # 필요 시 환경 변수로 토큰을 오버라이드할 수 있음
    
    def send_to_slack(self, config):
        """Slack으로 메시지 전송 (스크린샷 포함)"""
        bot_token = config['bot_token']
        channel_id = config['channel_id']
        
        # 이모지 및 색상 설정
        emoji = "🐛" if self.feedback_type == '버그' else "💡"
        color = "#ff0000" if self.feedback_type == '버그' else "#36a64f"
        
        # 1. 메인 메시지 전송
        url = "https://slack.com/api/chat.postMessage"
        
        headers = {
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        }
        
        # 메시지 구성
        message = {
            'channel': channel_id,
            'text': f"{emoji} [{self.feedback_type}] {self.title}",
            'attachments': [
                {
                    'color': color,
                    'fields': [
                        {
                            'title': '제보자',
                            'value': self.reporter,
                            'short': True
                        },
                        {
                            'title': '앱 버전',
                            'value': self.app_version,
                            'short': True
                        },
                        {
                            'title': '유형',
                            'value': self.feedback_type,
                            'short': True
                        },
                        {
                            'title': '제출 시간',
                            'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'short': True
                        },
                        {
                            'title': '내용',
                            'value': self.content,
                            'short': False
                        }
                    ],
                    'footer': 'GetBuild 피드백 시스템',
                    'footer_icon': 'https://platform.slack-edge.com/img/default_application_icon.png'
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=message, timeout=10)
        result = response.json()
        
        if not result.get('ok'):
            return {'success': False, 'error': result.get('error', 'Unknown error')}
        
        # 2. 스크린샷 업로드 (있는 경우)
        if self.screenshots:
            thread_ts = result.get('ts')  # 메인 메시지의 타임스탬프
            print(f"[Feedback] 스크린샷 {len(self.screenshots)}개 업로드 시작")
            print(f"[Feedback] 메인 메시지 ts: {thread_ts}")
            
            upload_success = 0
            upload_fail = 0
            
            for idx, pixmap in enumerate(self.screenshots):
                try:
                    print(f"[Feedback] 스크린샷 {idx + 1} 업로드 중... (크기: {pixmap.width()}x{pixmap.height()})")
                    self._upload_screenshot(bot_token, channel_id, pixmap, idx + 1, thread_ts)
                    upload_success += 1
                    print(f"[Feedback] 스크린샷 {idx + 1} 업로드 성공!")
                except Exception as e:
                    upload_fail += 1
                    print(f"[Feedback] 스크린샷 {idx + 1} 업로드 실패: {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"[Feedback] 업로드 완료: 성공 {upload_success}개, 실패 {upload_fail}개")
        
        return {'success': True}
    
    def _upload_screenshot(self, bot_token, channel_id, pixmap, index, thread_ts=None):
        """스크린샷을 Slack에 업로드 (새로운 API 방식)"""
        # QPixmap을 바이트로 변환 (QBuffer 사용)
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        
        # PNG로 저장
        success = pixmap.save(buffer, 'PNG')
        if not success:
            raise Exception("이미지를 PNG로 변환하는데 실패했습니다")
        
        # QBuffer에서 바이트 데이터 추출
        image_data = buffer.data().data()  # QByteArray → bytes
        buffer.close()
        
        if len(image_data) == 0:
            raise Exception("이미지 데이터가 비어있습니다")
        
        print(f"[Feedback] 이미지 크기: {len(image_data)} bytes")
        
        headers = {
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        }
        
        # 1단계: 업로드 URL 요청
        print(f"[Feedback] 1단계: 업로드 URL 요청...")
        upload_url_response = requests.post(
            'https://slack.com/api/files.getUploadURLExternal',
            headers=headers,
            json={
                'filename': f'screenshot_{index}.png',
                'length': len(image_data)
            },
            timeout=10
        )
        upload_url_result = upload_url_response.json()
        
        if not upload_url_result.get('ok'):
            error_msg = upload_url_result.get('error', 'Failed to get upload URL')
            raise Exception(f"업로드 URL 요청 실패: {error_msg}")
        
        upload_url = upload_url_result['upload_url']
        file_id = upload_url_result['file_id']
        print(f"[Feedback] 업로드 URL 획득: file_id={file_id}")
        
        # 2단계: 파일 업로드
        print(f"[Feedback] 2단계: 파일 업로드 중...")
        upload_response = requests.post(
            upload_url,
            data=image_data,
            headers={'Content-Type': 'image/png'},
            timeout=30
        )
        
        if upload_response.status_code != 200:
            raise Exception(f"파일 업로드 실패: HTTP {upload_response.status_code}")
        
        print(f"[Feedback] 파일 업로드 완료")
        
        # 3단계: 업로드 완료 및 채널 공유
        print(f"[Feedback] 3단계: 채널에 공유 중...")
        complete_data = {
            'files': [
                {
                    'id': file_id,
                    'title': f'스크린샷 {index}'
                }
            ],
            'channel_id': channel_id,
        }
        
        # 스레드로 전송
        if thread_ts:
            complete_data['thread_ts'] = thread_ts
        
        # 초기 코멘트 추가
        complete_data['initial_comment'] = f'📸 첨부 이미지 {index}'
        
        complete_response = requests.post(
            'https://slack.com/api/files.completeUploadExternal',
            headers=headers,
            json=complete_data,
            timeout=10
        )
        complete_result = complete_response.json()
        
        print(f"[Feedback] 완료 응답: {complete_result}")
        
        if not complete_result.get('ok'):
            error_msg = complete_result.get('error', 'Upload completion failed')
            raise Exception(f"업로드 완료 실패: {error_msg}")
        
        print(f"[Feedback] 스크린샷 {index} 업로드 성공!")


class FeedbackDialogSlack(QDialog):
    """피드백 및 버그 제보 다이얼로그 - Slack 방식"""
    
    def __init__(self, parent=None, app_version="1.0.0"):
        super().__init__(parent)
        self.app_version = app_version
        self.screenshots = []  # QPixmap 리스트
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("버그 및 피드백 제보")
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        
        layout = QVBoxLayout()
        
        # 안내 메시지
        info_label = QLabel(
            "💬 제출된 내용은 개발팀 Slack 채널로 전송됩니다.\n"
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
        # self.title_input.setPlaceholderText("간단한 제목을 입력하세요")
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
        #     "- 기대하는 기능"
        # )
        content_layout.addWidget(self.content_input)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # 스크린샷 섹션
        screenshot_group = QGroupBox("스크린샷 첨부 (선택사항)")
        screenshot_layout = QVBoxLayout()
        
        # 안내 및 버튼
        screenshot_info = QLabel(
            "💡 Ctrl+V로 클립보드의 이미지를 붙여넣을 수 있습니다.\n"
            "또는 아래 버튼을 클릭하여 붙여넣기하세요."
        )
        screenshot_info.setStyleSheet("color: #64748b; font-size: 12px;")
        screenshot_layout.addWidget(screenshot_info)
        
        paste_btn = QPushButton("📋 클립보드에서 붙여넣기 (Ctrl+V)")
        paste_btn.clicked.connect(self.paste_from_clipboard)
        screenshot_layout.addWidget(paste_btn)
        
        # 스크린샷 미리보기 영역
        self.screenshot_scroll = QScrollArea()
        self.screenshot_scroll.setWidgetResizable(True)
        self.screenshot_scroll.setMaximumHeight(200)
        
        self.screenshot_container = QFrame()
        self.screenshot_container_layout = QHBoxLayout()
        self.screenshot_container_layout.setAlignment(Qt.AlignLeft)
        self.screenshot_container.setLayout(self.screenshot_container_layout)
        
        self.screenshot_scroll.setWidget(self.screenshot_container)
        screenshot_layout.addWidget(self.screenshot_scroll)
        
        screenshot_group.setLayout(screenshot_layout)
        layout.addWidget(screenshot_group)
        
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
        
        # 키보드 단축키 설정 (Ctrl+V)
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """이벤트 필터 - Ctrl+V 감지"""
        if event.type() == event.KeyPress:
            if event.matches(QKeySequence.Paste):
                self.paste_from_clipboard()
                return True
        return super().eventFilter(obj, event)
    
    def paste_from_clipboard(self):
        """클립보드에서 이미지 붙여넣기"""
        from PyQt5.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                self.add_screenshot(pixmap)
                QMessageBox.information(
                    self,
                    "스크린샷 추가됨",
                    f"스크린샷이 추가되었습니다. (총 {len(self.screenshots)}개)"
                )
            else:
                QMessageBox.warning(self, "오류", "클립보드에 유효한 이미지가 없습니다.")
        else:
            QMessageBox.warning(
                self,
                "이미지 없음",
                "클립보드에 이미지가 없습니다.\n\n"
                "스크린샷을 찍거나 이미지를 복사한 후 다시 시도하세요."
            )
    
    def add_screenshot(self, pixmap):
        """스크린샷 추가"""
        self.screenshots.append(pixmap)
        
        # 썸네일 생성 (150x150)
        thumbnail = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 썸네일 프레임 생성
        thumb_frame = QFrame()
        thumb_frame.setFrameStyle(QFrame.Box)
        thumb_frame.setLineWidth(2)
        thumb_layout = QVBoxLayout()
        
        # 이미지 라벨
        img_label = QLabel()
        img_label.setPixmap(thumbnail)
        img_label.setAlignment(Qt.AlignCenter)
        thumb_layout.addWidget(img_label)
        
        # 삭제 버튼
        remove_btn = QPushButton("🗑️ 삭제")
        remove_btn.setMaximumWidth(150)
        screenshot_index = len(self.screenshots) - 1
        remove_btn.clicked.connect(lambda: self.remove_screenshot(screenshot_index, thumb_frame))
        thumb_layout.addWidget(remove_btn)
        
        thumb_frame.setLayout(thumb_layout)
        self.screenshot_container_layout.addWidget(thumb_frame)
    
    def remove_screenshot(self, index, frame):
        """스크린샷 제거"""
        if 0 <= index < len(self.screenshots):
            self.screenshots.pop(index)
            frame.deleteLater()
            
            # 인덱스 재조정
            for i in range(self.screenshot_container_layout.count()):
                widget = self.screenshot_container_layout.itemAt(i).widget()
                if widget:
                    # 버튼의 람다 함수 업데이트 필요 시
                    pass
    
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
            f"다음 내용을 Slack으로 전송하시겠습니까?\n\n"
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
        self.submit_btn.setText("전송 중...")
        
        # 워커 스레드 시작
        self.submit_thread = SlackFeedbackThread(
            feedback_type, reporter, title, content, self.app_version, self.screenshots
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

