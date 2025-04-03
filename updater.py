import os
import sys
import requests
import zipfile
import time
import subprocess
import shutil
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import traceback

# ───── 설정 ─────

# ───── 자기복제 설정 (RatUpdater 스타일) ─────
SELF_NAME = os.path.basename(sys.argv[0])
IS_TEMP = "_temp" in SELF_NAME.lower()
TEMP_NAME = SELF_NAME.replace(".exe", "_temp.exe") if SELF_NAME.endswith(".exe") else "updater_temp.exe"

def relaunch_as_temp():
    if not os.path.exists(TEMP_NAME):
        shutil.copy2(SELF_NAME, TEMP_NAME)
    subprocess.Popen([TEMP_NAME, "--run-temp"] + sys.argv[1:])
    sys.exit()

def delete_self():
    bat = "_self_delete.bat"
    with open(bat, "w") as f:
        f.write("@echo off\n")
        f.write("ping 127.0.0.1 -n 2 >nul\n")
        f.write("del \"{}\"\n".format(SELF_NAME))
        f.write("del \"%~f0\"\n")
    subprocess.Popen([bat], shell=True)

VERSION_FILE = "version.txt"
APP_NAME = "QuickBuild.exe"
ZIP_URL = "https://github.com/SungMinseok/GetBuild/releases/latest/download/QuickBuild.zip"
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/SungMinseok/GetBuild/main/version.txt"
TEMP_DIR = "update_temp"

# ───── 유틸 ─────
def is_silent_mode():
    return "--silent" in sys.argv

def show_message(title, message):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo(title, message)
    root.destroy()

def ask_yes_no(title, message):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    result = messagebox.askyesno(title, message)
    root.destroy()
    return result

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
        if not is_silent_mode():
            show_message("업데이트 실패", f"원격 버전 정보를 불러오는 데 실패했습니다:\n{e}")
        return None

def parse_version_date(version_str):
    try:
        parts = version_str.split("-")
        if len(parts) != 3:
            return None
        date_str = parts[1]
        time_str = parts[2]
        return datetime.strptime(f"{date_str}-{time_str}", "%Y.%m.%d-%H%M")
    except Exception:
        return None

def is_remote_newer(local_version, remote_version):
    local_dt = parse_version_date(local_version)
    remote_dt = parse_version_date(remote_version)
    if not local_dt or not remote_dt:
        return False
    return remote_dt > local_dt

# ───── 업데이트 로직 ─────
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
        if not is_silent_mode():
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
            if file.lower() == SELF_NAME.lower() or file.lower() == "updater.py":
                print(f"[SKIP] 보호된 파일 제외: {file}")
                continue
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, TEMP_DIR)
            dst_path = os.path.join(".", rel_path)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            try:
                shutil.copy2(src_path, dst_path)
            except PermissionError:
                print(f"[SKIP] 사용 중인 파일 복사 실패: {dst_path}")

def run_app():
    subprocess.Popen([APP_NAME], shell=True)

def clean_up():
    zip_path = os.path.join("QuickBuild.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

# ───── 메인 진입점 ─────
def main():
    try:
        quickbuild_exists = os.path.exists(APP_NAME)
        local_version = get_local_version() if quickbuild_exists else None
        remote_version = get_remote_version()

        if not remote_version:
            return

        if not quickbuild_exists:
            relaunch_as_temp()
            zip_path = download_zip()
            if not zip_path: return
            extract_zip(zip_path)
            replace_files()
            clean_up()
            show_message("설치 완료", "QuickBuild가 성공적으로 설치되었습니다.")
            return

        if not is_remote_newer(local_version, remote_version):
            if not is_silent_mode():
                show_message(
                    "업데이트 불필요",
                    f"이미 최신 버전입니다.\n\n현재 버전: {local_version}\n최신 버전: {remote_version}"
                )
            return

        if not is_silent_mode():
            do_update = ask_yes_no(
                "업데이트 확인",
                f"현재 버전: {local_version}\n최신 버전: {remote_version}\n\n업데이트 하시겠습니까?"
            )
            if not do_update:
                return

        relaunch_as_temp()
        zip_path = download_zip()
        if not zip_path: return
        extract_zip(zip_path)
        kill_app()
        replace_files()

        orig_name = SELF_NAME.replace("_temp", "")
        try:
            if os.path.exists(orig_name):
                os.remove(orig_name)
            shutil.copy2(SELF_NAME, orig_name)
            print(f"[INFO] 본체 덮어쓰기 완료: {orig_name}")
        except Exception as e:
            print(f"[WARN] 본체 덮어쓰기 실패: {e}")

        clean_up()
        show_message("업데이트 완료", "QuickBuild가 최신 버전으로 업데이트되었습니다.")
        run_app()

        if IS_TEMP:
            delete_self()

    except Exception as e:
        print("🔥 [업데이트 중 에러 발생]")
        print(traceback.format_exc())
        os.system("pause")

if __name__ == "__main__":
    # if "--run-temp" not in sys.argv:
    #     relaunch_as_temp()
    # else:
    main()
