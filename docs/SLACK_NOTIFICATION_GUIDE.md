# 슬랙 알림 기능 가이드

QuickBuild의 스케줄 실행 시 슬랙(Slack) 채널로 알림을 받을 수 있는 기능입니다.

## 목차
1. [기능 개요](#기능-개요)
2. [슬랙 Webhook 설정](#슬랙-webhook-설정)
3. [hook.json 설정](#hookjson-설정)
4. [스케줄에 슬랙 알림 추가](#스케줄에-슬랙-알림-추가)
5. [알림 메시지 예시](#알림-메시지-예시)
6. [테스트 방법](#테스트-방법)
7. [문제 해결](#문제-해결)

---

## 기능 개요

스케줄 실행 시 다음 3가지 시점에 슬랙 알림을 전송합니다:

1. **시작 알림** - 스케줄이 실행될 때
2. **완료 알림** - 스케줄이 성공적으로 완료되었을 때
3. **실패 알림** - 스케줄 실행 중 오류가 발생했을 때

### 특징
- ✅ 한글 메시지 지원
- ✅ 상태별 색상 구분 (시작: 파란색, 완료: 녹색, 실패: 빨간색)
- ✅ 여러 채널에 대한 Webhook URL 관리
- ✅ 스케줄별로 개별 설정 가능

---

## 슬랙 Webhook 설정

### 1. Slack Incoming Webhook 생성

1. 슬랙 워크스페이스에 로그인합니다.
2. [Slack API 페이지](https://api.slack.com/apps)로 이동합니다.
3. **Create New App** 버튼을 클릭합니다.
4. **From scratch** 선택 후, 앱 이름과 워크스페이스를 지정합니다.
5. 좌측 메뉴에서 **Incoming Webhooks**를 선택합니다.
6. **Activate Incoming Webhooks**를 켭니다 (ON).
7. 하단의 **Add New Webhook to Workspace** 버튼을 클릭합니다.
8. 알림을 받을 채널을 선택하고 허용합니다.
9. 생성된 **Webhook URL**을 복사합니다.
   - 형식: `https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_TOKEN`

### 2. Webhook URL 확인

생성된 Webhook URL은 다음과 같은 형식입니다:
```
https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_TOKEN
```

⚠️ **주의**: 이 URL은 민감한 정보이므로 외부에 공개하지 마세요!

---

## hook.json 설정

프로젝트 루트 디렉토리에 `hook.json` 파일을 생성하고 Webhook URL을 등록합니다.

### hook.json 파일 예시

```json
[
  {
    "name": "QA 알림 채널",
    "url": "https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_TOKEN_HERE"
  },
  {
    "name": "개발 팀 채널",
    "url": "https://hooks.slack.com/services/ANOTHER_WORKSPACE/ANOTHER_CHANNEL/ANOTHER_TOKEN"
  },
  {
    "name": "테스트 채널",
    "url": "https://hooks.slack.com/services/TEST_WORKSPACE/TEST_CHANNEL/TEST_TOKEN"
  }
]
```

### 파일 구조 설명

- `name`: 채널 이름 (UI에서 드롭다운에 표시됨)
- `url`: Slack Incoming Webhook URL

### 파일 위치

```
GetBuild_clean/
├── index.py
├── slack.py
├── hook.json          ← 여기에 생성
└── schedule.json
```

---

## 스케줄에 슬랙 알림 추가

### 1. 스케줄 편집 다이얼로그 열기

- QuickBuild 메인 화면에서 스케줄의 **✏ 편집** 버튼을 클릭합니다.
- 또는 새 스케줄을 생성합니다 (**+ 스케줄 추가** 버튼).

### 2. 슬랙 알림 설정

스케줄 편집 다이얼로그 하단에 **슬랙 알림 (선택사항)** 섹션이 있습니다.

1. **슬랙 알림 사용** 체크박스를 체크합니다.
2. **Webhook URL** 드롭다운에서:
   - `hook.json`에 등록된 채널 중 하나를 선택하거나
   - 직접 Webhook URL을 입력할 수 있습니다.
3. **🔄** 버튼을 클릭하면 `hook.json`에서 최신 목록을 불러옵니다.

### 3. 저장

- **저장** 버튼을 클릭하면 설정이 저장됩니다.

### 4. 슬랙 알림 상태 확인

스케줄 아이템 위젯에서 슬랙 알림이 활성화된 경우 **📢 슬랙 ON** 표시가 나타납니다.

---

## 알림 메시지 예시

### 시작 알림

```
🔔 스케줄 알림: game_SEL 빌드 복사

상태: 시작
옵션: 클라복사
빌드: CompileBuild_DEV_game_SEL_271167_r306671
```

**색상**: 파란색 (#2196F3)

### 완료 알림

```
🔔 스케줄 알림: game_SEL 빌드 복사

상태: 완료
빌드 복사가 성공적으로 완료되었습니다.
```

**색상**: 녹색 (good)

### 실패 알림

```
🔔 스케줄 알림: game_dev 서버 패치

상태: 실패
FileNotFoundError: 빌드 파일을 찾을 수 없습니다.
```

**색상**: 빨간색 (danger)

---

## 테스트 방법

### 1. 테스트 스크립트 실행

프로젝트 루트에서 다음 명령을 실행합니다:

```bash
python test_slack_notification.py
```

이 스크립트는:
- `hook.json`에서 첫 번째 Webhook URL을 사용합니다.
- 5가지 유형의 알림 메시지를 전송합니다.
- 각 테스트의 성공/실패를 출력합니다.

### 2. 수동 테스트

1. QuickBuild를 실행합니다.
2. 슬랙 알림이 설정된 스케줄을 생성합니다.
3. **▶ 실행** 버튼을 눌러 수동으로 실행합니다.
4. 슬랙 채널에서 알림을 확인합니다.

---

## 문제 해결

### Q1. "채널 ID를 찾을 수 없습니다" (channel_not_found) 오류

이 오류의 **가장 흔한 원인은 봇이 채널에 추가되지 않은 것**입니다.

**✅ 해결 방법 (순서대로):**

1. **먼저 봇을 채널에 초대하세요** (가장 중요!)
   ```
   - Slack 앱을 열고 해당 채널로 이동
   - 채널 메시지 입력창에 다음을 입력:
     /invite @봇이름
   
   예: /invite @QuickBuild
   
   - 봇이 추가되면 "○○○님이 #채널에 추가되었습니다" 메시지가 표시됩니다
   ```

2. **채널 ID가 정확한지 확인**
   - Slack 채널 클릭 → 오른쪽 상단 ⋮ → "채널 세부정보 보기"
   - 하단에서 "채널 ID" 복사
   - 공개 채널: `C`로 시작 (예: C0123456789)
   - 비공개 채널: `G`로 시작 (예: G0123456789)

3. **Bot Token 권한 확인**
   - https://api.slack.com/apps 접속
   - 앱 선택 → "OAuth & Permissions" 메뉴
   - "Scopes" 섹션에서 다음 권한이 있는지 확인:
     - ✓ `channels:history` (공개 채널)
     - ✓ `channels:read` (공개 채널)
     - ✓ `groups:history` (비공개 채널)
     - ✓ `groups:read` (비공개 채널)
     - ✓ `chat:write` (메시지 전송)
   - 권한이 없다면 추가 후 "Reinstall to Workspace" 클릭
   - 새로운 Bot Token을 복사하여 다시 설정

**로그 확인:**
- QuickBuild 메인 화면 하단의 로그 영역에서 `[Slack]` 메시지를 확인합니다.
- 상세한 오류 원인과 해결 방법이 표시됩니다.

---

### Q2. 슬랙 알림이 전송되지 않습니다.

**확인 사항:**
1. `hook.json` 파일이 프로젝트 루트에 존재하는지 확인
2. Webhook URL이 올바른지 확인 (`https://hooks.slack.com/services/...` 형식)
3. 스케줄에서 **슬랙 알림 사용** 체크박스가 체크되어 있는지 확인
4. Webhook URL이 입력되어 있는지 확인
5. 네트워크 연결 상태 확인

**로그 확인:**
- QuickBuild 메인 화면 하단의 로그 영역에서 `[슬랙 알림 오류]` 메시지를 확인합니다.

### Q3. 한글이 깨져서 표시됩니다.

이 문제는 발생하지 않아야 합니다. `slack.py`에서 UTF-8 인코딩을 사용하고 있습니다.

만약 발생한다면:
1. Python 버전 확인 (3.7 이상 권장)
2. `requests` 라이브러리 업데이트: `pip install --upgrade requests`

### Q4. Webhook URL을 변경하고 싶습니다.

1. `hook.json` 파일을 편집합니다.
2. QuickBuild에서 스케줄 편집 다이얼로그를 열고 **🔄** 버튼을 클릭합니다.
3. 새로운 Webhook URL을 선택합니다.

### Q5. 여러 채널에 동시에 알림을 보낼 수 있나요?

현재 버전에서는 스케줄당 하나의 Webhook URL만 설정할 수 있습니다.

여러 채널에 알림을 보내려면:
- 같은 스케줄을 여러 개 복사하고 각각 다른 Webhook URL을 설정합니다.

### Q6. 알림이 너무 많이 옵니다.

스케줄별로 슬랙 알림을 켜거나 끌 수 있습니다:
1. 스케줄 편집 다이얼로그에서 **슬랙 알림 사용** 체크박스를 해제합니다.
2. **저장** 버튼을 클릭합니다.

---

## 추가 정보

### 관련 파일

- `slack.py` - 슬랙 메시지 전송 모듈
- `hook.json` - Webhook URL 관리 파일
- `test_slack_notification.py` - 테스트 스크립트
- `ui/schedule_dialog.py` - 스케줄 편집 UI (슬랙 알림 설정)
- `ui/schedule_item_widget.py` - 스케줄 아이템 위젯 (슬랙 상태 표시)
- `index.py` - 메인 애플리케이션 (슬랙 알림 발송 로직)

### 의존성

슬랙 알림 기능은 다음 Python 패키지를 사용합니다:
- `requests` - HTTP 요청 (Webhook 전송)
- `slack_sdk` - (선택사항, OAuth 토큰 방식)

### 보안 주의사항

⚠️ **중요**: `hook.json` 파일에는 민감한 Webhook URL이 포함되어 있습니다.

- Git에 커밋하지 마세요!
- `.gitignore`에 `hook.json`을 추가하는 것을 권장합니다.
- 외부에 공유하지 마세요.

---

## 지원

문제가 발생하거나 추가 기능이 필요한 경우:
1. 로그 파일을 확인하세요.
2. 개발팀에 문의하세요.

---

**최종 업데이트**: 2025-11-07




