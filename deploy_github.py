"""
GitHub Release 자동 배포 스크립트
로컬에서 빌드된 QuickBuild.zip을 GitHub Release로 업로드합니다.
"""

import os
import sys
import json
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
        sys.exit(1)


def load_token():
    """token.json에서 GitHub 토큰 로드"""
    try:
        with open('token.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            token = data.get('github_token')
            if not token:
                print("❌ token.json에 'github_token' 키가 없습니다!")
                sys.exit(1)
            return data
    except FileNotFoundError:
        print("❌ token.json 파일이 없습니다!")
        print("\n📝 token.json 파일을 생성하세요:")
        print('{')
        print('  "github_token": "ghp_your_token_here"')
        print('}')
        sys.exit(1)


def find_zip_file(version):
    """빌드된 ZIP 파일 찾기"""
    dist_dir = Path('dist')
    
    # 버전 포함 파일명 먼저 찾기
    zip_with_version = dist_dir / f"QuickBuild_{version}.zip"
    if zip_with_version.exists():
        return zip_with_version
    
    # 일반 파일명 찾기
    zip_file = dist_dir / "QuickBuild.zip"
    if zip_file.exists():
        return zip_file
    
    # dist 폴더에서 QuickBuild로 시작하는 ZIP 찾기
    for file in dist_dir.glob("QuickBuild*.zip"):
        return file
    
    return None


def create_changelog_file(version_info):
    """changelog.txt 파일 생성"""
    version = version_info.get('version', 'Unknown')
    build_date = version_info.get('build_date', 'Unknown')
    
    # 최신 changelog 가져오기
    changelogs = version_info.get('changelog', [])
    latest_changes = []
    if changelogs:
        latest_changes = changelogs[0].get('changes', [])
    
    # changelog.txt 생성
    content = f"# QuickBuild {version} 릴리즈 노트\n\n"
    content += f"**빌드 날짜**: {build_date}\n\n"
    content += "## 변경사항\n\n"
    
    if latest_changes:
        for change in latest_changes:
            content += f"* {change}\n"
    else:
        content += "* 버그 수정 및 성능 개선\n"
    
    with open('changelog.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ changelog.txt 생성 완료")
    return content


def create_github_release(version, changelog, token, zip_path):
    """GitHub 릴리즈 생성 및 파일 업로드"""
    repo_owner = "SungMinseok"
    repo_name = "GetBuild"
    tag_name = f"v{version}"
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    print(f"\n📝 릴리즈 노트 작성 중...")
    
    # 1. changelog.txt 파일 열기 (있는 경우)
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    if Path('changelog.txt').exists():
        if not auto_confirm:
            try:
                os.startfile('changelog.txt')
                print("   changelog.txt 파일이 열렸습니다.")
            except:
                print("   changelog.txt 파일을 자동으로 열 수 없습니다.")
            
            input("\n👉 changelog.txt 편집 완료 후 엔터를 누르세요 (또는 그냥 엔터)...")
        else:
            print("   자동 진행 모드: changelog.txt 사용")
        
        # 파일 내용 읽기
        with open('changelog.txt', 'r', encoding='utf-8') as f:
            changelog_content = f.read().strip()
    else:
        changelog_content = changelog
    
    # 2. Release 데이터 구성
    release_data = {
        "tag_name": tag_name,
        "target_commitish": "main",
        "name": f"QuickBuild {version}",
        "body": changelog_content,
        "draft": False,
        "prerelease": False
    }
    
    print(f"\n🚀 GitHub Release 생성 중...")
    print(f"   저장소: {repo_owner}/{repo_name}")
    print(f"   태그: {tag_name}")
    
    # 3. GitHub API로 Release 생성
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    
    try:
        response = requests.post(url, json=release_data, headers=headers)
        
        if response.status_code == 201:
            release = response.json()
            release_id = release['id']
            release_url = release['html_url']
            print(f"✅ Release 생성 성공!")
            print(f"   URL: {release_url}")
        else:
            print(f"❌ Release 생성 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            
            # 409 Conflict: 이미 존재하는 릴리즈
            if response.status_code == 409:
                print("\n💡 동일한 버전의 Release가 이미 존재합니다.")
                print("   GitHub에서 기존 Release를 삭제하거나 새 버전으로 업데이트하세요.")
            
            return False
    
    except Exception as e:
        print(f"❌ Release 생성 오류: {e}")
        return False
    
    # 4. ZIP 파일 업로드
    print(f"\n📦 ZIP 파일 업로드 중...")
    print(f"   파일: {zip_path.name}")
    print(f"   크기: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    upload_url = f"https://uploads.github.com/repos/{repo_owner}/{repo_name}/releases/{release_id}/assets"
    
    try:
        with open(zip_path, 'rb') as f:
            upload_headers = headers.copy()
            upload_headers['Content-Type'] = 'application/zip'
            
            params = {'name': zip_path.name}
            response = requests.post(
                upload_url,
                headers=upload_headers,
                params=params,
                data=f
            )
            
            if response.status_code == 201:
                asset = response.json()
                download_url = asset['browser_download_url']
                print(f"✅ 파일 업로드 성공!")
                print(f"   다운로드 URL: {download_url}")
            else:
                print(f"❌ 파일 업로드 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                return False
    
    except Exception as e:
        print(f"❌ 파일 업로드 오류: {e}")
        return False
    
    return True


def send_slack_notification(version, changelog, webhook_url):
    """Slack Webhook으로 릴리즈 알림 전송"""
    if not webhook_url:
        return
    
    try:
        message = {
            "text": f":rocket: *QuickBuild {version}* 업데이트 배포 완료!\n\n"
                    f"• GitHub Release: https://github.com/SungMinseok/GetBuild/releases/tag/v{version}\n"
                    f"• 변경사항:\n{changelog}\n"
        }
        
        response = requests.post(webhook_url, json=message)
        
        if response.status_code == 200:
            print("✅ Slack 알림 전송 완료")
        else:
            print(f"⚠️ Slack 알림 전송 실패: {response.status_code}")
    
    except Exception as e:
        print(f"⚠️ Slack 알림 오류: {e}")


def main():
    """메인 배포 프로세스"""
    print("=" * 60)
    print("QuickBuild GitHub Release 배포")
    print("=" * 60)
    
    # 1. 버전 정보 로드
    version_info = load_version_info()
    version = version_info.get('version', 'Unknown')
    
    print(f"\n📌 배포 정보:")
    print(f"   버전: {version}")
    print(f"   날짜: {version_info.get('build_date', 'Unknown')}")
    
    # 2. ZIP 파일 확인
    zip_path = find_zip_file(version)
    
    if not zip_path:
        print(f"\n❌ dist/QuickBuild_{version}.zip 파일이 존재하지 않습니다!")
        print("   먼저 build_release.py를 실행하세요:")
        print("   python build_release.py")
        sys.exit(1)
    
    print(f"   ZIP 파일: {zip_path}")
    print(f"   크기: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 3. 확인
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    if not auto_confirm:
        confirm = input("\n계속 진행하시겠습니까? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ 배포 취소")
            sys.exit(0)
    else:
        print("\n자동 진행 모드 (--yes)")

    
    # 4. GitHub 토큰 로드
    token_data = load_token()
    github_token = token_data.get('github_token')
    
    # 5. changelog.txt 생성
    changelog = create_changelog_file(version_info)
    
    # 6. GitHub Release 생성 및 업로드
    success = create_github_release(version, changelog, github_token, zip_path)
    
    if not success:
        print("\n❌ 배포 실패")
        sys.exit(1)
    
    # 7. Slack 알림 (선택사항)
    webhook_url = token_data.get('webhook_qa') or token_data.get('webhook_dev')
    if webhook_url:
        send_notify = input("\nSlack 알림을 전송하시겠습니까? (y/n): ").strip().lower()
        if send_notify == 'y':
            send_slack_notification(version, changelog, webhook_url)
    
    print("\n" + "=" * 60)
    print("✅ 배포 완료!")
    print("=" * 60)
    print(f"버전: {version}")
    print(f"Release URL: https://github.com/SungMinseok/GetBuild/releases/tag/v{version}")
    print("\n사용자들은 앱 내 자동 업데이트 기능으로 새 버전을 받을 수 있습니다.")
    print("=" * 60)


if __name__ == '__main__':
    main()

