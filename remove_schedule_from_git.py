"""
schedule.json 파일을 Git에서 완전히 제거하는 스크립트
로컬 파일은 유지하면서 Git 추적만 중단합니다.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, check=True):
    """명령어 실행 및 결과 출력"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(f"⚠️  {e.stderr}")
        return False


def check_git_repo():
    """Git 저장소인지 확인"""
    if not Path('.git').exists():
        print("❌ 현재 디렉토리가 Git 저장소가 아닙니다!")
        sys.exit(1)


def is_file_tracked(filename):
    """파일이 Git에 추적되고 있는지 확인"""
    result = subprocess.run(
        f'git ls-files "{filename}"',
        shell=True,
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())


def main():
    """메인 프로세스"""
    print("=" * 60)
    print("schedule.json 파일을 Git에서 제거")
    print("=" * 60)
    print()
    
    # Git 저장소 확인
    check_git_repo()
    
    filename = "schedule.json"
    
    # 1. 파일이 Git에 추적되고 있는지 확인
    print(f"[1/5] {filename} 추적 상태 확인 중...")
    is_tracked = is_file_tracked(filename)
    
    if is_tracked:
        print(f"✅ {filename}이 Git에 추적되고 있습니다.")
    else:
        print(f"ℹ️  {filename}이 이미 Git에서 추적되지 않습니다.")
    
    print()
    
    # 2. Git 캐시에서 제거 (로컬 파일은 유지)
    print(f"[2/5] Git 인덱스에서 {filename} 제거 중...")
    if is_tracked:
        success = run_command(f'git rm --cached "{filename}"', check=False)
        if success:
            print(f"✅ Git 인덱스에서 제거 완료")
        else:
            print(f"ℹ️  이미 제거되었거나 변경사항 없음")
    else:
        print("ℹ️  제거할 필요 없음 (이미 추적되지 않음)")
    
    print()
    
    # 3. .gitignore 확인
    print("[3/5] .gitignore 확인 중...")
    gitignore_path = Path('.gitignore')
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        if filename in gitignore_content:
            print(f"✅ {filename}이 이미 .gitignore에 있습니다.")
        else:
            print(f"⚠️  {filename}이 .gitignore에 없습니다. 추가 중...")
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{filename}\n")
            print(f"✅ .gitignore에 추가 완료")
    else:
        print("⚠️  .gitignore 파일이 없습니다. 생성 중...")
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(f"{filename}\n")
        print(f"✅ .gitignore 생성 및 {filename} 추가 완료")
    
    print()
    
    # 4. 변경사항 커밋
    print("[4/5] 변경사항 커밋 중...")
    
    # 상태 확인
    result = subprocess.run(
        'git status --short',
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print("변경사항:")
        print(result.stdout)
        
        # .gitignore 추가
        run_command('git add .gitignore', check=False)
        
        # 커밋
        commit_msg = f"Remove {filename} from Git tracking (keep local file)"
        success = run_command(f'git commit -m "{commit_msg}"', check=False)
        
        if success:
            print("✅ 커밋 완료")
        else:
            print("ℹ️  커밋할 변경사항이 없거나 이미 커밋됨")
    else:
        print("ℹ️  커밋할 변경사항이 없습니다.")
    
    print()
    
    # 5. 로컬 파일 확인
    print(f"[5/5] 로컬 {filename} 파일 확인 중...")
    if Path(filename).exists():
        print(f"✅ 로컬 {filename} 파일은 그대로 유지되고 있습니다.")
    else:
        print(f"⚠️  로컬 {filename} 파일이 없습니다. (정상적으로 삭제되었거나 원래 없었음)")
    
    print()
    print("=" * 60)
    print("✅ 작업 완료!")
    print("=" * 60)
    print()
    print("📝 다음 단계:")
    print()
    print("1. 변경사항을 GitHub에 푸시하세요:")
    print("   git push")
    print()
    print("2. (선택) Git 히스토리에서도 완전히 제거하려면:")
    print("   아래 명령어를 실행하세요 (주의: 히스토리 재작성)")
    print()
    print("   # BFG Repo-Cleaner 사용 (권장):")
    print("   java -jar bfg.jar --delete-files schedule.json")
    print("   git reflog expire --expire=now --all")
    print("   git gc --prune=now --aggressive")
    print()
    print("   # 또는 git filter-repo 사용:")
    print("   git filter-repo --path schedule.json --invert-paths")
    print()
    print("⚠️  주의:")
    print("   - 히스토리 재작성은 다른 사람과 공유 중인 저장소에서는")
    print("     협업에 문제를 일으킬 수 있습니다.")
    print("   - 반드시 백업 후 진행하세요.")
    print()
    print(f"💡 {filename}은 앞으로 Git에 추적되지 않습니다.")
    print("   (로컬에서는 계속 사용 가능)")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 취소되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

