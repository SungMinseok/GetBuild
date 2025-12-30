# 🚀 피드백 시스템 설정 가이드

## ⚡ 빠른 시작

### 1. 환경 변수 설정

#### PowerShell (권장)
```powershell
.\setup_env.ps1
```

#### CMD
```cmd
setup_env.bat
```

### 2. 토큰 입력
스크립트 실행 시 프롬프트가 나타나면 **관리자에게 받은 토큰**을 입력하세요:
```
Slack Bot Token 입력: [여기에 토큰 붙여넣기]
Slack Channel ID 입력: [여기에 채널 ID 붙여넣기]
```

### 3. 앱 실행
```bash
python index.py
```

### 4. 피드백 제출
```
[💬 피드백] 버튼 클릭 → 작성 → 보내기
```

---

## 🧪 테스트

환경 변수가 제대로 설정되었는지 확인:
```bash
python test_env_feedback.py
```

---

## 🐛 문제 해결

### "invalid_auth" 오류
**해결**: `.\setup_env.ps1` 재실행 후 올바른 토큰 입력

### "xoxb-YOUR-BOT-TOKEN-HERE" 오류
**해결**: 환경 변수 미설정, `.\setup_env.ps1` 실행

### 환경 변수가 사라짐
**해결**: 터미널 재시작 시 `.\setup_env.ps1` 재실행 필요

---

## 💡 영구 설정 (선택사항)

매번 설정하기 싫으면 Windows 시스템 환경 변수에 등록:
```
Windows 설정 → 시스템 → 정보 → 고급 시스템 설정
→ 환경 변수 → 시스템 변수 → 새로 만들기
→ DEFAULT_SLACK_BOT_TOKEN, DEFAULT_SLACK_CHANNEL_ID 추가
```

---

## 📝 참고

- 토큰 정보는 관리자에게 문의
- `SLACK_CREDENTIALS.txt` 파일은 Git에 커밋되지 않음
- 자세한 내용은 `SLACK_TOKEN_SETUP.md` 참고

