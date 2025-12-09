# Git에서 schedule.json 파일 제거 가이드

## 📋 개요

`schedule.json` 파일이 실수로 Git에 커밋되어 GitHub에 올라간 상태입니다. 이 파일은 개인 스케줄 정보를 포함하고 있어 공개 저장소에서는 제거해야 합니다.

## 🎯 목표

1. ✅ Git 추적 중단 (더 이상 커밋되지 않도록)
2. ✅ 로컬 파일은 유지 (계속 사용 가능)
3. ✅ GitHub에서 파일 제거
4. ✅ (선택) Git 히스토리에서도 완전히 제거

## 🚀 빠른 실행

### 방법 1: Python 스크립트 (권장)

```bash
python remove_schedule_from_git.py
```

### 방법 2: 배치 파일

```bash
remove_schedule_from_git.bat
```

### 방법 3: 수동 실행

```bash
# 1. Git 캐시에서 제거 (로컬 파일은 유지)
git rm --cached schedule.json

# 2. .gitignore 확인 (이미 있음)
# schedule.json이 .gitignore에 있는지 확인

# 3. 커밋
git add .gitignore
git commit -m "Remove schedule.json from Git tracking"

# 4. GitHub에 푸시
git push
```

## 📝 단계별 설명

### Step 1: Git 인덱스에서 제거

```bash
git rm --cached schedule.json
```

**동작**:
- Git 추적을 중단
- 로컬 파일은 삭제되지 않음 ✅
- 다음 커밋부터 Git이 더 이상 추적하지 않음

### Step 2: .gitignore 확인

`schedule.json`이 이미 `.gitignore`에 포함되어 있는지 확인:

```bash
# .gitignore 내용 확인
type .gitignore | findstr schedule.json
```

**현재 상태**: ✅ 이미 `.gitignore`에 포함됨 (22번 줄)

### Step 3: 변경사항 커밋

```bash
git add .gitignore
git commit -m "Remove schedule.json from Git tracking (keep local file)"
```

### Step 4: GitHub에 푸시

```bash
git push
```

**결과**:
- GitHub에서 `schedule.json` 파일이 사라짐
- 로컬에서는 계속 사용 가능
- 앞으로 커밋되지 않음

## 🔍 추가 작업 (선택사항)

### Git 히스토리에서 완전히 제거

⚠️ **주의**: 이 작업은 Git 히스토리를 다시 쓰므로, 다른 사람과 공유 중인 저장소에서는 신중하게 사용하세요!

#### 방법 1: BFG Repo-Cleaner (권장)

```bash
# 1. BFG 다운로드
# https://rtyley.github.io/bfg-repo-cleaner/

# 2. 파일 제거
java -jar bfg.jar --delete-files schedule.json

# 3. Git 정리
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. 강제 푸시
git push origin --force --all
```

#### 방법 2: git filter-repo (권장)

```bash
# 1. git-filter-repo 설치
pip install git-filter-repo

# 2. 파일 제거
git filter-repo --path schedule.json --invert-paths

# 3. 강제 푸시
git push origin --force --all
```

#### 방법 3: git filter-branch (레거시)

```bash
# 1. 백업 생성
git clone . ../GetBuild_backup

# 2. 히스토리에서 제거
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch schedule.json" \
  --prune-empty --tag-name-filter cat -- --all

# 3. 정리
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. 강제 푸시
git push origin --force --all
git push origin --force --tags
```

## ⚠️ 주의사항

### 1. 협업 중인 저장소

다른 사람과 협업 중이라면:
```bash
# 팀원들에게 알림
# "Git 히스토리를 재작성했으니 다시 클론하세요"

# 팀원들이 해야 할 작업:
git fetch origin
git reset --hard origin/main  # 또는 origin/master
```

### 2. 백업

히스토리 재작성 전 반드시 백업:
```bash
git clone . ../GetBuild_backup
```

### 3. 로컬 파일 보존

작업 전 로컬 파일 백업:
```bash
copy schedule.json schedule.json.backup
```

## 🔒 앞으로의 방지 방법

