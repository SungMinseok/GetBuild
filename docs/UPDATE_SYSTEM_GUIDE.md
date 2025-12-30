# QuickBuild 자동 업데이트 시스템 가이드

## 📋 개요

QuickBuild는 GitHub Releases를 통한 자동 업데이트 시스템을 제공합니다.

### 주요 기능
- GitHub Releases에서 최신 버전 자동 감지
- 사용자 친화적인 업데이트 알림 다이얼로그
- 다운로드 진행률 표시
- 안전한 파일 교체 및 자동 재시작
- About 다이얼로그에서 버전 정보 및 변경사항 확인

---

## 🔧 시스템 구조

### 핵심 파일

```
QuickBuild/
├── updater.py              # 업데이트 로직 (체크/다운로드/설치)
├── update_dialogs.py       # PyQt5 다이얼로그 (알림/진행률/About)
├── version.json            # 현재 버전 정보
└── index.py                # 메인 앱 (업데이트 시스템 통합)
```

### 모듈 설명

#### 1. updater.py
- **UpdateChecker**: GitHub API로 버전 체크
- **UpdateDownloader**: 스트리밍 다운로드 + 진행률 콜백
- **UpdateInstaller**: 배치 스크립트로 안전한 파일 교체
- **AutoUpdater**: 전체 프로세스 통합 관리

#### 2. update_dialogs.py
- **UpdateNotificationDialog**: 업데이트 알림 (릴리즈 노트, 버튼)
- **DownloadProgressDialog**: 다운로드 진행률 표시 (스레드 안전)
- **AboutDialog**: 버전 정보 및 변경사항 표시

#### 3. index.py 통합
- 시작 시 자동 업데이트 체크 (3초 후)
- 메뉴에서 수동 업데이트 확인
- About 다이얼로그에서 업데이트 확인

---

## 🔄 업데이트 프로세스

### 전체 흐름

```
1. 앱 시작
   ↓
2. 3초 후 백그라운드에서 버전 체크 (GitHub API)
   ↓
3. 새 버전 발견 시 UpdateNotificationDialog 표시
   ↓
4. 사용자가 "지금 업데이트" 선택
   ↓
5. DownloadProgressDialog 표시하며 ZIP 다운로드
   ↓
6. 다운로드 완료 후 압축 해제
   ↓
7. update_installer.bat 배치 스크립트 생성 및 실행
   ↓
8. 현재 프로세스 종료
   ↓
9. 배치 스크립트가 파일 교체 후 새 버전 실행
   ↓
10. 새 버전 앱 시작 (업데이트 완료)
```

### 배치 스크립트 동작

`update_installer.bat`가 다음 순서로 실행됩니다:

1. **[1/5]** 현재 프로세스 종료 대기 (taskkill)
2. **[1.5/5]** 파일 핸들 해제 대기 (5초)
3. **[2/5]** 새 파일 복사 (xcopy)
4. **[3/5]** 임시 파일 정리 (ZIP, 압축 해제 폴더)
5. **[4/5]** 새 버전 앱 실행
6. **[5/5]** 배치 파일 자체 삭제

---

## 📝 사용 방법

### 1. 앱 시작 시 자동 체크

앱이 시작되면 3초 후 자동으로 GitHub에서 최신 버전을 확인합니다.
- 새 버전이 있으면 알림 다이얼로그 표시
- 네트워크 오류는 로그에만 기록 (팝업 없음)

### 2. 메뉴에서 수동 체크

**메뉴 → 업데이트 확인**을 클릭하면 즉시 업데이트를 확인합니다.
- 최신 버전이면 "최신 버전을 사용 중입니다" 메시지 표시
- 새 버전이 있으면 UpdateNotificationDialog 표시

### 3. About 다이얼로그

**메뉴 → About**을 클릭하면 버전 정보를 확인할 수 있습니다.
- 현재 버전 및 빌드 날짜
- 최근 변경사항 (version.json의 changelog)
- **업데이트 확인** 버튼으로 수동 체크 가능

---

## 🎨 UI 다이얼로그

### UpdateNotificationDialog

```
┌─────────────────────────────────────────┐
│  🎉 새로운 버전이 출시되었습니다!        │
│                                         │
│  새 버전: 3.0.1                         │
│  발행일: 2025-12-12                     │
│                                         │
│  📝 변경사항:                            │
│  ┌─────────────────────────────────┐   │
│  │ • 새 기능 추가                  │   │
│  │ • 버그 수정                     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [나중에] [건너뛰기]     [지금 업데이트] │
└─────────────────────────────────────────┘
```

**버튼 동작:**
- **지금 업데이트**: 다운로드 시작
- **나중에**: 다이얼로그 닫기 (다음 실행 시 다시 표시)
- **이 버전 건너뛰기**: 이 버전 무시 (TODO: 설정 저장)

### DownloadProgressDialog

```
┌─────────────────────────────────────┐
│  업데이트 파일 다운로드 중...        │
│                                     │
│  [████████████░░░░░░░░░░] 65%        │
│                                     │
│                    15.2 MB / 23.5 MB │
│                                     │
│                      [취소]         │
└─────────────────────────────────────┘
```

