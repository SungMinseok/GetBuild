# 🔒 Slack 토큰 설정 가이드

## ⚠️ 중요: GitHub Push Protection

GitHub가 Slack API 토큰을 감지하여 push를 차단합니다.
따라서 **환경 변수**를 사용하여 토큰을 관리해야 합니다.

---

## 🔧 설정 방법

### 방법 1: 자동 설정 스크립트 (권장)

#### PowerShell
```powershell
# 스크립트 실행 (대화형으로 토큰 입력)
.\setup_env.ps1

# 입력 프롬프트:
# Slack Bot Token 입력: [여기에 토큰 입력]
# Slack Channel ID 입력: [여기에 채널 ID 입력]
```

#### CMD
```cmd
# 스크립트 실행 (대화형으로 토큰 입력)
setup_env.bat

# 입력 프롬프트:
# Slack Bot Token 입력: [여기에 토큰 입력]
# Slack Channel ID 입력: [여기에 채널 ID 입력]
```

### 방법 2: 수동 설정

#### Windows
```cmd
# 임시 설정 (현재 세션만)
set DEFAULT_SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
set DEFAULT_SLACK_CHANNEL_ID=YOUR-CHANNEL-ID

# 영구 설정 (시스템 환경 변수)
setx DEFAULT_SLACK_BOT_TOKEN "xoxb-YOUR-BOT-TOKEN-HERE"
setx DEFAULT_SLACK_CHANNEL_ID "YOUR-CHANNEL-ID"
```

#### Linux/Mac
```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export DEFAULT_SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
export DEFAULT_SLACK_CHANNEL_ID=YOUR-CHANNEL-ID

# 적용
source ~/.bashrc  # 또는 source ~/.zshrc
```

### 방법 2: .env 파일

#### 1. .env 파일 생성
```bash
# .env.example을 복사
cp .env.example .env
```

#### 2. .env 파일 편집
```env
DEFAULT_SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
DEFAULT_SLACK_CHANNEL_ID=YOUR-CHANNEL-ID
```

#### 3. python-dotenv 설치
```bash
pip install python-dotenv
```

#### 4. index.py에서 로드 (선택사항)
```python
from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드
```

---

## 📝 토큰 정보 확인 방법

### Slack Bot Token 확인
```
1. https://api.slack.com/apps 접속
2. 앱 선택
3. OAuth & Permissions 메뉴
4. Bot User OAuth Token 복사
   형식: xoxb-***-***-***
```

### Slack Channel ID 확인
```
1. Slack 웹/앱 열기
2. 채널 클릭
3. 채널 이름 클릭 → 채널 세부정보
4. 하단에 채널 ID 표시
   형식: C09RYABRECB
```

---

## 🧪 테스트

### 환경 변수 확인
```bash
# Windows
echo %DEFAULT_SLACK_BOT_TOKEN%
echo %DEFAULT_SLACK_CHANNEL_ID%

# Linux/Mac
echo $DEFAULT_SLACK_BOT_TOKEN
echo $DEFAULT_SLACK_CHANNEL_ID
```

### 앱 실행
```bash
python index.py
```

### 테스트 스크립트 수정
`test_slack_upload.py`:
```python
import os

# 환경 변수에서 로드
bot_token = os.environ.get('DEFAULT_SLACK_BOT_TOKEN', 'xoxb-YOUR-BOT-TOKEN-HERE')
channel_id = os.environ.get('DEFAULT_SLACK_CHANNEL_ID', 'YOUR-CHANNEL-ID-HERE')
```

---

## 🔒 보안

### Git에 커밋하지 말 것
```
❌ 실제 토큰을 코드에 하드코딩
❌ .env 파일을 Git에 커밋
✅ 환경 변수 사용
✅ .env.example만 커밋 (예시용)
```

### .gitignore 확인
```gitignore
# .gitignore에 이미 추가됨
.env
token.json
slack_tokens.json
feedback_tokens.json
```

---

## 💡 작동 방식

### ui/feedback_dialog_slack.py
```python
def load_encrypted_config(self):
    # 1순위: 환경 변수
    bot_token = os.environ.get('SLACK_BOT_TOKEN')
    channel_id = os.environ.get('SLACK_CHANNEL_ID')
    
    if bot_token and channel_id:
        return {'bot_token': bot_token, 'channel_id': channel_id}
    
    # 2순위: 기본값 (환경 변수에서 로드)
    default_token = os.environ.get('DEFAULT_SLACK_BOT_TOKEN', 'xoxb-YOUR-BOT-TOKEN-HERE')
    default_channel = os.environ.get('DEFAULT_SLACK_CHANNEL_ID', 'C09RYABRECB')
    
    return {
        'bot_token': default_token,
        'channel_id': default_channel
    }
```

---

## 🚀 빠른 시작

### Windows (개발 환경)
```cmd
# 1. 환경 변수 설정 (실제 토큰으로 교체)
set DEFAULT_SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
set DEFAULT_SLACK_CHANNEL_ID=YOUR-CHANNEL-ID

# 2. 앱 실행
python index.py

# 3. 피드백 테스트
# 메뉴 → 버그 및 피드백 → 보내기
```

### Windows (배포 환경)
```cmd
# 1. 시스템 환경 변수 설정 (관리자 권한, 실제 토큰으로 교체)
setx DEFAULT_SLACK_BOT_TOKEN "xoxb-YOUR-BOT-TOKEN-HERE" /M
setx DEFAULT_SLACK_CHANNEL_ID "YOUR-CHANNEL-ID" /M

# 2. 재부팅 또는 새 터미널 열기

# 3. 앱 실행
python index.py
```

---

## 🐛 문제 해결

### "xoxb-YOUR-BOT-TOKEN-HERE" 오류
**원인**: 환경 변수가 설정되지 않음

**해결**:
```cmd
# 환경 변수 설정 (실제 토큰으로 교체)
set DEFAULT_SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
set DEFAULT_SLACK_CHANNEL_ID=YOUR-CHANNEL-ID

# 앱 재실행
python index.py
```

### GitHub Push Protection 오류
**원인**: 코드에 실제 토큰이 하드코딩됨

**해결**:
```
✅ 이미 수정됨!
- slack_tokens.json.example: 예시 토큰으로 변경
- test_slack_upload.py: 환경 변수 사용
- ui/feedback_dialog_slack.py: 환경 변수 사용
```

---

## 📚 참고

### 환경 변수 우선순위
```
1. SLACK_BOT_TOKEN (최우선)
2. DEFAULT_SLACK_BOT_TOKEN (기본값)
3. 'xoxb-YOUR-BOT-TOKEN-HERE' (폴백)
```

### 채널 ID 확인 방법
```
1. Slack 웹/앱 열기
2. 채널 클릭
3. 채널 이름 클릭 → 채널 세부정보
4. 하단에 채널 ID 표시
   예: C09RYABRECB
```

---

## ✅ 체크리스트

- [ ] 환경 변수 설정 완료
- [ ] 환경 변수 확인 (echo 명령)
- [ ] 앱 실행 테스트
- [ ] 피드백 전송 테스트
- [ ] Slack 채널에서 메시지 확인

---

## 🎉 완료!

이제 Git에 안전하게 커밋할 수 있습니다!

```bash
git add .
git commit -m "fix: Slack 토큰을 환경 변수로 변경"
git push
```

**보안을 유지하면서 기능을 사용할 수 있습니다!** 🔒✅

