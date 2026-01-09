"""
QuickBuild 빌드 스크립트 (Semantic Versioning)
PyInstaller를 사용하여 실행 파일을 생성합니다.
"""

import os
import sys
import shutil
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


def parse_semver(version_str):
    """
    SemVer 문자열을 파싱하여 (major, minor, patch) 반환
    표준 형식: 3.0.0
    """
    try:
        # 표준 SemVer 형식
        parts = version_str.split('.')
        if len(parts) >= 3:
            return int(parts[0]), int(parts[1]), int(parts[2])
        return 3, 0, 0
    except:
        return 3, 0, 0


def load_version_info():
    """version.json에서 버전 정보 로드"""
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  version.json 파일이 없습니다.")
        return None
    except Exception as e:
        print(f"⚠️  버전 정보 로드 실패: {e}")
        return None


def update_version(version_type='patch', changelog_message=None):
    """
    version.json을 Semantic Versioning으로 업데이트
    
    Args:
        version_type: 'major', 'minor', 'patch' 중 하나
        changelog_message: 변경사항 메시지
    
    Returns:
        새 버전 문자열
    """
    # 현재 날짜
    now = datetime.now()
    build_date = now.strftime("%Y-%m-%d")
    
    # 기존 버전 로드
    if os.path.exists('version.json'):
        with open('version.json', 'r', encoding='utf-8') as f:
            version_data = json.load(f)
        current_version = version_data.get('version', '3.0.0')
    else:
        version_data = {}
        current_version = "3.0.0"
    
    print(f"[INFO] 이전 버전: {current_version}")
    
    # 버전 파싱 및 증가
    major, minor, patch = parse_semver(current_version)
    
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
        print(f"🔴 MAJOR 버전 업데이트 (Breaking changes)")
    elif version_type == 'minor':
        minor += 1
        patch = 0
        print(f"🟡 MINOR 버전 업데이트 (New features)")
    else:  # patch
        patch += 1
        print(f"🟢 PATCH 버전 업데이트 (Bug fixes)")
    
    # 표준 SemVer 형식으로 버전 생성: major.minor.patch
    new_version = f"{major}.{minor}.{patch}"
    
    print(f"[INFO] 새 버전: {new_version}")
    
    # version.json 업데이트
    version_data['version'] = new_version
    version_data['build_date'] = build_date
    
    # changelog 추가
    if changelog_message:
        new_changelog = {
            "version": new_version,
            "date": build_date,
            "changes": [changelog_message]
        }
        if 'changelog' not in version_data:
            version_data['changelog'] = []
        version_data['changelog'].insert(0, new_changelog)
    
    # update_url이 없으면 추가
    if 'update_url' not in version_data:
        version_data['update_url'] = "https://api.github.com/repos/SungMinseok/GetBuild/releases/latest"
    
    # 파일 저장
    with open('version.json', 'w', encoding='utf-8') as f:
        json.dump(version_data, f, ensure_ascii=False, indent=2)
    
    print(f"[DONE] version.json 업데이트 완료!")
    
    return new_version


