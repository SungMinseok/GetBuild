# 슬랙 토큰 및 채널 관리 가이드

## 개요

QuickBuild v3.x부터는 슬랙 알림 설정 시 Bot Token과 채널 ID를 이름과 함께 저장하여 관리할 수 있습니다.
이를 통해 여러 토큰과 채널을 쉽게 구분하고 재사용할 수 있습니다.

## 주요 기능

### 1. Bot Token 관리
- **이름 기반 저장**: Bot Token을 알기 쉬운 이름으로 저장
- **드롭다운 선택**: 저장된 토큰을 드롭다운에서 선택
- **코드 표시**: 선택한 토큰의 실제 코드를 확인 가능
- **추가 버튼**: "+" 버튼으로 새 토큰을 즉시 추가

### 2. 채널 ID 관리
- **이름 기반 저장**: 채널 ID를 채널 이름으로 저장
- **드롭다운 선택**: 저장된 채널을 드롭다운에서 선택
- **코드 표시**: 선택한 채널의 실제 ID를 확인 가능
- **추가 버튼**: "+" 버튼으로 새 채널을 즉시 추가

## 사용 방법

### 초기 설정

1. **설정 파일 확인**
   - 프로젝트 루트에 `slack_tokens.json` 파일이 자동 생성됩니다
   - 예시 파일: `slack_tokens.json.example` 참고

2. **Bot Token 추가**
   - 스케줄 편집 다이얼로그 열기
   - "슬랙 알림 (선택사항)" 섹션에서 "슬랙 알림 사용" 체크
   - Bot Token 옆의 "+" 버튼 클릭
   - 이름과 토큰 입력 후 저장

3. **채널 추가**
   - 채널 ID 옆의 "+" 버튼 클릭
   - 채널 이름과 ID 입력 후 저장

### UI 구성

```
┌─ 슬랙 알림 (선택사항) ─────────────────────────────┐
│ ☑ 슬랙 알림 사용                                    │
│                                                     │
│ 알림 타입:                                          │
│   ◉ 단독 알림   ○ 스레드 댓글 알림                  │
│                                                     │
│ Bot Token:                                          │
│   [QA팀 Bot ▼] [xoxb-****...***] [+]              │
│                 ↑드롭다운    ↑코드표시  ↑추가버튼    │
│                                                     │
│ 채널 ID:                                            │
│   [빌드 공지 채널 ▼] [C01234ABCDE] [+]             │
│                      ↑드롭다운   ↑코드표시 ↑추가버튼 │
│                                                     │
│ 스레드 키워드: [________________]                   │
│ 첫 메시지:     [________________]                   │
└─────────────────────────────────────────────────────┘
```

### Bot Token 추가 팝업

```
┌─ Bot Token 추가 ─────────────────────────────┐
│                                               │
│ 새로운 Bot Token을 추가합니다.                │
│ 이름과 토큰 값을 입력하세요.                  │
│                                               │
│ 이름:         [QA팀 Bot________]              │
│ Bot Token:    [YOUR-BOT-TOKEN-HERE]           │
│                                               │
│                        [취소]  [저장]         │
└───────────────────────────────────────────────┘
```

### 채널 추가 팝업

```
┌─ 채널 ID 추가 ───────────────────────────────┐
│                                               │
│ 새로운 채널을 추가합니다.                     │
│ 채널 이름과 채널 ID를 입력하세요.             │
│                                               │
│ 이름:      [빌드 공지 채널___]                │
│ 채널 ID:   [C0XXXXXXX_______]                 │
│                                               │
│ 채널 ID 찾는 방법:                            │
│ 1. Slack 채널 클릭                            │
│ 2. 오른쪽 상단 ⋮ 메뉴                         │
│ 3. '채널 세부정보 보기'                       │
│ 4. 하단에서 채널 ID 복사                      │
│                                               │
│                        [취소]  [저장]         │
└───────────────────────────────────────────────┘
```

## 데이터 저장 형식

### slack_tokens.json

```json
{
    "bot_tokens": [
        {
            "name": "QA팀 Bot",
            "token": "xoxb-YOUR-BOT-TOKEN-HERE"
        },
        {
            "name": "개발팀 Bot",
            "token": "xoxb-YOUR-ANOTHER-BOT-TOKEN-HERE"
        }
    ],
    "channels": [
        {
            "name": "빌드 공지 채널",
            "channel_id": "C01234ABCDE"
        },
        {
            "name": "QA 알림 채널",
            "channel_id": "C56789FGHIJ"
        },
        {
            "name": "개발팀 비공개 채널",
            "channel_id": "G12345KLMNO"
        }
    ]
}
```

### 스케줄 데이터 (schedule.json)

