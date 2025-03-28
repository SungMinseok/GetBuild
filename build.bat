@echo off
setlocal ENABLEDELAYEDEXPANSION

REM === [1] 버전 구성 ===
set MAJOR_VERSION=1.0

REM 현재 날짜 및 시간 가져오기
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy.MM.dd-HHmm"') do set DATE_VER=%%i

REM 최종 버전 문자열 생성
set VERSION_STR=%MAJOR_VERSION%-%DATE_VER%

REM version.txt 생성
echo %VERSION_STR% > version.txt
echo [INFO] Generated version.txt with version: %VERSION_STR%

REM === [2] 가상환경 활성화 ===
call C:\myvenv\getbuild\Scripts\activate.bat

REM === [3] PyInstaller 실행 ===
start /wait pyinstaller --upx-dir C:\upx-4.2.4-win64 -F -w -i ico.ico --name QuickBuild index.py

REM === [4] 기존 zip 삭제 ===
if exist QuickBuild.zip del QuickBuild.zip

REM === [5] zip 생성 ===
echo [INFO] Creating new QuickBuild.zip file...

powershell Compress-Archive -Path dist\QuickBuild.exe, version.txt, ico.ico, qss -DestinationPath QuickBuild.zip

echo [INFO] Done. Final version: %VERSION_STR%
pause