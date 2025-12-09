"""
QuickBuild 릴리즈 빌드 스크립트
PyInstaller를 사용하여 실행 파일을 생성하고 ZIP으로 패키징합니다.
"""

import os
import sys
import shutil
import zipfile
import json
from pathlib import Path
import subprocess
from datetime import datetime


def load_version_info():
    """version.json에서 버전 정보 로드"""
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  version.json 파일이 없습니다. 기본 버전으로 생성합니다...")
        default_version = {
            'version': '3.0-25.01.01.0000',
            'build_date': datetime.now().strftime("%Y-%m-%d")
        }
        with open('version.json', 'w', encoding='utf-8') as f:
            json.dump(default_version, f, indent=2, ensure_ascii=False)
        return default_version
    except Exception as e:
        print(f"⚠️  버전 정보 로드 실패: {e}")
        return {
            'version': '3.0-25.01.01.0000',
            'build_date': datetime.now().strftime("%Y-%m-%d")
        }


def create_version_file():
    """Windows 버전 정보 파일 생성"""
    version_info = load_version_info()
    version = version_info.get('version', '3.0-25.01.01.0000')
    build_date = version_info.get('build_date', '2025-01-01')
    
    print(f"  버전: {version}")
    print(f"  빌드 날짜: {build_date}")
    
    # 버전 형식: 3.0-yy.mm.dd.hhmm
    # Windows 버전 형식: 3,0,yymmdd,hhmm
    if '-' in version:
        major_minor, date_time = version.split('-')
        major, minor = major_minor.split('.')
        date_time_parts = date_time.split('.')
        
        if len(date_time_parts) >= 4:
            yy, mm, dd, hhmm = date_time_parts[:4]
            yymmdd = f"{yy}{mm}{dd}"
            file_version_parts = [major, minor, yymmdd, hhmm]
        else:
            file_version_parts = ['3', '0', '0', '0']
    else:
        # 레거시 형식 처리
        version_parts = version.split('.')
        while len(version_parts) < 4:
            version_parts.append('0')
        
        file_version_parts = []
        for i, part in enumerate(version_parts[:4]):
            try:
                num = int(part)
                if num > 65535:
                    if i == 0 and num > 2000:
                        num = num % 100  # 2025 → 25
                    else:
                        num = 65535
                file_version_parts.append(str(num))
            except ValueError:
                file_version_parts.append('0')
    
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
        [StringStruct(u'CompanyName', u'PUBG QuickBuild Team'),
        StringStruct(u'FileDescription', u'PUBG QuickBuild - Build Management Tool'),
        StringStruct(u'FileVersion', u'{display_version}'),
        StringStruct(u'InternalName', u'QuickBuild'),
        StringStruct(u'LegalCopyright', u'Copyright 2025'),
        StringStruct(u'OriginalFilename', u'QuickBuild.exe'),
        StringStruct(u'ProductName', u'QuickBuild'),
        StringStruct(u'ProductVersion', u'{display_version}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    print("  ✅ version_info.txt 생성 완료")
    return version


def create_spec_file(version):
    """PyInstaller spec 파일 동적 생성"""
    
    # 포함할 데이터 파일 목록
    datas_list = ["('version.json', '.')"]
    
    # qss 폴더가 있으면 포함
    if os.path.exists('qss'):
        datas_list.append("('qss', 'qss')")
    
    # ico 파일 포함
    if os.path.exists('ico.ico'):
        datas_list.append("('ico.ico', '.')")
    
    datas_str = ",\n        ".join(datas_list)
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['index.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        {datas_str},
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
        'makelog',
        'exporter',
        'updater',
        'packaging',
        'packaging.version',
    ],
    hookspath=['.'],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'distutils',
        'pydoc',
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
'''
    
    with open('QuickBuild_release.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("  ✅ QuickBuild_release.spec 생성 완료")
    return 'QuickBuild_release.spec'


def force_remove_directory(path):
    """강제로 디렉토리 삭제 (Windows 권한 문제 해결)"""
    if not os.path.exists(path):
        return
    
    try:
        # 먼저 일반 삭제 시도
        shutil.rmtree(path, ignore_errors=True)
        
        # 여전히 존재하면 attrib으로 읽기 전용 해제 후 재시도
        if os.path.exists(path):
            print(f"  [INFO] 읽기 전용 속성 제거 중: {path}")
            try:
                subprocess.run(f'attrib -R "{path}\\*" /S /D', shell=True, check=False, 
                             capture_output=True, timeout=10)
            except:
                pass
            
            # 다시 삭제 시도
            shutil.rmtree(path, ignore_errors=True)
        
        # 그래도 존재하면 rd 명령 사용
        if os.path.exists(path):
            print(f"  [INFO] rd 명령으로 삭제 중: {path}")
            try:
                subprocess.run(f'rd /s /q "{path}"', shell=True, check=False,
                             capture_output=True, timeout=10)
            except:
                pass
    except Exception as e:
        print(f"  ⚠️  {path} 완전 삭제 실패: {e}")


def run_pyinstaller(spec_file):
    """PyInstaller 실행"""
    print("\n🔨 PyInstaller 빌드 시작...")
    print(f"  모드: onefile (단일 실행 파일)")
    print(f"  출력: dist/QuickBuild.exe")
    
    # EXE가 이미 존재하면 사용자에게 확인
    exe_path = Path('dist/QuickBuild.exe')
    
    if exe_path.exists():
        print(f"\n  ⚠️  EXE 파일이 이미 존재합니다: {exe_path}")
        response = input("  새로 빌드하시겠습니까? (y/N): ").strip().lower()
        if response != 'y':
            print("  ⏭️  기존 EXE 파일을 사용합니다.")
            return True
    
    # 실행 중인 프로세스 강제 종료
    print("\n  🛑 실행 중인 QuickBuild.exe 프로세스 종료 중...")
    try:
        subprocess.run('taskkill /F /IM QuickBuild.exe', 
                      shell=True, check=False, capture_output=True, timeout=5)
        import time
        time.sleep(2)  # 프로세스 종료 대기
        print("  ✅ 프로세스 종료 완료")
    except Exception as e:
        print(f"  ⚠️  프로세스 종료 실패 (무시): {e}")
    
    # 빌드 폴더 강제 삭제
    print("\n  🧹 빌드 디렉토리 정리 중...")
    for folder in ['build', 'dist']:
        force_remove_directory(folder)
    print("  ✅ 빌드 디렉토리 정리 완료")
    
    # 로그 파일 경로
    log_file = Path('build_pyinstaller.log')
    
    try:
        print("  ⏳ PyInstaller 실행 중 (로그: build_pyinstaller.log)...")
        
        # PyInstaller 환경 변수 설정 (타임아웃 방지)
        env = os.environ.copy()
        env['PYINSTALLER_COMPILE_BOOTLOADER'] = '0'
        env['PYINSTALLER_IGNORE_HOOKSPATH_WARNINGS'] = '1'
        
        # 로그 파일을 열어서 실시간으로 출력 저장
        with open(log_file, 'w', encoding='utf-8', errors='ignore') as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    '-m', 'PyInstaller',
                    '--noconfirm',
                    spec_file
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1,  # 라인 버퍼링
                env=env  # 환경 변수 적용
            )
            
            # 실시간으로 출력 읽기
            for line in process.stdout:
                log.write(line)
                # 중요한 메시지만 화면에 표시
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ['warning', 'error', 'building', 'completed', 'successfully', 'failed']):
                    print(f"  {line.rstrip()}")
            
            # 프로세스 종료 대기
            return_code = process.wait()
        
        if return_code == 0:
            print("\n  ✅ 빌드 완료")
            
            # EXE 파일 확인
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"  📦 생성된 파일: {exe_path.name} ({size_mb:.2f} MB)")
            
            # 로그 파일 삭제 (성공 시)
            try:
                log_file.unlink()
            except:
                pass
            
            return True
        else:
            print(f"\n  ❌ 빌드 실패 (exit code: {return_code})")
            print(f"  📝 자세한 로그: {log_file}")
            return False
        
    except FileNotFoundError:
        print(f"\n  ❌ PyInstaller를 찾을 수 없습니다.")
        print(f"     다음 명령으로 설치하세요: pip install pyinstaller")
        return False
    except Exception as e:
        print(f"\n  ❌ 예상치 못한 오류: {e}")
        print(f"  📝 로그 파일 확인: {log_file}")
        return False


def create_zip_package(version):
    """빌드 결과물을 ZIP으로 패키징"""
    dist_dir = Path('dist')
    exe_file = dist_dir / 'QuickBuild.exe'
    
    if not exe_file.exists():
        print(f"  ❌ {exe_file} 파일을 찾을 수 없습니다!")
        return False
    
    # ZIP 파일명 생성
    zip_filename = f"QuickBuild_{version}.zip"
    zip_path = dist_dir / zip_filename
    
    # ZIP이 이미 존재하면 건너뛰기
    if zip_path.exists():
        print(f"  ⏭️  ZIP이 이미 존재합니다: {zip_path}")
        return True
    
    print(f"\n📦 ZIP 패키징 중: {zip_filename}")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # EXE 파일 추가
            zipf.write(exe_file, 'QuickBuild.exe')
            print(f"  ✅ QuickBuild.exe 추가")
            
            # version.json 추가
            if Path('version.json').exists():
                zipf.write('version.json', 'version.json')
                print(f"  ✅ version.json 추가")
            
            # README 추가 (있는 경우)
            if Path('Readme.md').exists():
                zipf.write('Readme.md', 'Readme.md')
                print(f"  ✅ Readme.md 추가")
        
        print(f"\n  ✅ ZIP 생성 완료: {zip_path}")
        print(f"     파일 크기: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # EXE 파일 삭제 (ZIP만 유지)
        try:
            exe_file.unlink()
            print(f"  ✅ 원본 EXE 파일 정리")
        except Exception as e:
            print(f"  ⚠️  원본 EXE 삭제 실패: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ ZIP 생성 실패: {e}")
        return False


def cleanup():
    """빌드 임시 파일 정리"""
    print("\n🧹 임시 파일 정리 중...")
    
    files_to_remove = [
        'version_info.txt',
        'QuickBuild_release.spec',
        'build_pyinstaller.log',  # 빌드 로그 파일
        'hook-pkg_resources.py',  # PyInstaller 훅 파일
        'hook-win32com.py',  # PyInstaller 훅 파일
    ]
    
    dirs_to_remove = [
        'build'  # PyInstaller 작업 디렉토리
    ]
    
    for file in files_to_remove:
        try:
            if Path(file).exists():
                Path(file).unlink()
                print(f"  ✅ {file} 삭제")
        except Exception as e:
            print(f"  ⚠️  {file} 삭제 실패: {e}")
    
    for dir_name in dirs_to_remove:
        try:
            if Path(dir_name).exists():
                force_remove_directory(dir_name)
                print(f"  ✅ {dir_name}/ 폴더 삭제")
        except Exception as e:
            print(f"  ⚠️  {dir_name}/ 삭제 실패: {e}")
    
    print("  ✅ 정리 완료")


def create_pyinstaller_hooks():
    """PyInstaller 훅 파일 생성 (타임아웃 문제 해결)"""
    
    # hook-pkg_resources.py
    hook_pkg_resources = '''# PyInstaller hook for pkg_resources
# pkg_resources.py2_warn 타임아웃 문제 해결

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# pkg_resources의 필수 서브모듈만 수집
hiddenimports = [
    'pkg_resources.extern',
    'pkg_resources._vendor',
]

# py2_warn 제외 (Python 2 지원 관련, 더 이상 필요 없음)
excludedimports = [
    'pkg_resources.py2_warn',
]

datas = collect_data_files('pkg_resources', include_py_files=True)
'''
    
    # hook-win32com.py
    hook_win32com = '''# PyInstaller hook for win32com
# win32com 타임아웃 문제 해결

from PyInstaller.utils.hooks import exec_statement_rc, get_module_file_attribute
import os

# win32com이 설치되어 있는지 확인하고, 타임아웃 없이 처리
hiddenimports = []
datas = []

# win32com이 실제로 필요한 경우만 처리
try:
    import win32com
    # 필요한 최소한의 모듈만 포함
    hiddenimports = [
        'win32com.client',
        'win32com.client.gencache',
    ]
except ImportError:
    # win32com이 없으면 무시 (선택적 의존성)
    pass
'''
    
    with open('hook-pkg_resources.py', 'w', encoding='utf-8') as f:
        f.write(hook_pkg_resources)
    print("  ✅ hook-pkg_resources.py 생성")
    
    with open('hook-win32com.py', 'w', encoding='utf-8') as f:
        f.write(hook_win32com)
    print("  ✅ hook-win32com.py 생성")


def main():
    """메인 빌드 프로세스"""
    print("=" * 70)
    print("QuickBuild 릴리즈 빌드")
    print("=" * 70)
    
    version_info = load_version_info()
    version = version_info.get('version', '3.0-25.01.01.0000')
    build_date = version_info.get('build_date', datetime.now().strftime("%Y-%m-%d"))
    
    print(f"버전: {version}")
    print(f"빌드 날짜: {build_date}")
    
    # 1. 버전 정보 파일 생성
    print("\n[1/4] 버전 정보 파일 생성 중...")
    create_version_file()
    
    # 2. PyInstaller 훅 파일 생성
    print("\n[2/4] PyInstaller 훅 생성 중...")
    create_pyinstaller_hooks()
    
    # 3. spec 파일 생성
    print("\n[3/4] Spec 파일 생성 중...")
    spec_file = create_spec_file(version)
    
    # 4. PyInstaller 실행
    print("\n[4/4] EXE 빌드 중...")
    if not run_pyinstaller(spec_file):
        print("\n❌ 빌드 실패")
        cleanup()
        sys.exit(1)
    
    # 정리
    print("\n정리 중...")
    cleanup()
    
    print("\n" + "=" * 70)
    print("✅ 빌드 완료!")
    print("=" * 70)
    print(f"📦 버전: {version}")
    print(f"📁 출력 파일: dist/QuickBuild.exe")
    print(f"🗑️  임시 파일: 정리됨 (build/, *.spec, version_info.txt)")
    print("\n다음 단계:")
    print("  python deploy_github.py  # GitHub Release 배포")
    print("=" * 70)


if __name__ == '__main__':
    sys.exit(main())
