@echo off
chcp 65001 >nul
echo ============================================================
echo QuickBuild 빠른 배포 스크립트
echo ============================================================
echo.
echo [0/3] Activate virtual environment...
echo.

set VENV1=C:\pyenvs\getbuild\Scripts\activate.bat
call "%VENV1%"
echo.
REM 1. 버전 업데이트
echo [1/3] 버전 업데이트 중...
set /p changelog="변경사항 메시지 입력 (엔터만 누르면 기본 메시지): "
if "%changelog%"=="" (
    python update_version.py
) else (
    python update_version.py "%changelog%"
)
if errorlevel 1 (
    echo 버전 업데이트 실패!
    pause
    exit /b 1
)
echo.

REM 2. 빌드
echo [2/3] 빌드 중...
python build_release.py
if errorlevel 1 (
    echo 빌드 실패!
    pause
    exit /b 1
)
echo.

REM 3. 배포
echo [3/3] GitHub Release 배포...
python deploy_github.py
if errorlevel 1 (
    echo 배포 실패!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✅ 모든 과정 완료!
echo ============================================================
pause

