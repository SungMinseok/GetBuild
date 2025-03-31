import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
import requests
import json

with open("config.json", "r") as f:
    config = json.load(f)

# 설정
GITHUB_TOKEN = config.get("token")
REPO_OWNER = "SungMinseok"
REPO_NAME = "GetBuild"
FILE_PATH = "QuickBuild.zip"

# ===== UI & Git =====
def show_popup(title, message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning(title, message)

def ask_release_type():
    root = tk.Tk()
    root.withdraw()
    return messagebox.askyesno(
        "릴리스 방식 선택",
        "새로운 버전으로 새 태그를 생성하시겠습니까?\n\n"
        "예 (Yes): version.txt 기반으로 새 릴리스 생성\n"
        "아니오 (No): 기존 릴리스 zip 삭제 후 덮어쓰기 (태그는 새로 생성)"
    )

def run_git_command(args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        show_popup("Git 오류", result.stderr)
        sys.exit(1)
    return result.stdout.strip()

def check_clean_working_directory():
    return run_git_command(["git", "status", "--porcelain"]).strip() == ""

def get_current_commit_sha():
    return run_git_command(["git", "rev-parse", "HEAD"])

def create_git_tag(tag_name):
    run_git_command(["git", "tag", tag_name])
    run_git_command(["git", "push", "origin", tag_name])

# ===== GitHub API =====
def get_latest_release():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    return res.json() if res.status_code == 200 else None

def delete_existing_asset(release_id, asset_name):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/{release_id}/assets"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        for asset in res.json():
            if asset["name"] == asset_name:
                delete_url = asset["url"]
                requests.delete(delete_url, headers={**headers, "Accept": "application/vnd.github.v3+json"})
                print(f"[INFO] 기존 asset '{asset_name}' 삭제 완료")
    else:
        print("[WARN] 릴리스 asset 정보를 가져오지 못했습니다.")

def create_release(tag, name, body="", draft=False, prerelease=False):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "tag_name": tag,
        "name": name,
        "body": body,
        "draft": draft,
        "prerelease": prerelease
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"[INFO] 새 릴리스 생성 성공: {tag}")
        return response.json()["id"]
    else:
        show_popup("릴리스 생성 실패", response.text)
        sys.exit(1)

def upload_file_to_release(release_id, file_path):
    url = f"https://uploads.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/{release_id}/assets?name={os.path.basename(file_path)}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/zip"
    }
    with open(file_path, "rb") as f:
        res = requests.post(url, headers=headers, data=f)
    if res.status_code == 201:
        print("[INFO] 파일 업로드 완료 ✅")
    else:
        show_popup("업로드 실패", res.text)
        sys.exit(1)

# ===== Main Logic =====
def main():
    if not os.path.exists(FILE_PATH):
        show_popup("에러", f"{FILE_PATH} 파일이 존재하지 않습니다.")
        return

    if not check_clean_working_directory():
        show_popup("업로드 취소됨", "로컬에 커밋되지 않은 변경사항이 존재합니다.\n업로드를 중단합니다.")
        return

    with open("version.txt", "r") as f:
        version = f.read().strip()

    is_full_release = ask_release_type()

    if is_full_release:
        # 새 릴리스 생성 (버전 기반 태그)
        create_git_tag(version)
        release_id = create_release(version, f"Release {version}")
        upload_file_to_release(release_id, FILE_PATH)
    else:
        # 기존 최신 릴리스에 asset 삭제 + 재업로드, 단 태그는 새로 생성
        latest = get_latest_release()
        if not latest:
            show_popup("에러", "최신 릴리스를 불러오지 못했습니다.")
            return

        release_id = latest["id"]
        delete_existing_asset(release_id, os.path.basename(FILE_PATH))
        upload_file_to_release(release_id, FILE_PATH)
        create_git_tag(version)

if __name__ == "__main__":
    main()
