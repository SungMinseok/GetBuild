"""
QuickBuild 로컬 빌드 배포 스크립트
PyInstaller로 빌드된 EXE를 ZIP으로 패키징하고 GitHub Release로 업로드합니다.
"""

import os
import sys
import json
import zipfile
import requests
from pathlib import Path
from datetime import datetime


def load_version_info():
    """version.json에서 버전 정보 로드"""
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ version.json 파일이 없습니다!")
        return None
    except Exception as e:
        print(f"❌ version.json 로드 실패: {e}")
        return None


def load_token_data():
    """token.json에서 토큰 및 Webhook 정보 로드"""
    try:
        with open('token.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ token.json 파일이 없습니다!")
        print("\n📝 token.json 파일을 생성하세요:")
        print('{')
        print('  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx",')
        print('  "webhook_team1": "https://hooks.slack.com/services/..."')
        print('}')
        return None
    except Exception as e:
        print(f"❌ token.json 로드 실패: {e}")
        return None


def verify_github_token(token):
    """GitHub 토큰 유효성 검증"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # 사용자 정보로 토큰 검증
        response = requests.get("https://api.github.com/user", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            username = user_data.get('login', 'Unknown')
            print(f"  ✅ 토큰 인증 성공: @{username}")
            
            # 권한 확인
            scopes = response.headers.get('X-OAuth-Scopes', '')
            print(f"  권한: {scopes if scopes else '(확인 불가)'}")
            
            if 'repo' not in scopes and scopes:
                print(f"  ⚠️  경고: 'repo' 권한이 없을 수 있습니다.")
            
            return True
        elif response.status_code == 401:
            print(f"  ❌ 토큰 인증 실패: 유효하지 않거나 만료된 토큰")
            print(f"  응답: {response.json().get('message', 'Unknown error')}")
            return False
        else:
            print(f"  ⚠️  토큰 검증 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠️  토큰 검증 중 오류: {e}")
        return False


def get_github_token():
    """GitHub 토큰 가져오기"""
    # 방법 1: token.json 파일에서 읽기
    token_data = load_token_data()
    if token_data and "github_token" in token_data:
        token = token_data["github_token"].strip()
        return token
    
    # 방법 2: 환경변수에서 읽기
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip()
    
    print("❌ GitHub 토큰을 찾을 수 없습니다.")
    print("\n📝 다음 중 하나를 수행하세요:")
    print("  1. token.json 파일에 'github_token' 추가")
    print("  2. 환경변수 GITHUB_TOKEN 설정")
    print("\n🔑 GitHub 토큰 생성 방법:")
    print("  1. GitHub → Settings → Developer settings")
    print("  2. Personal access tokens → Tokens (classic)")
    print("  3. Generate new token")
    print("  4. 권한 선택: repo (전체)")
    print("  5. 토큰 복사 후 token.json에 저장")
    return None


def create_zip_package():
    """빌드된 EXE와 version.json을 ZIP으로 패키징"""
    print("\n[1/4] ZIP 패키지 생성 중...")
    
    dist_dir = Path("dist")
    exe_file = dist_dir / "QuickBuild.exe"
    version_json_path = Path('version.json')
    zip_path = dist_dir / "QuickBuild.zip"
    
    # 파일 존재 확인
    if not exe_file.exists():
        print(f"❌ EXE 파일을 찾을 수 없습니다: {exe_file}")
        return None
    
    if not version_json_path.exists():
        print(f"❌ version.json 파일을 찾을 수 없습니다")
        return None
    
    # 기존 ZIP 삭제
    if zip_path.exists():
        zip_path.unlink()
        print(f"  기존 ZIP 파일 삭제: {zip_path}")
    
    # ZIP 생성
    print(f"  압축 중: {exe_file.name}")
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(exe_file, 'QuickBuild.exe')
        zipf.write(version_json_path, 'version.json')
    
    # 파일 크기 확인
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"✅ ZIP 패키지 생성 완료: {zip_path} ({zip_size_mb:.2f} MB)")
    return zip_path


def create_changelog_file(version_info):
    """changelog.txt 파일 생성 및 편집"""
    changelog_file_path = "changelog.txt"
    version = version_info.get('version', 'Unknown')
    build_date = version_info.get('build_date', datetime.now().strftime("%Y-%m-%d"))
    
    # 최신 changelog 가져오기
    changelogs = version_info.get('changelog', [])
    latest_changes = []
    if changelogs:
        latest_changes = changelogs[0].get('changes', [])
    
    # changelog.txt 생성 또는 업데이트
    content = f"# QuickBuild {version} 릴리즈 노트\n\n"
    content += f"**빌드 날짜**: {build_date}\n\n"
    content += "## 변경사항\n\n"
    
    if latest_changes:
        for change in latest_changes:
            content += f"- {change}\n"
    else:
        content += "- 버그 수정 및 성능 개선\n"
    
    content += "\n---\n\n"
    content += "**자동 업데이트 지원**: QuickBuild를 실행하면 자동으로 새 버전을 확인합니다.\n"
    
    with open(changelog_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n📝 changelog.txt 파일이 생성되었습니다.")
    print(f"  내용을 확인하고 수정하려면 파일을 열어주세요.")
    
    # 파일 자동 열기 (Windows)
    try:
        os.startfile(changelog_file_path)
        print(f"  📄 {changelog_file_path} 파일을 열었습니다.")
    except:
        print(f"  ℹ️  수동으로 {changelog_file_path} 파일을 열어 편집하세요.")
    
    input("\n👉 편집 완료 후 엔터를 누르세요...")
    
    # 파일 내용 읽기
    with open(changelog_file_path, 'r', encoding='utf-8') as f:
        changelog_content = f.read().strip()
    
    return changelog_content


def create_github_release(version, changelog_content, token, zip_path):
    """GitHub 릴리즈 생성 및 파일 업로드"""
    print("\n[2/4] GitHub 릴리즈 생성 중...")
    
    repo_owner = "SungMinseok"
    repo_name = "GetBuild"
    tag_name = f"v{version}"
    
    print(f"  저장소: {repo_owner}/{repo_name}")
    print(f"  태그: {tag_name}")
    
    # Release 데이터 구성
    release_data = {
        "tag_name": tag_name,
        "target_commitish": "main",
        "name": f"QuickBuild {version}",
        "body": changelog_content,
        "draft": False,
        "prerelease": False
    }
    
    # GitHub API 호출 (Release 생성)
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    
    print(f"  API 호출: {url}")
    response = requests.post(url, json=release_data, headers=headers)
    
    if response.status_code != 201:
        print(f"❌ 릴리즈 생성 실패: {response.status_code}")
        print(f"  응답: {response.text}")
        return False
    
    release_id = response.json()['id']
    release_url = response.json()['html_url']
    print(f"✅ 릴리즈 생성 완료 (ID: {release_id})")
    print(f"  URL: {release_url}")
    
    # ZIP 파일 업로드
    print("\n[3/4] ZIP 파일 업로드 중...")
    upload_url = f"https://uploads.github.com/repos/{repo_owner}/{repo_name}/releases/{release_id}/assets"
    
    with open(zip_path, 'rb') as f:
        upload_headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/zip"
        }
        params = {"name": zip_path.name}
        
        print(f"  업로드: {zip_path.name} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
        response = requests.post(
            upload_url, 
            headers=upload_headers, 
            params=params, 
            data=f
        )
    
    if response.status_code != 201:
        print(f"❌ 파일 업로드 실패: {response.status_code}")
        print(f"  응답: {response.text}")
        return False
    
    download_url = response.json()['browser_download_url']
    print(f"✅ 파일 업로드 완료")
    print(f"  다운로드 URL: {download_url}")
    
    return True


def send_slack_notification(version, changelog, webhook_url):
    """Slack Webhook으로 릴리즈 알림 전송"""
    # changelog에서 첫 줄만 추출 (요약용)
    changelog_lines = changelog.split('\n')
    changelog_summary = next((line for line in changelog_lines if line.strip() and not line.startswith('#')), "업데이트")
    
    message = {
        "text": f":rocket: *QuickBuild {version}* 업데이트",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*QuickBuild {version}* 새 버전이 릴리즈되었습니다!"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• 업데이트 방법: QuickBuild 재실행 시 자동 확인\n• {changelog_summary}"
                }
            }
        ]
    }
    
    response = requests.post(webhook_url, json=message)
    
    if response.status_code == 200:
        print("✅ Slack 알림 전송 성공")
        return True
    else:
        print(f"⚠️ Slack 알림 실패: {response.status_code}")
        return False


def choose_webhook(webhooks: dict):
    """여러 Webhook 중 선택"""
    keys = list(webhooks.keys())
    
    print("\n🔔 Slack 알림을 보내시겠습니까?")
    print("  0. 건너뛰기")
    for i, k in enumerate(keys, 1):
        print(f"  {i}. {k}")
    
    while True:
        try:
            choice = input("\n번호 입력 (0-{}): ".format(len(keys))).strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                return None
            elif 1 <= choice_num <= len(keys):
                selected_key = keys[choice_num - 1]
                return webhooks[selected_key]
            else:
                print("⚠️ 잘못된 번호입니다.")
        except ValueError:
            print("⚠️ 숫자를 입력해주세요.")
        except KeyboardInterrupt:
            print("\n알림 전송 취소")
            return None


def cleanup_files(zip_path):
    """임시 파일 정리"""
    print("\n[4/4] 임시 파일 정리 중...")
    
    # changelog.txt는 유지 (다음 배포 시 참고용)
    files_to_keep = ['changelog.txt']
    
    # ZIP 파일은 유지 (배포 완료 후에도 보관)
    print(f"  ZIP 파일 유지: {zip_path}")
    print(f"  changelog.txt 유지")
    
    print("✅ 정리 완료")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("QuickBuild 로컬 빌드 배포 스크립트")
    print("=" * 60)
    
    # 1. 버전 정보 로드
    version_info = load_version_info()
    if not version_info:
        return 1
    
    version = version_info.get("version", "Unknown")
    build_date = version_info.get("build_date", "Unknown")
    
    print(f"\n📦 배포 정보:")
    print(f"  버전: {version}")
    print(f"  빌드 날짜: {build_date}")
    
    # 최신 changelog 표시
    changelogs = version_info.get('changelog', [])
    if changelogs:
        latest_changes = changelogs[0].get('changes', [])
        print(f"  변경사항:")
        for change in latest_changes:
            print(f"    - {change}")
    
    # 2. ZIP 패키지 생성
    zip_path = create_zip_package()
    if not zip_path:
        print("\n❌ ZIP 패키지 생성 실패!")
        return 1
    
    # 3. Changelog 파일 생성 및 편집
    changelog_content = create_changelog_file(version_info)
    
    # 4. 배포 확인
    print("\n" + "=" * 60)
    print(f"🚀 QuickBuild {version} 릴리즈를 GitHub에 배포하시겠습니까?")
    print("=" * 60)
    response = input("계속하려면 'y'를 입력하세요 (y/N): ").lower().strip()
    
    if response != 'y':
        print("\n배포 취소됨")
        cleanup_files(zip_path)
        return 0
    
    # 5. GitHub 토큰 가져오기 및 검증
    print("\n🔐 GitHub 토큰 확인 중...")
    token = get_github_token()
    if not token:
        return 1
    
    # 토큰 유효성 검증
    if not verify_github_token(token):
        print("\n❌ GitHub 토큰이 유효하지 않습니다.")
        print("\n📝 해결 방법:")
        print("  1. GitHub에서 새 토큰 생성")
        print("  2. token.json 파일의 'github_token' 값 업데이트")
        print("  3. 토큰 권한에 'repo' 포함 확인")
        return 1
    
    # 6. Slack Webhook 로드 (선택사항)
    token_data = load_token_data()
    webhooks = {}
    if token_data:
        webhooks = {k: v for k, v in token_data.items() 
                    if k.startswith("webhook_")}
    
    try:
        # 7. GitHub Release 생성 및 업로드
        if not create_github_release(version, changelog_content, token, zip_path):
            print("\n❌ GitHub 릴리즈 생성 실패!")
            return 1
        
        # 8. 성공 메시지
        print("\n" + "=" * 60)
        print("✅ GitHub 릴리즈 배포 완료!")
        print("=" * 60)
        print(f"버전: {version}")
        print(f"릴리즈 URL: https://github.com/SungMinseok/GetBuild/releases/tag/v{version}")
        print(f"ZIP 파일: {zip_path}")
        print("=" * 60)
        
        # 9. Slack 알림 (선택사항)
        if webhooks:
            webhook_url = choose_webhook(webhooks)
            if webhook_url:
                send_slack_notification(version, changelog_content, webhook_url)
        
        # 10. 임시 파일 정리
        cleanup_files(zip_path)
        
        print("\n✨ 배포가 완료되었습니다!")
        print("사용자는 QuickBuild를 재실행하면 자동으로 업데이트를 확인합니다.")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ 배포 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] 사용자가 배포를 취소했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 예기치 않은 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