**기능:**
- 실시간 진행률 표시
- 다운로드 크기 표시 (MB 단위)
- 취소 버튼 (확인 후 다운로드 중단)

### AboutDialog

```
┌─────────────────────────────────────┐
│  [아이콘] QuickBuild                 │
│           PUBG 빌드 자동화 도구      │
│                                     │
│  버전: 3.0.0                        │
│  빌드 날짜: 2025-12-12              │
│                                     │
│  📝 최근 변경사항:                   │
│  ┌─────────────────────────────┐   │
│  │ v3.0.0                      │   │
│  │ • Semantic Versioning 전환  │   │
│  │ • 스케줄 필터링 기능 추가    │   │
│  └─────────────────────────────┘   │
│                                     │
│  [업데이트 확인]          [닫기]    │
└─────────────────────────────────────┘
```

---

## ⚙️ 설정

### version.json 형식

```json
{
  "version": "3.0.0",
  "build_date": "2025-12-12",
  "update_url": "https://api.github.com/repos/SungMinseok/GetBuild/releases/latest",
  "changelog": [
    {
      "version": "3.0.0",
      "date": "2025-12-12",
      "changes": [
        "Semantic Versioning 전환 (3.0.0)",
        "스케줄 필터링 기능 추가",
        "빌드 스크립트 자동화 시스템 구축"
      ]
    }
  ]
}
```

### updater.py 설정

GitHub 리포지토리 변경 시 `UpdateChecker.check_for_updates()` 메서드 수정:

```python
api_url = "https://api.github.com/repos/USERNAME/REPO/releases/latest"
```

---

## 🔍 문제 해결

### Q1: "업데이트 모듈을 불러올 수 없습니다"

**원인:** `updater.py` 또는 `update_dialogs.py` import 실패

**해결:**
1. 파일 존재 확인: `updater.py`, `update_dialogs.py`
2. 의존성 설치: `pip install requests packaging PyQt5`

### Q2: "네트워크 오류" 또는 "업데이트 확인 실패"

**원인:** GitHub API 연결 실패 또는 Rate Limit

**해결:**
1. 인터넷 연결 확인
2. GitHub API Rate Limit: 익명 60회/시간 (충분함)
3. 방화벽 확인

### Q3: 다운로드 후 Windows Defender 차단

**원인:** 다운로드된 파일의 Zone.Identifier

**해결:**
- updater.py에서 자동으로 제거됨 (이미 구현됨)
- 문제 지속 시 수동으로 "차단 해제" 체크

### Q4: 배치 스크립트 실패 ("파일 복사 실패")

**원인:** 파일 경로 공백, 권한 문제

**해결:**
1. 경로에 큰따옴표 사용 (이미 구현됨)
2. 관리자 권한 없이 실행 가능 (설계됨)
3. 안티바이러스 일시 중지

### Q5: PyQt5 스레드 오류 ("GUI 스레드 외부에서 호출")

**원인:** 다운로드 스레드에서 직접 UI 업데이트

**해결:**
- PyQt5 시그널/슬롯 사용 (이미 구현됨)
- `update_dialogs.py`의 `progress_updated`, `download_completed` 시그널

---

## 🚀 개발자 가이드

### 테스트

#### 1. 버전 체크 테스트

```bash
python updater.py
```

단독 실행 시 버전 체크 → 다운로드 → 설치까지 전체 플로우 테스트

#### 2. UI 다이얼로그 테스트

```python
from PyQt5.QtWidgets import QApplication
from update_dialogs import UpdateNotificationDialog, AboutDialog
import sys

app = QApplication(sys.argv)

# 업데이트 알림 테스트
info = {
    'version': '3.0.1',
    'published_at': '2025-12-12T10:00:00Z',
    'release_notes': '• 테스트 릴리즈\n• 버그 수정'
}
dialog = UpdateNotificationDialog(info)
dialog.exec_()

# About 다이얼로그 테스트
about = AboutDialog()
about.exec_()

sys.exit()
```

### 새 버전 릴리즈 방법

1. **version.json 업데이트**
   ```json
   {
     "version": "3.0.1",
     "build_date": "2025-12-13",
     "changelog": [
       {
         "version": "3.0.1",
         "date": "2025-12-13",
         "changes": ["새 기능", "버그 수정"]
       },
       ...
     ]
   }
   ```

2. **빌드 생성**
   ```bash
   python build.py  # 또는 빌드 스크립트
   ```

3. **GitHub Release 생성**
   - Tag: `v3.0.1` (v 접두사 필수)
   - Title: `QuickBuild v3.0.1`
   - Description: 변경사항 작성
   - Assets: `QuickBuild_v3.0.1.zip` 업로드 (이름에 QuickBuild 포함)

4. **자동 배포**
   - 사용자가 앱 시작 시 자동으로 새 버전 감지
   - "지금 업데이트" 클릭 시 자동 설치

---

## 📚 참고 문서

- [앱_자동_업데이트_시스템_문서.md](../앱_자동_업데이트_시스템_문서.md) - 상세 기술 문서
- [GitHub Releases API](https://docs.github.com/en/rest/releases/releases)
- [Semantic Versioning](https://semver.org/lang/ko/)

---

**문서 버전:** 1.0.0  
**작성일:** 2025-12-12  
**작성자:** AI Assistant

