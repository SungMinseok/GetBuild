@echo off
chcp 65001 > nul
echo ============================================================
echo Slack 환경 변수 설정
echo ============================================================
echo.
echo 관리자에게 다음 정보를 받으세요:
echo   - Slack Bot Token (xoxb-로 시작)
echo   - Slack Channel ID (C로 시작)
echo.

REM 사용자 입력 받기
set /p DEFAULT_SLACK_BOT_TOKEN="Slack Bot Token 입력: "
set /p DEFAULT_SLACK_CHANNEL_ID="Slack Channel ID 입력: "

echo.
echo [OK] 환경 변수가 설정되었습니다.
echo.
echo Bot Token: %DEFAULT_SLACK_BOT_TOKEN:~0,20%...
echo Channel ID: %DEFAULT_SLACK_CHANNEL_ID%
echo.
echo ============================================================
echo 이제 앱을 실행할 수 있습니다:
echo   python index.py
echo ============================================================
echo.
echo 참고: 이 설정은 현재 터미널 세션에만 적용됩니다.
echo 영구 설정을 원하면 시스템 환경 변수에 추가하세요.
echo.
pause

