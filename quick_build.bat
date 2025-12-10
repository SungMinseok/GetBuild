@echo off
chcp 65001 > nul
echo ========================================
echo QuickBuild 빠른 빌드 스크립트
echo ========================================
echo.

echo [1/3] 가상환경 진입...
set VENV1=.venv\Scripts\activate.bat
call "%VENV1%"
if %errorlevel% neq 0 (
    echo [ERROR] 가상환경을 찾을 수 없습니다: %VENV1%
    pause
    exit /b 1
)
echo [OK] 가상환경 활성화 완료
echo.

echo [2/4] 필수 패키지 확인...
python -c "import PyInstaller; print('PyInstaller:', PyInstaller.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] PyInstaller가 설치되어 있지 않습니다.
    echo [INFO] 필수 패키지 설치 중...
    pip install pyinstaller
)
echo [OK] 필수 패키지 확인 완료
echo.

echo [3/4] 이전 빌드 파일 정리...
REM 실행 중인 QuickBuild.exe 프로세스 종료
taskkill /F /IM QuickBuild.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM build 폴더 강제 삭제
if exist "build" (
    echo [INFO] build 폴더 삭제 중...
    rmdir /S /Q "build" 2>nul
    if exist "build" (
        echo [WARN] build 폴더를 삭제할 수 없습니다. 재시도 중...
        timeout /t 2 /nobreak >nul
        rmdir /S /Q "build" 2>nul
    )
)

REM dist 폴더 내 QuickBuild.exe만 삭제
if exist "dist\QuickBuild.exe" (
    echo [INFO] 기존 EXE 파일 삭제 중...
    del /F /Q "dist\QuickBuild.exe" 2>nul
)

echo [OK] 정리 완료
echo.

echo [4/4] EXE 빌드 생성...
echo.

REM 버전 정보 로드
for /f "tokens=2 delims=:" %%a in ('python -c "import json; f=open('version.json', encoding='utf-8'); v=json.load(f); print(v['version'])" 2^>nul') do set VERSION=%%a
if not defined VERSION set VERSION=3.0.0

echo 빌드 버전: %VERSION%
echo.

REM PyInstaller 실행 (간단 버전)
REM --clean 옵션 제거 (수동으로 정리했으므로)
python -m PyInstaller ^
    --name=QuickBuild ^
    --onefile ^
    --noconsole ^
    --icon=ico.ico ^
    --add-data "version.json;." ^
    --hidden-import=selenium ^
    --hidden-import=selenium.webdriver ^
    --hidden-import=selenium.webdriver.chrome ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=core ^
    --hidden-import=core.config_manager ^
    --hidden-import=core.scheduler ^
    --hidden-import=core.build_operations ^
    --hidden-import=core.aws_manager ^
    --hidden-import=core.worker_thread ^
    --hidden-import=ui ^
    --hidden-import=ui.schedule_dialog ^
    --hidden-import=ui.schedule_item_widget ^
    --hidden-import=ui.settings_dialog ^
    --hidden-import=updater ^
    --hidden-import=packaging ^
    --hidden-import=packaging.version ^
    --noconfirm ^
    index.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [SUCCESS] 빌드 완료!
    echo ========================================
    echo.
    echo 생성된 파일: dist\QuickBuild.exe
    if exist "dist\QuickBuild.exe" (
        for %%A in ("dist\QuickBuild.exe") do echo 파일 크기: %%~zA bytes
    )
) else (
    echo.
    echo ========================================
    echo [FAILED] 빌드 실패
    echo ========================================
)

echo.
pause



