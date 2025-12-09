# QuickBuild 로컬 빌드 및 GitHub 배포 가이드

이 문서는 QuickBuild 프로젝트를 로컬에서 빌드하고 GitHub Release로 배포하는 방법을 설명합니다.

**배포 방식**: 로컬 빌드 후 수동 배포 (GitHub Actions 미사용)

## 📋 목차
1. [전체 구조 개요](#전체-구조-개요)
2. [초기 설정](#초기-설정)
3. [배포 워크플로우](#배포-워크플로우)
4. [스크립트 설명](#스크립트-설명)
5. [문제 해결](#문제-해결)
6. [체크리스트](#체크리스트)

---

## 전체 구조 개요

```
GetBuild_clean/
├── version.json           # 버전 정보 및 changelog
├── version.txt            # 버전 정보 (레거시 호환)
├── update_version.py      # 버전 자동 업데이트 스크립트
├── build_release.py       # PyInstaller 빌드 스크립트
├── deploy_github.py       # GitHub Release 배포 스크립트
├── changelog.txt          # 릴리즈 노트 작성용
├── token.json            # GitHub Token 및 Webhook URL (gitignore)
├── token.json.example    # token.json 예시
└── dist/
    └── QuickBuild_3.0-25.10.26.1805.zip  # 빌드 결과물
```

**배포 흐름**:
1. `update_version.py` → 버전 업데이트
2. `build_release.py` → EXE 빌드 및 ZIP 생성
3. `deploy_github.py` → GitHub Release 생성 및 ZIP 업로드

---

## 초기 설정 (최초 1회)

### 1. Python 및 의존성 설치

```bash
# Python 버전 확인 (3.11 권장)
python --version

# 의존성 설치
pip install -r requirements.txt
pip install pyinstaller
```

### 2. GitHub Personal Access Token 생성

1. GitHub 접속 → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. "Generate new token" 클릭
4. **권한 선택**: `repo` (전체) 체크
5. 토큰 생성 및 복사

### 3. token.json 파일 생성

```bash
# token.json.example을 복사
copy token.json.example token.json

# token.json 편집
notepad token.json
```

**token.json 내용**:
```json
{
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx",
  "webhook_qa": "https://hooks.slack.com/services/...",
  "webhook_dev": "https://hooks.slack.com/services/..."
}
```

> ⚠️ **중요**: `token.json`은 절대 Git에 커밋하지 마세요! (`.gitignore`에 이미 포함됨)

### 4. 초기 버전 확인

`version.json` 파일이 자동 생성되어 있는지 확인:
```json
{
  "version": "3.0-25.10.26.1805",
  "build_date": "2025-10-26",
  "update_url": "https://api.github.com/repos/SungMinseok/GetBuild/releases/latest",
  "changelog": [...]
}
```

---

## 배포 워크플로우

### 전체 프로세스 (한 줄 요약)

```bash
# 1단계: 버전 업데이트
python update_version.py "변경사항 메시지"

# 2단계: 빌드
python build_release.py

# 3단계: Git 커밋 (선택)
git add .
git commit -m "버전 업데이트: 3.0-25.10.27.1430"
git push

# 4단계: GitHub 배포
python deploy_github.py
```

### 상세 단계별 설명

#### Step 1: 버전 업데이트

```bash
python update_version.py "스케줄 진행 상태 표시 기능 추가"
```

**실행 결과**:
```
새 버전: 3.0-25.10.27.1430
빌드 날짜: 2025-10-27
이전 버전: 3.0-25.10.26.1805
변경사항 추가: 스케줄 진행 상태 표시 기능 추가

✅ 버전 업데이트 완료!
   version.json: 3.0-25.10.27.1430
   version.txt: 3.0-25.10.27.1430
   날짜: 2025-10-27
```

**수행 작업**:
- 현재 시간 기반으로 새 버전 생성 (`3.0-YY.MM.DD.HHMM`)
- `version.json` 업데이트
- `version.txt` 업데이트 (레거시 호환)
- changelog에 변경사항 추가

#### Step 2: 로컬 빌드

```bash
python build_release.py
```

**실행 과정**:
```
============================================================
QuickBuild 릴리즈 빌드
============================================================
버전: 3.0-25.10.27.1430
빌드 날짜: 2025-10-27
✅ version_info.txt 생성 완료
✅ QuickBuild_release.spec 생성 완료

🔨 PyInstaller 빌드 시작...
✅ 빌드 완료

📦 ZIP 패키징 중: QuickBuild_3.0-25.10.27.1430.zip
  ✓ QuickBuild.exe 추가
  ✓ version.json 추가
  ✓ Readme.md 추가
✅ ZIP 생성 완료: dist\QuickBuild_3.0-25.10.27.1430.zip
   파일 크기: 25.34 MB

🧹 임시 파일 정리 중...
✅ 정리 완료

============================================================
✅ 빌드 완료!
============================================================
버전: 3.0-25.10.27.1430
출력 파일: dist/QuickBuild_3.0-25.10.27.1430.zip
```

**생성되는 파일**:
- `dist/QuickBuild_3.0-25.10.27.1430.zip` (최종 배포 파일)

#### Step 3: Git 커밋 (선택사항)

```bash
git add .
git commit -m "버전 업데이트: 3.0-25.10.27.1430 - 스케줄 진행 상태 표시 추가"
git push
```

> 💡 **팁**: 배포 전에 코드 변경사항을 커밋하는 것이 좋습니다.

#### Step 4: GitHub Release 배포

```bash
python deploy_github.py
```

**실행 흐름**:
```
============================================================
QuickBuild GitHub Release 배포
============================================================

📌 배포 정보:
   버전: 3.0-25.10.27.1430
   날짜: 2025-10-27
   ZIP 파일: dist\QuickBuild_3.0-25.10.27.1430.zip
   크기: 25.34 MB

계속 진행하시겠습니까? (y/n): y

✅ changelog.txt 생성 완료
   changelog.txt 파일이 열렸습니다.

👉 changelog.txt 편집 완료 후 엔터를 누르세요 (또는 그냥 엔터)...
```

**changelog.txt 편집**:
```markdown
# QuickBuild 3.0-25.10.27.1430 릴리즈 노트

**빌드 날짜**: 2025-10-27

## 변경사항

* 스케줄 진행 상태 실시간 표시 기능 추가
* ScheduleDialog에 소스/로컬 경로 설정 기능 추가
* 개별 스케줄 위젯에 진행 상태 표시
* 상단 헤더에 실행 중인 스케줄 요약 표시
* UI 개선 및 버그 수정
```

**배포 완료**:
```
🚀 GitHub Release 생성 중...
   저장소: SungMinseok/GetBuild
   태그: v3.0-25.10.27.1430
✅ Release 생성 성공!
   URL: https://github.com/SungMinseok/GetBuild/releases/tag/v3.0-25.10.27.1430

📦 ZIP 파일 업로드 중...
   파일: QuickBuild_3.0-25.10.27.1430.zip
   크기: 25.34 MB
✅ 파일 업로드 성공!

Slack 알림을 전송하시겠습니까? (y/n): y
✅ Slack 알림 전송 완료

============================================================
✅ 배포 완료!
============================================================
버전: 3.0-25.10.27.1430
Release URL: https://github.com/SungMinseok/GetBuild/releases/tag/v3.0-25.10.27.1430
============================================================
```

---

## 스크립트 설명

### 1. update_version.py

**목적**: 버전 번호를 현재 시간 기반으로 자동 생성

**사용법**:
```bash
# 버전만 업데이트
python update_version.py

# 변경사항 메시지와 함께
python update_version.py "새 기능 추가 및 버그 수정"
```

**버전 형식**: `3.0-YY.MM.DD.HHMM`
- 예시: `3.0-25.10.27.1430` (2025년 10월 27일 14시 30분)

### 2. build_release.py

**목적**: PyInstaller로 실행 파일 빌드 및 ZIP 패키징

**주요 기능**:
1. Windows 버전 정보 파일 생성 (`version_info.txt`)
2. PyInstaller spec 파일 동적 생성 (`QuickBuild_release.spec`)
3. `index_v2.py`를 진입점으로 EXE 빌드
4. ZIP 패키지 생성 (EXE + version.json + Readme.md)
5. 임시 파일 자동 정리

**출력**: `dist/QuickBuild_<버전>.zip`

### 3. deploy_github.py

**목적**: GitHub Release 생성 및 ZIP 파일 업로드

**주요 기능**:
1. `dist/` 폴더에서 ZIP 파일 자동 검색
2. `changelog.txt` 파일 자동 생성 및 편집
3. GitHub API로 Release 생성
4. ZIP 파일 업로드
5. Slack Webhook 알림 (선택사항)

**필수 파일**: `token.json` (GitHub Token 포함)

---

## 문제 해결

### 1. dist 폴더에 ZIP 파일이 없음

**증상**:
```
❌ dist/QuickBuild_3.0-25.10.27.1430.zip 파일이 존재하지 않습니다!
```

**해결**:
```bash
python build_release.py  # 먼저 빌드 실행
```

### 2. GitHub Token 오류

**증상**:
```
❌ token.json 파일이 없습니다!
```

**해결**:
1. `token.json.example`을 복사하여 `token.json` 생성
2. GitHub Personal Access Token 발급
3. `token.json`에 토큰 추가:
```json
{
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx"
}
```

### 3. 릴리즈 생성 실패 (409 Conflict)

**증상**:
```
❌ Release 생성 실패: 409
💡 동일한 버전의 Release가 이미 존재합니다.
```

**해결**:
```bash
# 옵션 1: GitHub에서 기존 Release 삭제
# https://github.com/SungMinseok/GetBuild/releases

# 옵션 2: 새 버전으로 업데이트
python update_version.py "재배포"
python build_release.py
python deploy_github.py
```

### 4. PyInstaller 빌드 실패

**체크리스트**:
```bash
# Python 버전 확인
python --version  # 3.11 권장

# 의존성 설치
pip install -r requirements.txt
pip install pyinstaller

# version.json 확인
type version.json

# core, ui 모듈 확인
dir core
dir ui
```

### 5. 빌드된 EXE가 실행되지 않음

**원인**: 누락된 의존성 또는 hiddenimports 문제

**해결**:
1. `build_release.py`의 `hiddenimports` 섹션 확인
2. 콘솔 모드로 빌드하여 오류 확인:
```python
# QuickBuild_release.spec에서
console=True  # False → True로 변경
```

---

## 체크리스트

### 초기 설정 (최초 1회)

- [ ] Python 3.11 설치 확인
- [ ] `requirements.txt` 의존성 설치
  ```bash
  pip install -r requirements.txt
  pip install pyinstaller
  ```
- [ ] GitHub Personal Access Token 발급
- [ ] `token.json` 파일 생성 및 토큰 추가
- [ ] `.gitignore`에 `token.json` 포함 확인
- [ ] `version.json` 파일 존재 확인

### 매 배포 시 (반복)

- [ ] 1. 코드 변경사항 완료 및 테스트
- [ ] 2. 버전 업데이트
  ```bash
  python update_version.py "변경사항 메시지"
  ```
- [ ] 3. 로컬 빌드
  ```bash
  python build_release.py
  ```
- [ ] 4. 빌드 결과 확인 (`dist/QuickBuild_<버전>.zip` 존재)
- [ ] 5. Git 커밋 및 푸시 (선택사항)
  ```bash
  git add .
  git commit -m "버전 업데이트: <버전>"
  git push
  ```
- [ ] 6. GitHub Release 배포
  ```bash
  python deploy_github.py
  ```
- [ ] 7. `changelog.txt` 편집 (릴리즈 노트 작성)
- [ ] 8. 콘솔에서 엔터 입력하여 배포 진행
- [ ] 9. Slack 알림 전송 (선택사항)
- [ ] 10. GitHub Release 페이지에서 배포 확인
  ```
  https://github.com/SungMinseok/GetBuild/releases
  ```

---

## 버전 형식 설명

### 표시용 버전
**형식**: `3.0-YY.MM.DD.HHMM`
- 예시: `3.0-25.10.27.1430`
- 메이저: `3`
- 마이너: `0`
- 빌드: `25.10.27.1430` (날짜/시간)

### Windows 파일 버전
**형식**: `3,0,YYMMDD,HHMM`
- 예시: `3,0,251027,1430`
- 각 부분은 0-65535 범위

---

## GitHub Release URL

**저장소**: https://github.com/SungMinseok/GetBuild

**릴리즈 페이지**: https://github.com/SungMinseok/GetBuild/releases

**최신 릴리즈 API**: https://api.github.com/repos/SungMinseok/GetBuild/releases/latest

---

## 추가 리소스

### GitHub API 문서
- [GitHub REST API - Releases](https://docs.github.com/en/rest/releases/releases)
- [Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

### PyInstaller 문서
- [PyInstaller 공식 문서](https://pyinstaller.org/)
- [Version Information (Windows)](https://pyinstaller.org/en/stable/usage.html#capturing-windows-version-data)

---

## FAQ

**Q: 매번 빌드해야 하나요?**  
A: 네, 코드 변경 시마다 빌드가 필요합니다. `build_release.py`로 빌드하고 `deploy_github.py`로 배포합니다.

**Q: 버전을 수동으로 관리할 수 있나요?**  
A: 가능합니다. `version.json` 파일을 직접 수정하면 됩니다. 하지만 `update_version.py`를 사용하면 자동으로 시간 기반 버전이 생성되어 편리합니다.

**Q: Slack 알림이 필수인가요?**  
A: 아니요. `token.json`에 Webhook URL이 없으면 알림을 건너뜁니다.

**Q: changelog.txt는 매번 작성해야 하나요?**  
A: `deploy_github.py` 실행 시 자동으로 생성되며, 편집 후 엔터를 누르거나 그냥 엔터를 눌러 기본 내용으로 배포할 수 있습니다.

**Q: index.py와 index_v2.py 중 어떤 것을 사용하나요?**  
A: 현재 빌드 스크립트는 `index_v2.py`를 진입점으로 사용합니다. 이는 새로운 스케줄 중심 UI입니다.

---

**작성일**: 2025-10-27  
**버전**: 1.0  
**배포 방식**: 로컬 빌드 + 수동 배포

