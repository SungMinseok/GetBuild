import requests
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

# GitHub 정보 설정
GITHUB_TOKEN = os.getenv("token")
REPO_OWNER = "SungMinseok"
REPO_NAME = "GetBuild"
RELEASE_TAG = "v1.0.0"
FILE_PATH = "QuickBuild.zip"

def show_popup(title, message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning(title, message)

def run_git_command(args):
    try:
        result = subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        show_popup("Git 오류", f"명령 실패: {' '.join(args)}\n\n{e.stderr}")
        sys.exit(1)

def check_clean_working_directory():
    result = run_git_command(["git", "status", "--porcelain"])
    return len(result.strip()) == 0

def get_release_id():
    """릴리즈 ID를 가져옵니다."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/{RELEASE_TAG}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        release_data = response.json()
        return release_data["id"]
    else:
        print(f"[ERROR] Failed to fetch release ID: {response.status_code} - {response.text}")
        return None

def upload_file_to_release(release_id):
    """릴리즈에 파일을 업로드합니다."""
    url = f"https://uploads.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/{release_id}/assets?name={os.path.basename(FILE_PATH)}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/zip"
    }

    with open(FILE_PATH, "rb") as file:
        response = requests.post(url, headers=headers, data=file)

    if response.status_code == 201:
        print("[INFO] File uploaded successfully!")
    else:
        print(f"[ERROR] Failed to upload file: {response.status_code} - {response.text}")

def main():
    if not os.path.exists(FILE_PATH):
        print(f"[ERROR] File '{FILE_PATH}' does not exist.")
        return

    if not check_clean_working_directory():
        show_popup("업로드 취소됨", "로컬에 커밋되지 않은 변경사항이 존재합니다.\n업로드를 중단합니다.")
        return

    print("[INFO] Fetching release ID...")
    release_id = get_release_id()

    if release_id:
        print(f"[INFO] Release ID: {release_id}")
        print("[INFO] Uploading file to release...")
        upload_file_to_release(release_id)

if __name__ == "__main__":
    main()