### 1. .gitignore 확인

커밋 전 항상 `.gitignore` 확인:
```bash
git status
# schedule.json이 표시되지 않아야 함
```

### 2. Pre-commit Hook 설정

`.git/hooks/pre-commit` 파일 생성:
```bash
#!/bin/bash
if git diff --cached --name-only | grep -q "schedule.json"; then
    echo "❌ schedule.json은 커밋할 수 없습니다!"
    exit 1
fi
```

### 3. Git 설정

민감한 파일 패턴을 전역 gitignore에 추가:
```bash
# 전역 .gitignore 설정
git config --global core.excludesfile ~/.gitignore_global

# ~/.gitignore_global에 추가
echo "schedule.json" >> ~/.gitignore_global
echo "token.json" >> ~/.gitignore_global
echo "*.local.json" >> ~/.gitignore_global
```

## 📊 현재 상태 확인

### Git 추적 상태 확인

```bash
# schedule.json이 Git에 추적되고 있는지 확인
git ls-files | findstr schedule.json

# 결과가 없으면: ✅ 추적되지 않음
# 결과가 있으면: ❌ 여전히 추적 중
```

### .gitignore 확인

```bash
# .gitignore에 포함되어 있는지 확인
type .gitignore | findstr schedule.json

# 결과가 있으면: ✅ .gitignore에 포함
```

### 로컬 파일 확인

```bash
# 로컬 파일이 존재하는지 확인
dir schedule.json

# 파일이 보이면: ✅ 로컬 파일 유지됨
```

## 🎯 체크리스트

배포 전:
- [ ] `schedule.json`이 `.gitignore`에 포함됨
- [ ] `token.json`이 `.gitignore`에 포함됨
- [ ] `git status`에서 민감한 파일이 표시되지 않음

Git에서 제거 후:
- [ ] `git ls-files | findstr schedule.json` 결과 없음
- [ ] `git push` 완료
- [ ] GitHub에서 파일 제거 확인
- [ ] 로컬 파일은 여전히 존재
- [ ] 앱이 정상 작동

히스토리 재작성 후 (선택):
- [ ] 백업 생성 완료
- [ ] `git push --force` 완료
- [ ] 팀원들에게 알림
- [ ] GitHub Actions 등 CI/CD 확인

## 💡 FAQ

**Q: 로컬 파일이 삭제되지 않을까요?**  
A: 아니요. `git rm --cached`는 Git 추적만 중단하고 로컬 파일은 유지합니다.

**Q: 이미 GitHub에 올라간 파일은 어떻게 되나요?**  
A: `git push` 후 GitHub에서도 파일이 제거됩니다. 하지만 Git 히스토리에는 남아 있습니다.

**Q: 히스토리에서도 제거해야 하나요?**  
A: 선택사항입니다. 민감한 정보(비밀번호, 토큰 등)가 포함되어 있다면 제거하는 것이 좋습니다.

**Q: filter-branch가 실패합니다.**  
A: `git filter-repo`나 BFG Repo-Cleaner를 사용하세요. 더 안전하고 빠릅니다.

**Q: 다시 커밋되는 것을 방지하려면?**  
A: `.gitignore`에 포함되어 있으면 자동으로 방지됩니다. (현재 이미 포함됨)

## 📚 참고 자료

- [Git - Removing Files](https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository#_removing_files)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [GitHub - Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)

## 🆘 문제 해결

### "pathspec 'schedule.json' did not match any files"

**원인**: 파일이 이미 Git에서 제거됨

**해결**: 정상입니다. 다음 단계로 진행하세요.

### "nothing to commit"

**원인**: 변경사항이 없음

**해결**: `git status`로 확인 후, 이미 완료되었다면 다음 단계로 진행하세요.

### 로컬 파일이 사라짐

**원인**: `git rm --cached` 대신 `git rm` 사용

**해결**: 백업에서 복원
```bash
copy schedule.json.backup schedule.json
# 또는
git checkout HEAD schedule.json
```

---

**작성일**: 2025-10-27  
**버전**: 1.0

