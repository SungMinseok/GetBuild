# Slack 환경 변수 설정 (PowerShell)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Slack 환경 변수 설정" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "관리자에게 다음 정보를 받으세요:" -ForegroundColor Yellow
Write-Host "  - Slack Bot Token (xoxb-로 시작)" -ForegroundColor Gray
Write-Host "  - Slack Channel ID (C로 시작)" -ForegroundColor Gray
Write-Host ""

# 사용자 입력 받기
$botToken = Read-Host "Slack Bot Token 입력"
$channelId = Read-Host "Slack Channel ID 입력"

# 환경 변수 설정
$env:DEFAULT_SLACK_BOT_TOKEN = $botToken
$env:DEFAULT_SLACK_CHANNEL_ID = $channelId

Write-Host ""
Write-Host "[OK] 환경 변수가 설정되었습니다." -ForegroundColor Green
Write-Host ""
Write-Host "Bot Token: $($env:DEFAULT_SLACK_BOT_TOKEN.Substring(0,[Math]::Min(20, $env:DEFAULT_SLACK_BOT_TOKEN.Length)))..."
Write-Host "Channel ID: $env:DEFAULT_SLACK_CHANNEL_ID"
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "이제 앱을 실행할 수 있습니다:" -ForegroundColor Yellow
Write-Host "  python index.py" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "참고: 이 설정은 현재 PowerShell 세션에만 적용됩니다." -ForegroundColor Gray
Write-Host "영구 설정을 원하면 시스템 환경 변수에 추가하세요." -ForegroundColor Gray
Write-Host ""

