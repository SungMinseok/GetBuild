@echo off
chcp 65001 > nul
echo ========================================
echo QuickBuild 클린 환경 설정
echo ========================================
echo.

echo [경고] 이 스크립트는 가상환경의 패키지를 정리합니다.
echo.
pause

REM 가상환경 활성화
echo [1/4] 가상환경 활성화...
set VENV1=C:\pyenvs\getbuild\Scripts\activate.bat
call "%VENV1%"
echo.

REM 이전 requirements 백업
echo [2/4] 이전 requirements.txt 백업...
if exist requirements.txt.old del requirements.txt.old
if exist requirements_old.txt (
    copy requirements_old.txt requirements.txt.old
    echo [OK] 백업 완료: requirements.txt.old
)
echo.

REM 필수 패키지만 재설치
echo [3/4] 필수 패키지 설치 중...
echo [INFO] 이전 패키지는 유지되며, 필수 패키지를 업데이트합니다.
echo.

pip install --upgrade pip
pip install -r requirements.txt --upgrade

echo.
echo [4/4] 설치된 패키지 확인...
echo.

echo Python 버전:
python --version
echo.

echo PyInstaller:
python -c "import PyInstaller; print('버전:', PyInstaller.__version__)"

echo PyQt5:
python -c "import PyQt5; print('버전:', PyQt5.Qt.PYQT_VERSION_STR)"

echo Selenium:
python -c "import selenium; print('버전:', selenium.__version__)"

echo.
echo ========================================
echo [SUCCESS] 설정 완료!
echo ========================================
echo.
echo 이제 quick_build.bat을 실행하세요.
echo.
pause



