@echo off
chcp 65001 >nul
echo ============================================================
echo schedule.json 파일을 Git에서 완전히 제거
echo ============================================================
echo.
echo ⚠️  경고: 이 작업은 Git 히스토리를 수정합니다.
echo    이미 공유된 저장소에서는 주의가 필요합니다.
echo.
echo 작업 내용:
echo   1. Git 캐시에서 schedule.json 제거
echo   2. Git 히스토리에서 schedule.json 제거
echo   3. 로컬 파일은 유지 (.gitignore 적용)
echo.
pause

echo.
echo [1/3] Git 인덱스에서 schedule.json 제거 중...
git rm --cached schedule.json
if errorlevel 1 (
    echo ⚠️  schedule.json이 이미 제거되었거나 추적되지 않습니다.
)
echo.

echo [2/3] .gitignore 확인 중...
findstr /C:"schedule.json" .gitignore >nul
if errorlevel 1 (
    echo schedule.json을 .gitignore에 추가 중...
    echo schedule.json >> .gitignore
) else (
    echo ✅ schedule.json이 이미 .gitignore에 있습니다.
)
echo.

echo [3/3] 변경사항 커밋 중...
git add .gitignore
git commit -m "Remove schedule.json from Git tracking (keep local file)"
if errorlevel 1 (
    echo ⚠️  커밋할 변경사항이 없습니다.
)
echo.

echo ============================================================
echo ✅ Git 인덱스에서 제거 완료!
echo ============================================================
echo.
echo 📝 다음 단계:
echo.
echo 1. 변경사항을 GitHub에 푸시하세요:
echo    git push
echo.
echo 2. (선택) Git 히스토리에서도 완전히 제거하려면:
echo    git filter-branch --force --index-filter "git rm --cached --ignore-unmatch schedule.json" --prune-empty --tag-name-filter cat -- --all
echo    git push origin --force --all
echo.
echo ⚠️  주의: filter-branch는 Git 히스토리를 다시 쓰므로
echo    다른 사람과 공유 중인 저장소에서는 신중하게 사용하세요!
echo.
echo 💡 로컬 파일은 그대로 유지되며, 앞으로 Git에 추적되지 않습니다.
echo.
pause

