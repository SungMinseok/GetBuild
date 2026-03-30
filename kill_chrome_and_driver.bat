@echo off
chcp 65001 > nul
echo [Chrome/ChromeDriver 강제 종료]
echo.

echo Chrome 프로세스 종료 중...
taskkill /F /IM chrome.exe /T 2>nul
if %errorlevel% equ 0 (
    echo   - Chrome 프로세스 종료 완료
) else (
    echo   - 실행 중인 Chrome 프로세스 없음
)

echo ChromeDriver 프로세스 종료 중...
taskkill /F /IM chromedriver.exe /T 2>nul
if %errorlevel% equ 0 (
    echo   - ChromeDriver 프로세스 종료 완료
) else (
    echo   - 실행 중인 ChromeDriver 프로세스 없음
)

echo.
echo 정리 완료.
pause
