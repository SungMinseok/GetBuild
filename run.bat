@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 가상환경 활성화 (.venv 우선, 없으면 pyenvs)
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else if exist "C:\pyenvs\getbuild\Scripts\activate.bat" (
    call "C:\pyenvs\getbuild\Scripts\activate.bat"
) else (
    echo [오류] 가상환경을 찾을 수 없습니다.
    echo .venv 또는 C:\pyenvs\getbuild 중 하나를 생성해 주세요.
    pause
    exit /b 1
)

python index.py
if errorlevel 1 pause
