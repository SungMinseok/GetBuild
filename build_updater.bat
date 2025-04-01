@echo off
REM Set the Python environment path
call C:\myvenv\getbuild\Scripts\activate.bat

REM Set the PyInstaller command with options
start /wait pyinstaller --upx-dir C:\upx-4.2.4-win64 -F -w -i ico.ico --name QuickBuild_Updater updater.py

REM Pause to see the output if running manually
pause