def create_version_file():
    """Windows 버전 정보 파일 생성"""
    print("\n[2/5] Creating version file...")
    
    version_info = load_version_info()
    if not version_info:
        return None
    
    version = version_info.get('version', '3.0.0')
    build_date = version_info.get('build_date', '2025-01-01')
    
    print(f"  버전: {version}")
    print(f"  빌드 날짜: {build_date}")
    
    # 버전 형식: 3.0.0
    # Windows 버전 형식: 3,0,0,0 (4개 필드 필요)
    version_parts = version.split('.')
    while len(version_parts) < 4:
        version_parts.append('0')
    
    file_version_parts = version_parts[:4]
    file_version_str = ','.join(file_version_parts)
    display_version = version
    
    print(f"  Windows 파일 버전: {file_version_str}")
    
    version_info_content = f'''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({file_version_str}),
    prodvers=({file_version_str}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [
          StringStruct(u'CompanyName', u'KRAFTON'),
          StringStruct(u'FileDescription', u'QuickBuild - 스케줄 기반 빌드 관리 도구'),
          StringStruct(u'FileVersion', u'{display_version}'),
          StringStruct(u'InternalName', u'QuickBuild'),
          StringStruct(u'LegalCopyright', u'Copyright (c) 2025 KRAFTON'),
          StringStruct(u'OriginalFilename', u'QuickBuild.exe'),
          StringStruct(u'ProductName', u'QuickBuild'),
          StringStruct(u'ProductVersion', u'{display_version}'),
        ]
      )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    print(f"[DONE] version_info.txt 생성 완료")
    return 'version_info.txt'


def create_spec_file():
    """PyInstaller spec 파일을 동적으로 생성"""
    print("\n[3/5] Creating spec file...")
    
    # QuickBuild.spec 파일 내용 (기존 spec 기반)
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['index.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        ('version.json', '.'),
        ('qss', 'qss'),
        ('ico.ico', '.'),
    ],
    hiddenimports=[
        'pkg_resources',
        'setuptools',
        'selenium', 
        'selenium.webdriver', 
        'selenium.webdriver.chrome', 
        'selenium.webdriver.chrome.options', 
        'selenium.webdriver.common.by', 
        'selenium.webdriver.common.keys', 
        'selenium.webdriver.support', 
        'selenium.webdriver.support.ui', 
        'selenium.webdriver.support.expected_conditions', 
        'selenium.common.exceptions', 
        'chromedriver_autoinstaller',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'core',
        'core.config_manager',
        'core.scheduler',
        'core.build_operations',
        'core.aws_manager',
        'core.worker_thread',
        'ui',
        'ui.schedule_dialog',
        'ui.schedule_item_widget',
        'ui.settings_dialog',
        'makelog',
        'exporter',
        'slack',
        'updater',
        'packaging',
        'packaging.version',
    ],
    hookspath=['.'],  # 현재 디렉토리의 커스텀 hook 사용
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'distutils',
        'pydoc',
        'win32com',
        'win32api',
        'win32con',
        'pythoncom',
        'pywintypes',
        'pywin',
        'pywin32',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QuickBuild',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='ico.ico',
)
"""
    
    with open('QuickBuild.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"[DONE] QuickBuild.spec 생성 완료")
    return 'QuickBuild.spec'


def safe_rmtree(path, max_retries=3):
    """
    Windows에서 안전하게 폴더 삭제
    권한 오류 발생 시 재시도
    """
    import time
    
    for attempt in range(max_retries):
        try:
            if os.path.exists(path):
                # 읽기 전용 속성 제거
                for root, dirs, files in os.walk(path):
                    for d in dirs:
                        try:
                            os.chmod(os.path.join(root, d), 0o777)
                        except:
                            pass
                    for f in files:
                        try:
                            os.chmod(os.path.join(root, f), 0o777)
                        except:
                            pass
                
                # 폴더 삭제
                shutil.rmtree(path, ignore_errors=False)
                return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"  [경고] 폴더 삭제 실패 (재시도 {attempt + 1}/{max_retries}): {path}")
                time.sleep(1)  # 1초 대기 후 재시도
            else:
                print(f"  [경고] 폴더 삭제 실패 (건너뛰기): {path}")
                print(f"  → {e}")
                return False
        except Exception as e:
            print(f"  [경고] 폴더 삭제 중 오류: {e}")
            return False
    
    return False


def clean_pyinstaller_cache():
    """PyInstaller 캐시 정리 (베스트 에포트)"""
    import tempfile
    
    cache_dirs = []
    deleted_count = 0
    skipped_count = 0
    
    # 1. 로컬 캐시
    local_cache = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'pyinstaller')
    if os.path.exists(local_cache):
        cache_dirs.append(local_cache)
    
    # 2. Temp 폴더의 PyInstaller 캐시
    temp_dir = tempfile.gettempdir()
    try:
        for item in os.listdir(temp_dir):
            if item.startswith('_MEI') or item.startswith('pyinstaller'):
                cache_path = os.path.join(temp_dir, item)
                if os.path.isdir(cache_path):
                    cache_dirs.append(cache_path)
    except:
        pass
    
    # 캐시 삭제 (베스트 에포트 - 실패해도 계속 진행)
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir, ignore_errors=True)
            if not os.path.exists(cache_dir):
                deleted_count += 1
            else:
                skipped_count += 1
        except:
            skipped_count += 1
    
    if deleted_count > 0:
        print(f"  ✅ 캐시 {deleted_count}개 삭제")
    if skipped_count > 0:
        print(f"  ℹ️  캐시 {skipped_count}개 건너뛰기 (사용 중)")
    
    if deleted_count == 0 and skipped_count == 0:
        print(f"  ℹ️  정리할 캐시 없음")


def build_exe(spec_file):
    """PyInstaller로 EXE 빌드"""
    print("\n[4/5] Building EXE...")
    
    exe_path = 'dist/QuickBuild.exe'
    
    # 자동 모드 확인
    auto_mode = os.environ.get('BUILD_VERSION_TYPE', '').strip() != ''
    force_rebuild = os.environ.get('BUILD_FORCE_REBUILD', '1') == '1'
    
    # 이미 존재하면 건너뛰기 (선택사항)
    if os.path.exists(exe_path):
        if auto_mode:
            # 자동 모드: 항상 재빌드 (force_rebuild 설정에 따라)
            if force_rebuild:
                print(f"  🤖 자동 모드: 기존 EXE 덮어쓰기")
            else:
                print(f"[SKIP] 기존 EXE 사용: {exe_path}")
                return True
        else:
            # 대화형 모드: 사용자에게 물어보기
            response = input(f"  [!] {exe_path} 파일이 이미 존재합니다. 다시 빌드하시겠습니까? (y/N): ").strip().lower()
            if response != 'y':
                print(f"[SKIP] 기존 EXE 사용: {exe_path}")
                return True
    
    # PyInstaller 캐시 정리
    print("  PyInstaller 캐시 정리 중...")
    clean_pyinstaller_cache()
    
    # 빌드 폴더 정리 (베스트 에포트)
    print("  빌드 폴더 정리 중...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder, ignore_errors=True)
                if not os.path.exists(folder):
                    print(f"  ✅ {folder}/ 폴더 삭제")
                else:
                    # 폴더가 남아있어도 PyInstaller가 덮어쓰므로 문제없음
                    print(f"  ℹ️  {folder}/ 폴더 일부 파일 사용 중 (빌드는 계속 진행)")
            except:
                print(f"  ℹ️  {folder}/ 폴더 정리 건너뛰기")
    
    # PyInstaller 실행
    print(f"  PyInstaller 실행: {spec_file}")
    
    # spec 파일 사용 시에는 --exclude-module 옵션 사용 불가
    # 모든 exclude 설정은 spec 파일에서 처리됨
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        spec_file
    ]
    result = subprocess.run(cmd, check=False, timeout=300)  # 5분 타임아웃
    
    if result.returncode != 0:
        print(f"[ERROR] PyInstaller 실패 (exit code: {result.returncode})")
        return False
    
    # EXE 생성 확인
    if not os.path.exists(exe_path):
        print(f"[ERROR] EXE 파일이 생성되지 않았습니다: {exe_path}")
        return False
    
    print(f"[DONE] EXE 빌드 완료: {exe_path}")
    return True


def clean_build():
    """빌드 임시 파일 정리"""
    print("\n[5/5] Cleaning up...")
    
    # build 폴더만 삭제 (dist는 유지)
    if os.path.exists('build'):
        if safe_rmtree('build'):
            print("  build/ 폴더 삭제")
        else:
            print("  build/ 폴더 삭제 건너뛰기 (수동 삭제 필요)")
    
    # .spec 파일은 유지 (재사용 가능)
    print("[DONE] 정리 완료")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("QuickBuild Build Script (Semantic Versioning)")
    print("=" * 60)
    
    # 환경변수 확인 (deploy.bat 등에서 버전 업데이트 건너뛰기용)
    skip_version_update = os.environ.get('SKIP_VERSION_UPDATE', '0') == '1'
    
    if not skip_version_update:
        print("\n[1/5] Updating version.json...")
        
        # 현재 버전 출력
        version_info = load_version_info()
        if version_info:
            current_version = version_info.get('version', '3.0.0')
            print(f"현재 버전: {current_version}")
        
        # 환경변수에서 버전 타입과 changelog 가져오기 (자동 모드)
        env_version_type = os.environ.get('BUILD_VERSION_TYPE', '').strip()
        env_changelog = os.environ.get('BUILD_CHANGELOG', '').strip()
        
        if env_version_type:
            # 자동 모드 (환경변수 사용)
            print(f"\n🤖 자동 모드: 버전 타입 = {env_version_type}")
            
            if env_version_type == 'test':
                print("\n🔧 테스트 빌드 모드 (버전 변경 없음)")
                version_info = load_version_info()
                if not version_info:
                    print("[ERROR] version.json을 찾을 수 없습니다.")
                    return 1
                new_version = version_info.get('version', '3.0.0')
                skip_version_update = True
            else:
                version_type = env_version_type
                changelog_msg = env_changelog or "버그 수정 및 성능 개선"
                
                print(f"변경사항: {changelog_msg}")
                
                # 버전 업데이트
                try:
                    new_version = update_version(version_type, changelog_msg)
                except Exception as e:
                    print(f"[ERROR] 버전 업데이트 실패: {e}")
                    import traceback
                    traceback.print_exc()
                    return 1
        else:
            # 대화형 모드 (기존 방식)
            # 버전 타입 선택
            print("\n버전 업데이트 타입을 선택하세요:")
            print("  1. PATCH (버그 수정) - 기본값")
            print("  2. MINOR (새 기능 추가)")
            print("  3. MAJOR (Breaking changes)")
            print("  0. 테스트 빌드 (버전 변경 없음)")
            version_choice = input("선택 (0/1/2/3, Enter=1): ").strip()
            
            # 테스트 빌드 옵션 체크
            if version_choice == '0':
                print("\n🔧 테스트 빌드 모드 (버전 변경 없음)")
                version_info = load_version_info()
                if not version_info:
                    print("[ERROR] version.json을 찾을 수 없습니다.")
                    return 1
                new_version = version_info.get('version', '3.0.0')
                skip_version_update = True  # 플래그 설정
            else:
                version_type_map = {
                    '1': 'patch',
                    '2': 'minor',
                    '3': 'major',
                    '': 'patch'
                }
                version_type = version_type_map.get(version_choice, 'patch')
                
                # 변경사항 입력
                print("\n변경사항을 입력하세요 (Enter만 누르면 '버그 수정 및 성능 개선' 사용):")
                changelog_msg = input("> ").strip() or "버그 수정 및 성능 개선"
                
                # 버전 업데이트
                try:
                    new_version = update_version(version_type, changelog_msg)
                except Exception as e:
                    print(f"[ERROR] 버전 업데이트 실패: {e}")
                    import traceback
                    traceback.print_exc()
                    return 1
    else:
        print("\n[1/5] Version update skipped (SKIP_VERSION_UPDATE=1)")
        version_info = load_version_info()
        if not version_info:
            print("[ERROR] version.json을 찾을 수 없습니다.")
            return 1
        new_version = version_info.get('version', '3.0.0')
    
    # Windows 버전 파일 생성
    version_file = create_version_file()
    if not version_file:
        print("[ERROR] 버전 파일 생성 실패")
        return 1
    
    # Spec 파일 생성
    spec_file = create_spec_file()
    if not spec_file:
        print("[ERROR] Spec 파일 생성 실패")
        return 1
    
    # EXE 빌드
    try:
        if not build_exe(spec_file):
            print("\n[ERROR] 빌드 실패!")
            return 1
    except Exception as e:
        print(f"\n[ERROR] 빌드 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 임시 파일 정리
    clean_build()
    
    # 완료 메시지
    print("\n" + "=" * 60)
    print("✅ Build completed successfully!")
    print("=" * 60)
    print(f"Version: {new_version}")
    if skip_version_update:
        print("(테스트 빌드 - 버전 변경 없음)")
    elif 'changelog_msg' in locals():
        print(f"Changelog: {changelog_msg}")
    print(f"EXE: dist/QuickBuild.exe")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] 사용자가 빌드를 취소했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 예기치 않은 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

