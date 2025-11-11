# Chrome 버전 불일치 오류 해결 방법

## 오류 메시지
```
This version of ChromeDriver only supports Chrome version 142
Current browser version is 135.0.7049.117
```

## 원인
ChromeDriver와 Chrome 브라우저의 버전이 일치하지 않아 발생하는 문제입니다.

## 해결 방법 (추천)

### 1. Chrome for Testing 다운로드

ChromeDriver와 정확히 일치하는 버전의 Chrome을 다운로드하세요.

#### 다운로드 사이트
https://googlechromelabs.github.io/chrome-for-testing/

#### 다운로드할 파일
- **chrome-win64.zip** (Windows 64-bit용)
- 현재 ChromeDriver 버전과 **동일한 버전** 선택 (예: 142.x.xxxx.xx)

### 2. 파일 배치

다운로드한 `chrome-win64.zip`을 다음 경로에 압축 해제:

```
프로그램폴더/
├── 142/                         # ChromeDriver 버전 폴더
│   ├── chromedriver.exe        # ChromeDriver
│   └── chrome-win64/           # 압축 해제한 Chrome
│       ├── chrome.exe          ← 이 파일이 필요합니다
│       └── ... (기타 파일들)
```

**예시**:
```
C:\Users\mssung\OneDrive - KRAFTON\PyProject\GetBuild_clean\142\chrome-win64\chrome.exe
```

### 3. 프로그램 재실행

파일을 올바른 위치에 배치한 후 프로그램을 다시 실행하면 자동으로 Chrome for Testing을 사용합니다.

## 작동 방식

프로그램은 다음 순서로 Chrome을 찾습니다:

1. **Chrome for Testing (우선)**: `142/chrome-win64/chrome.exe`
   - ChromeDriver와 버전이 정확히 일치
   - ✅ **오류 없이 작동**

2. **시스템 Chrome (백업)**: `C:\Program Files\Google\Chrome\Application\chrome.exe`
   - 버전이 다를 수 있음
   - ⚠️ 버전 불일치 시 오류 발생

## 빠른 다운로드 링크 (2024년 기준)

최신 안정 버전:
- https://googlechromelabs.github.io/chrome-for-testing/#stable

특정 버전 찾기:
- https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json

## 참고사항

- Chrome for Testing은 시스템에 설치된 일반 Chrome과 **독립적**으로 실행됩니다
- 북마크, 설정, 확장 프로그램이 공유되지 않습니다
- 테스트/자동화 전용입니다
- 시스템 Chrome은 영향을 받지 않습니다

## 문제 해결

### "Chrome for Testing을 찾을 수 없습니다"
- `chrome-win64` 폴더가 ChromeDriver와 같은 폴더에 있는지 확인
- `chrome.exe` 파일이 `chrome-win64` 폴더 안에 있는지 확인

### "ChromeDriver를 찾을 수 없습니다"
- ChromeDriver가 버전 번호 폴더 안에 있는지 확인 (예: `142/chromedriver.exe`)

### 여전히 버전 오류 발생
1. Chrome 프로세스 강제 종료:
   ```
   taskkill /F /IM chrome.exe /T
   taskkill /F /IM chromedriver.exe /T
   ```
2. 프로그램 재시작




