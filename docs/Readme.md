# QuickBuild - Build Management Tool

[![GitHub Release](https://img.shields.io/github/v/release/SungMinseok/GetBuild)](https://github.com/SungMinseok/GetBuild/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

PyQt5 기반 빌드 관리 및 배포 자동화 도구입니다.

## 🌟 주요 기능

### 빌드 관리
- **폴더 선택**: 소스 및 대상 폴더 쉽게 선택
- **동적 드롭다운**: 수정 시간 또는 리비전별 정렬된 빌드 폴더 목록
- **폴더 복사**: 소스에서 대상 디렉토리로 폴더 복사
- **폴더 압축**: 효율적인 저장을 위한 ZIP 압축

### 스케줄 관리 (v3.0+)
- **스케줄 생성/편집**: 시각적 UI로 스케줄 관리
- **반복 설정**: 일회성, 매일, 주간 반복 지원
- **실시간 진행 상태**: 각 스케줄의 실행 상태 실시간 표시
- **경로 설정**: 스케줄별 소스/로컬 경로 개별 설정
- **상태 요약**: 상단 헤더에 실행 중인 스케줄 개수 표시

### AWS 통합
- **S3 업로드**: ZIP 파일을 AWS S3에 업로드
- **AWS 설정 업데이트**: AWS 구성 자동 업데이트
- **서버 패치**: 원격 서버 자동 패치

### 자동화
- **예약 작업**: 특정 시간에 자동 실행
- **TeamCity 연동**: 빌드 자동 트리거

## 📸 스크린샷

### 메인 UI (v3.0)
![Main UI](https://github.com/SungMinseok/GetBuild/raw/main/screenshots/main_ui.png)

### 스케줄 관리
![Schedule Manager](https://github.com/SungMinseok/GetBuild/raw/main/screenshots/schedule.png)

## 🚀 시작하기

### 필수 요구사항

- Python 3.11+
- Windows 10/11
- PyQt5
- 필요한 Python 패키지 (requirements.txt 참조)

### 설치

1. **저장소 클론**
```bash
git clone https://github.com/SungMinseok/GetBuild.git
cd GetBuild
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

3. **설정 파일 생성**
```bash
# settings.json 생성 (첫 실행 시 자동 생성됨)
python index_v2.py
```

### 실행

```bash
# v3.0 스케줄 중심 UI (권장)
python index_v2.py

# 레거시 UI
python index.py
```

## 📦 빌드 및 배포

자세한 내용은 [배포 가이드](DEPLOYMENT_GUIDE.md)를 참조하세요.

### 빠른 배포

```bash
# 배치 파일로 한 번에 배포
quick_deploy.bat

# 또는 단계별 실행
python update_version.py "변경사항 메시지"
python build_release.py
python deploy_github.py
```

### 배포 프로세스

1. **버전 업데이트**: `update_version.py`
2. **로컬 빌드**: `build_release.py` → `dist/QuickBuild_<버전>.zip`
3. **GitHub 배포**: `deploy_github.py` → GitHub Release 생성

## 📖 문서

- [배포 가이드](DEPLOYMENT_GUIDE.md) - 로컬 빌드 및 GitHub 배포
- [스케줄 테스트 가이드](SCHEDULE_TEST_GUIDE.md) - 스케줄 기능 테스트
- [리팩토링 가이드](README_REFACTORING.md) - 코드 구조 설명
- [V2 UI 가이드](README_V2_UI.md) - 새로운 UI 설명

## 🔧 설정

### settings.json
```json
{
  "input_box1": "\\\\pubg-pds\\PBB\\Builds",
  "input_box2": "C:/mybuild",
  "buildnames": ["game_SEL", "game_progression"],
  "awsurl": "https://awsdeploy.pbb-qa.pubg.io/environment/..."
}
```

### schedule.json
```json
[
  {
    "id": "uuid",
    "name": "클라복사 - 09:00",
    "time": "09:00",
    "option": "클라복사",
    "buildname": "game_SEL",
    "src_path": "\\\\pubg-pds\\PBB\\Builds",
    "dest_path": "C:/mybuild",
    "repeat_type": "daily",
    "enabled": true
  }
]
```

## 🎯 실행 옵션

- **클라복사**: WindowsClient 폴더만 복사
- **서버복사**: WindowsServer 폴더만 복사
- **전체복사**: 전체 빌드 폴더 복사
- **서버업로드**: 서버 빌드를 ZIP으로 압축 및 S3 업로드
- **서버패치**: AWS 서버 자동 패치
- **서버업로드및패치**: 업로드 후 패치 자동 실행
- **빌드굽기**: TeamCity 빌드 트리거

## 🔄 버전 관리

**버전 형식**: `3.0-YY.MM.DD.HHMM`

- 예시: `3.0-25.10.27.1430` (2025년 10월 27일 14시 30분)
- 자동 업데이트: 앱 내 업데이트 확인 기능 지원

## 📝 변경 로그

### v3.0-25.10.27 (2025-10-27)
- ✨ 스케줄 진행 상태 실시간 표시 기능 추가
- ✨ ScheduleDialog에 소스/로컬 경로 설정 기능 추가
- 🎨 개별 스케줄 위젯에 진행 상태 표시
- 🎨 상단 헤더에 실행 중인 스케줄 요약 표시
- 🐛 클라복사 실행 시 작동하지 않던 문제 수정
- 🐛 빌드명 자동 검색 기능 추가

### v3.0-25.10.26 (2025-10-26)
- 🎉 새로운 스케줄 중심 UI (index_v2.py)
- ✨ 스케줄 생성/편집 다이얼로그
- ✨ 반복 설정 (일회성, 매일, 주간)
- ✨ 스케줄 복사 기능
- 🏗️ 코드 리팩토링 (core, ui 모듈 분리)

전체 변경 로그는 [CHANGELOG.txt](CHANGELOG.txt)를 참조하세요.

## 🤝 기여

Pull Request를 환영합니다! 큰 변경사항의 경우 먼저 이슈를 열어 논의해 주세요.

## 📄 라이센스

[MIT License](LICENSE)

## 👥 제작

- **개발자**: SungMinseok
- **저장소**: [https://github.com/SungMinseok/GetBuild](https://github.com/SungMinseok/GetBuild)
- **이슈 리포트**: [Issues](https://github.com/SungMinseok/GetBuild/issues)

## 📞 지원

- **버그 리포트**: [GitHub Issues](https://github.com/SungMinseok/GetBuild/issues)

---
