@echo off
chcp 65001 > nul
echo ========================================
echo QuickBuild 빠른 빌드 스크립트
echo ========================================
echo.

echo [0/6] Activate virtual environment...
echo.

set VENV1=C:\pyenvs\getbuild_clean\Scripts\activate.bat
call "%VENV1%"
echo.

echo [1/4] Python 환경 확인...
python --version
echo.

echo [2/4] 필수 패키지 확인...
python -c "import PyInstaller; print('PyInstaller:', PyInstaller.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] PyInstaller가 설치되어 있지 않습니다.
    echo [INFO] 패키지 설치 중...
    pip install -r requirements.txt
)
echo.

echo [3/4] 이전 빌드 정리...
if exist "dist" rd /s /q "dist" 2>nul
if exist "build" rd /s /q "build" 2>nul
echo [OK] 정리 완료
echo.

echo [4/4] 빌드 시작...
python build_release.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [SUCCESS] 빌드 완료!
    echo ========================================
    echo.
    if exist "dist\*.zip" (
        echo 생성된 파일:
        dir /b "dist\*.zip"
    )
) else (
    echo.
    echo ========================================
    echo [FAILED] 빌드 실패
    echo ========================================
    echo.
    echo 빌드_가이드.md 파일을 참고하세요.
)

echo.
pause



