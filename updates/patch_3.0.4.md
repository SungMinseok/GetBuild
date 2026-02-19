# QuickBuild v3.0.4 패치노트

**버전**: 3.0.4
**빌드 날짜**: 2026-02-13

---

## 주요 변경사항

### 1. 코드 정리 및 구조 개선
- 불필요한 파일 30개+ 삭제 (build.py, deploy_local.py, 피드백 시스템, 테스트 파일, 설정 예제, 문서 등)
- 빌드/배포 스크립트 경로를 `scripts/` 폴더로 이동 (build.py, deploy_local.py, update_version.py, build_release.py)
- 피드백 기능 비활성화 처리 (임포트 실패 시 안전하게 None 처리)

### 2. ChromeDriver 자동 관리
- 시스템 Chrome 버전 자동 감지
- Chrome과 ChromeDriver 메이저 버전 호환성 자동 확인
- 호환되지 않을 경우 올바른 버전 자동 다운로드/업데이트
- 구버전 ChromeDriver 자동 정리 기능

### 3. 서버업로드및패치 - 패치 대기시간 설정
- 업로드 완료 후 패치까지 대기 시간(분) 설정 가능 (0~120분, 기본 30분)
- 스케줄 다이얼로그에 패치 대기시간 SpinBox 추가 (서버업로드및패치 옵션에서만 활성화)
- 업로드 완료 시 1차 슬랙 알림 전송 (배포 요청 완료 + 패치 대기 안내)
- 대기 시간 동안 1분 간격으로 남은 시간 로그 출력

### 4. 슬랙 알림 개선
- **스레드 댓글(채널에도 전송)** 모드 추가 (`thread_broadcast`)
  - 스레드에 댓글을 달면서 채널에도 동시에 표시
  - Slack API `reply_broadcast` 옵션 활용
- 스케줄 다이얼로그에 알림 타입 라디오 버튼 추가 (단독 / 스레드 댓글 / 스레드 댓글+채널 전송)

### 5. 결과 파일 관리 개선
- CSV 결과 파일을 `result/` 폴더에 저장하도록 변경
- 폴더가 없으면 자동 생성

### 6. run.bat 개선
- 가상환경 자동 감지 (`.venv` 우선, `C:\pyenvs\getbuild` 대체)
- UTF-8 코드 페이지 설정
- 에러 발생 시 pause 추가

---

## 삭제된 파일 목록
- `build.py`, `build_release.py`, `deploy_local.py`, `git_release.py`, `update_version.py`
- `migrate_schedule.py`, `remove_schedule_from_git.py`
- `quick_build.bat`, `setup_env.bat`
- `ui/feedback_dialog.py`, `ui/feedback_dialog_v2.py`
- `test_env_feedback.py`, `test_feedback.py`, `test_slack_notification.py`, `test_slack_upload.py`
- `feedback_tokens.json.example`, `slack_tokens.json.example`, `token.json.example`, `hook.json.example`
- `requirements_251026.txt`, `requirements_old.txt`
- `temp_download/index_alpha.py`
- `SETUP_GUIDE_SIMPLE.md`, `SLACK_TOKEN_SETUP.md`
- `빌드_배포_시스템_구조_문서.md`, `앱_자동_업데이트_시스템_문서.md`
