# 리팩토링 완료 문서

## 개요
`index.py`와 `aws.py`에 집중되어 있던 코드를 기능별로 분리하여 유지보수성을 개선했습니다.

## 변경 사항

### 새로 추가된 모듈 구조

```
core/
├── __init__.py          # 모듈 초기화
├── config_manager.py    # 설정 관리 (config.json, settings.json)
├── scheduler.py         # 스케줄 관리 (schedule.json)
├── build_operations.py  # 빌드 복사/압축 작업
└── aws_manager.py       # AWS 배포 관련 작업 (기존 aws.py 정리)
```

### 각 모듈의 역할

#### 1. `core/config_manager.py`
- **기능**: 설정 파일 읽기/쓰기 관리
- **주요 메서드**:
  - `get_buildnames()`: 빌드명 목록 조회
  - `add_buildname()`: 빌드명 추가
  - `remove_buildname()`: 빌드명 삭제
  - `get_awsurls()`: AWS URL 목록 조회
  - `load_settings()` / `save_settings()`: 설정 로드/저장

#### 2. `core/scheduler.py`
- **기능**: 예약 스케줄 관리
- **주요 메서드**:
  - `load_schedules()`: 스케줄 목록 로드 (구버전 dict 포맷도 호환)
  - `add_schedule()`: 스케줄 추가
  - `get_due_schedules()`: 현재 시각 실행 스케줄 조회
  - `get_formatted_schedules()`: UI 표시용 포맷팅

#### 3. `core/build_operations.py`
- **기능**: 빌드 파일 작업
- **주요 메서드**:
  - `extract_revision_number()`: 리비전 번호 추출
  - `get_file_count()`: 파일 개수 계산
  - `copy_folder()`: 폴더 복사 (진행률 콜백 지원)
  - `zip_folder()`: 폴더 압축 (진행률 콜백 지원)
  - `get_latest_builds()`: 최신 빌드 목록 조회
  - `generate_backend_bat_files()`: BAT 파일 생성

#### 4. `core/aws_manager.py`
- **기능**: AWS 배포 작업 (기존 `aws.py` 개선)
- **주요 메서드**:
  - `start_driver()`: Chrome 디버깅 드라이버 시작
  - `upload_server_build()`: 서버 빌드 업로드
  - `update_server_container()`: 서버 컨테이너 패치
  - `run_teamcity_build()`: TeamCity 빌드 실행

### index.py 변경사항

**Before**:
```python
import aws
# ... 많은 직접 구현된 메서드들

class FolderCopyApp(QWidget):
    def extract_revision_number(self, folder_name):
        # 직접 구현
        import re
        match = re.search(r'_r(\d+)', folder_name)
        ...
```

**After**:
```python
from core import ConfigManager, ScheduleManager, BuildOperations
from core.aws_manager import AWSManager

class FolderCopyApp(QWidget):
    def __init__(self):
        self.config_mgr = ConfigManager()
        self.schedule_mgr = ScheduleManager()
        self.build_ops = BuildOperations()
        
    def extract_revision_number(self, folder_name):
        return self.build_ops.extract_revision_number(folder_name)
```

## 주요 개선사항

### 1. 관심사의 분리 (Separation of Concerns)
- UI 로직 (`index.py`)과 비즈니스 로직 (`core/` 모듈) 분리
- 각 모듈이 단일 책임만 가지도록 설계

### 2. 재사용성 향상
- 각 모듈을 독립적으로 테스트/사용 가능
- 다른 프로젝트에서도 `core/` 모듈 재사용 가능

### 3. 유지보수성 개선
- 기능별로 파일이 분리되어 수정이 용이
- 버그 발생 시 해당 모듈만 확인하면 됨

### 4. 코드 가독성 향상
- `index.py`가 1400줄에서 UI 중심 코드로 간소화
- 각 메서드가 명확한 모듈 API 호출로 변경

## 사용 예시

### 설정 관리
```python
# 기존
with open('config.json', 'r') as f:
    config = json.load(f)
    buildnames = config.get('buildnames', [])

# 리팩토링 후
buildnames = self.config_mgr.get_buildnames()
```

### 스케줄 관리
```python
# 기존
with open('schedule.json', 'r') as f:
    schedules = json.load(f)
    # ... 복잡한 로직

# 리팩토링 후
schedules = self.schedule_mgr.load_schedules()
text = self.schedule_mgr.get_formatted_schedules()
```

### 빌드 작업
```python
# 기존
for root, dirs, files in os.walk(src_path):
    # ... 많은 복사 로직

# 리팩토링 후
self.build_ops.copy_folder(src_path, dest_path, progress_callback, cancel_check)
```

## 호환성
- 기존 JSON 파일 포맷 완전 호환
- 기존 `settings.json`, `config.json`, `schedule.json` 그대로 사용 가능
- UI 및 사용자 경험 변경 없음

## 향후 확장 가능성
- `core/` 모듈에 단위 테스트 추가 용이
- 로깅, 에러 처리 중앙화 가능
- 플러그인 시스템 구현 가능
- CLI 인터페이스 추가 가능

## 주의사항
- 기존 `aws.py`는 `core/aws_manager.py`로 대체되었으나, 하위 호환성을 위해 유지
- 새로운 기능 추가 시 `core/` 모듈을 먼저 확인하여 중복 구현 방지

## 최신 업데이트 (2025-10-26)

### 예약 스케줄 시스템 전면 확장

#### 1. 여러 예약 동시 지원
- **기존**: 단일 예약만 지원 (체크박스 + 시간 설정)
- **변경**: 다중 스케줄 지원 (`schedule.json` 파일 기반)
- **특징**:
  - 같은 시간에 여러 작업 예약 가능
  - 단일 예약(체크박스)과 다중 스케줄(JSON) 동시 사용 가능
  - 주말 자동 스킵
  - 중복 실행 방지

#### 2. 테스트 옵션 추가
- **새 옵션**: "테스트(로그)"
- **기능**: 실제 작업 없이 로그만 출력
- **사용 사례**:
  ```python
  # 예약이 제대로 작동하는지 확인
  # 실제 빌드 복사/업로드 없이 로그만 확인
  ```

#### 3. 스케줄 관리 개선
- **추가**: "스케쥴 전체삭제" 버튼
- **기능**: `schedule.json`의 모든 스케줄 일괄 삭제
- **UI**: 빨간색 버튼으로 시각적 구분

#### 예제 schedule.json
```json
[
  {
    "time": "08:00",
    "option": "테스트(로그)",
    "buildname": "game_SEL",
    "awsurl": "",
    "branch": ""
  },
  {
    "time": "09:00",
    "option": "클라복사",
    "buildname": "game_dev",
    "awsurl": "",
    "branch": ""
  },
  {
    "time": "10:00",
    "option": "서버업로드및패치",
    "buildname": "game_SEL",
    "awsurl": "https://awsdeploy.pbb-qa.pubg.io/environment/sel-game",
    "branch": "game"
  }
]
```

**자세한 테스트 방법**: `SCHEDULE_TEST_GUIDE.md` 참조

