"""
버전 자동 업데이트 스크립트
현재 시간 기반으로 version.json과 version.txt를 업데이트합니다.
"""

import json
from datetime import datetime
import sys


def update_version(changelog_message=None):
    """version.json을 현재 시간 기반으로 업데이트"""
    
    # 현재 시간 기반 버전 생성 (3.0-YY.MM.DD.HHMM)
    now = datetime.now()
    new_version = now.strftime("3.0-%y.%m.%d.%H%M")
    build_date = now.strftime("%Y-%m-%d")
    
    print(f"새 버전: {new_version}")
    print(f"빌드 날짜: {build_date}")
    
    try:
        # 기존 version.json 읽기
        try:
            with open('version.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            old_version = data.get('version', 'unknown')
        except FileNotFoundError:
            # 파일이 없으면 새로 생성
            data = {
                "version": new_version,
                "build_date": build_date,
                "update_url": "https://api.github.com/repos/SungMinseok/GetBuild/releases/latest",
                "changelog": []
            }
            old_version = 'unknown'
        
        print(f"이전 버전: {old_version}")
        
        # 버전 업데이트
        data['version'] = new_version
        data['build_date'] = build_date
        
        # 변경사항 메시지가 있으면 changelog에 추가
        if changelog_message:
            changes = [changelog_message]
        else:
            changes = ["버그 수정 및 성능 개선"]
        
        new_changelog = {
            "version": new_version,
            "date": build_date,
            "changes": changes
        }
        
        # 기존 changelog 앞에 추가
        if 'changelog' not in data:
            data['changelog'] = []
        data['changelog'].insert(0, new_changelog)
        
        # 최대 10개까지만 유지
        if len(data['changelog']) > 10:
            data['changelog'] = data['changelog'][:10]
        
        print(f"변경사항 추가: {', '.join(changes)}")
        
        # version.json 저장
        with open('version.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # version.txt 저장 (기존 호환성)
        with open('version.txt', 'w', encoding='utf-8') as f:
            f.write(new_version)
        
        print("\n✅ 버전 업데이트 완료!")
        print(f"   version.json: {new_version}")
        print(f"   version.txt: {new_version}")
        print(f"   날짜: {build_date}")
        
        return new_version
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    # 커맨드라인 인자로 변경사항 메시지 받기
    changelog_msg = None
    if len(sys.argv) > 1:
        changelog_msg = ' '.join(sys.argv[1:])
    
    version = update_version(changelog_msg)
    print(f"\n다음 단계:")
    print(f"  1. python build_release.py  # 빌드")
    print(f"  2. python deploy_github.py  # 배포")
    print(f"\n또는 Git 태그 생성:")
    print(f"  git tag -a v{version} -m \"Release v{version}\"")
    print(f"  git push origin v{version}")