```json
{
    "id": "schedule_001",
    "name": "매일 빌드 알림",
    "slack_enabled": true,
    "bot_token": "xoxb-YOUR-BOT-TOKEN-HERE",
    "bot_token_name": "QA팀 Bot",
    "channel_id": "C01234ABCDE",
    "channel_id_name": "빌드 공지 채널",
    "notification_type": "standalone",
    "first_message": "yymmdd 빌드 완료"
}
```

## 채널 ID 찾는 방법

### 공개 채널
1. Slack에서 채널 클릭
2. 오른쪽 상단 **⋮** (더보기) 메뉴 클릭
3. **"채널 세부정보 보기"** 선택
4. 하단 "정보" 섹션에서 **채널 ID** 복사
5. 형식: `C`로 시작 (예: C01234ABCDE)

### 비공개 채널
1. 위와 동일한 방법
2. 형식: `G`로 시작 (예: G12345KLMNO)

### DM (Direct Message)
1. DM 창에서 동일한 방법
2. 형식: `D`로 시작 (예: D67890PQRST)
3. **참고**: DM은 권장하지 않음

## Bot Token 발급 방법

1. **Slack App 생성**
   - https://api.slack.com/apps 접속
   - "Create New App" 클릭
   - "From scratch" 선택
   - App 이름과 워크스페이스 선택

2. **Bot Token 발급**
   - "OAuth & Permissions" 메뉴 이동
   - "Scopes" 섹션에서 Bot Token Scopes 추가:
     - `chat:write` (메시지 전송)
     - `channels:history` (공개 채널 메시지 읽기)
     - `groups:history` (비공개 채널 메시지 읽기)
     - `channels:read` (채널 정보 읽기)
  - 상단 "Install to Workspace" 버튼 클릭
  - "Bot User OAuth Token" 복사 (xoxb- 형식으로 시작)

3. **채널에 Bot 추가**
   - Slack 채널에서 `/invite @봇이름` 입력
   - 또는 채널 설정 → 통합 → 앱 추가

## 주의사항

### 보안
- `slack_tokens.json` 파일은 민감한 정보를 포함합니다
- Git에 커밋하지 마세요 (.gitignore에 추가 권장)
- 토큰이 노출되면 즉시 재발급하세요

### 토큰 관리
- 같은 이름으로 중복 추가 불가
- 삭제 기능은 JSON 파일을 직접 편집하여 사용
- 토큰 또는 채널 삭제 시 기존 스케줄에 영향 없음 (코드 값 유지)

### 호환성
- 이전 버전에서 직접 입력한 토큰/채널 ID도 계속 작동
- 기존 스케줄을 편집하면 이름 없이 코드만 표시됨
- 드롭다운에서 선택하면 이름이 자동으로 저장됨

## 문제 해결

### 토큰이 드롭다운에 안 나타남
- `slack_tokens.json` 파일 확인
- JSON 형식이 올바른지 검증
- 애플리케이션 재시작

### 채널 ID가 작동하지 않음
- 채널 ID 형식 확인 (C, G, D로 시작)
- Bot이 해당 채널에 추가되었는지 확인
- Bot Token의 권한 확인

### 저장한 이름이 사라짐
- `slack_tokens.json` 파일이 삭제되었는지 확인
- 파일 권한 확인
- 백업 파일 복원

## 예시 워크플로우

### 1. 처음 설정하는 경우

1. Slack Bot Token 발급 (위 방법 참고)
2. QuickBuild 실행
3. 스케줄 생성/편집 클릭
4. "슬랙 알림 사용" 체크
5. Bot Token "+" 버튼 클릭
   - 이름: "QA팀 Bot"
   - 토큰: (실제 Bot Token 입력)
6. 채널 ID "+" 버튼 클릭
   - 이름: "빌드 공지 채널"
   - 채널 ID: C01234ABCDE
7. 스케줄 저장

### 2. 기존 토큰/채널 재사용

1. 스케줄 생성/편집 클릭
2. "슬랙 알림 사용" 체크
3. Bot Token 드롭다운에서 "QA팀 Bot" 선택
4. 채널 ID 드롭다운에서 "빌드 공지 채널" 선택
5. 스케줄 저장

### 3. 여러 채널에 동시 알림

같은 Bot Token으로 여러 스케줄을 만들고 각각 다른 채널을 선택하면 됩니다.

## 참고 자료

- [Slack API 공식 문서](https://api.slack.com/)
- [Bot Token 권한 가이드](https://api.slack.com/scopes)
- [채널 ID 찾기](https://www.wikihow.com/Find-a-Channel-ID-on-Slack-on-PC-or-Mac)
- `docs/SLACK_NOTIFICATION_GUIDE.md` - 슬랙 알림 기본 가이드

## 변경 이력

- **v3.1**: 초기 토큰/채널 관리 기능 추가
- 이름 기반 저장 및 드롭다운 선택 지원
- 즉시 추가 기능 ("+" 버튼)

