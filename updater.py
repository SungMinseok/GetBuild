import os
import requests
import zipfile
import time
import subprocess
import shutil
import tkinter as tk
from tkinter import messagebox

# 설정
VERSION_FILE = "version.txt"
APP_NAME = "QuickBuild.exe"
ZIP_URL = "https://github.com/SungMinseok/GetBuild/releases/latest/download/QuickBuild.zip"
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/SungMinseok/GetBuild/main/version.txt"
TEMP_DIR = "update_temp"

# 메시지 박스 초기화용
def show_message(title, message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, message)

def get_local_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return None

def get_remote_version():
    try:
        r = requests.get(REMOTE_VERSION_URL, timeout=5)
        return r.text.strip()
    except Exception as e:
        show_message("업데이트 실패", f"원격 버전 정보를 불러오는 데 실패했습니다:\n{e}")
        return None

def download_zip():
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        zip_path = os.path.join(TEMP_DIR, "QuickBuild.zip")
        with requests.get(ZIP_URL, stream=True) as r:
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return zip_path
    except Exception as e:
        show_message("다운로드 실패", f"업데이트 파일 다운로드 중 오류 발생:\n{e}")
        return None

def extract_zip(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(TEMP_DIR)

def kill_app():
    try:
        subprocess.call(["taskkill", "/f", "/im", APP_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass

def replace_files():
    for root, dirs, files in os.walk(TEMP_DIR):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, TEMP_DIR)
            dst_path = os.path.join(".", rel_path)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)

def run_app():
    subprocess.Popen([APP_NAME], shell=True)

def clean_up():
    zip_path = os.path.join("QuickBuild.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

def main():
    quickbuild_exists = os.path.exists(APP_NAME)
    local_version = get_local_version() if quickbuild_exists else None
    remote_version = get_remote_version()

    if not remote_version:
        return  # 오류 메시지는 위에서 이미 출력됨

    if not quickbuild_exists:
        # 최초 설치
        zip_path = download_zip()
        if not zip_path: return
        extract_zip(zip_path)
        replace_files()
        clean_up()
        show_message("설치 완료", "QuickBuild가 성공적으로 설치되었습니다.")
        run_app()
        return

    if local_version == remote_version:
        show_message("업데이트 불필요", "이미 최신 버전입니다.")
        return

    # 업데이트
    zip_path = download_zip()
    if not zip_path: return
    extract_zip(zip_path)
    kill_app()
    replace_files()
    clean_up()
    show_message("업데이트 완료", "QuickBuild가 최신 버전으로 업데이트되었습니다.")
    run_app()

if __name__ == "__main__":
    main()
