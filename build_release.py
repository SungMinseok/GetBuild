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


def load_version_info():
    """version.json에서 버전 정보 로드"""
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ version.json 파일이 없습니다. update_version.py를 먼저 실행하세요.")
        sys.exit(1)


def create_version_file():
    """Windows 버전 정보 파일 생성"""
    version_info = load_version_info()
    version = version_info.get('version', '3.0-25.01.01.0000')
    build_date = version_info.get('build_date', '2025-01-01')
    
    print(f"버전: {version}")
    print(f"빌드 날짜: {build_date}")
    
    # 버전 형식: 3.0-yy.mm.dd.hhmm
    # Windows 버전 형식: 3,0,mmdd,hhmm (각 부분은 0-65535 범위)
    if '-' in version:
        major_minor, date_time = version.split('-')
        major, minor = major_minor.split('.')
        date_time_parts = date_time.split('.')
        
        if len(date_time_parts) >= 4:
            yy, mm, dd, hhmm = date_time_parts[:4]
            # mmdd 형식 사용 (예: 1027) - 65535 이하로 유지
            mmdd = f"{mm}{dd}"
            file_version_parts = [major, minor, mmdd, hhmm]
        else:
            file_version_parts = ['3', '0', '0', '0']
    else:
        file_version_parts = ['3', '0', '0', '0']
    
    file_version_str = ','.join(file_version_parts)
    
    print(f"Windows 파일 버전: {file_version_str}")
    
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
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'QuickBuild'),
        StringStruct(u'LegalCopyright', u'Copyright 2025'),
        StringStruct(u'OriginalFilename', u'QuickBuild.exe'),
        StringStruct(u'ProductName', u'QuickBuild'),
        StringStruct(u'ProductVersion', u'{version}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    print("✅ version_info.txt 생성 완료")
    return version


def create_spec_file(version):
    """PyInstaller spec 파일 동적 생성 (onefile 모드)"""
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['index_v2.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('version.json', '.'),
        ('qss', 'qss'),
        ('ico.ico', '.'),
    ],
    hiddenimports=[
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
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# onefile 모드: 단일 실행 파일만 dist에 생성
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
    icon='ico.ico'
)
'''
    
    with open('QuickBuild_release.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ QuickBuild_release.spec 생성 완료 (onefile 모드)")


def run_pyinstaller():
    """PyInstaller 실행 (onefile 모드)"""
    print("\n🔨 PyInstaller 빌드 시작...")
    print("   모드: onefile (단일 실행 파일)")
    print("   출력: dist/QuickBuild.exe")
    
    try:
        result = subprocess.run(
            [
                'pyinstaller',
                '--clean',
                '--noconfirm',
                '--distpath', 'dist',
                '--workpath', 'build',
                'QuickBuild_release.spec'
            ],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("✅ 빌드 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패:")
        print(e.stdout)
        print(e.stderr)
        return False


def create_zip_package(version):
    """빌드 결과물을 ZIP으로 패키징"""
    dist_dir = Path('dist')
    exe_file = dist_dir / 'QuickBuild.exe'
    
    if not exe_file.exists():
        print(f"❌ {exe_file} 파일을 찾을 수 없습니다!")
        return False
    
    # ZIP 파일명 생성
    zip_filename = f"QuickBuild_{version}.zip"
    zip_path = dist_dir / zip_filename
    
    print(f"\n📦 ZIP 패키징 중: {zip_filename}")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # EXE 파일 추가
            zipf.write(exe_file, 'QuickBuild.exe')
            print(f"  ✓ QuickBuild.exe 추가")
            
            # version.json 추가
            if Path('version.json').exists():
                zipf.write('version.json', 'version.json')
                print(f"  ✓ version.json 추가")
            
            # README 추가 (있는 경우)
            if Path('Readme.md').exists():
                zipf.write('Readme.md', 'Readme.md')
                print(f"  ✓ Readme.md 추가")
        
        print(f"✅ ZIP 생성 완료: {zip_path}")
        print(f"   파일 크기: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # EXE 파일 삭제 (ZIP만 유지)
        exe_file.unlink()
        print(f"✓ 원본 EXE 파일 정리")
        
        return True
        
    except Exception as e:
        print(f"❌ ZIP 생성 실패: {e}")
        return False


def cleanup():
    """빌드 임시 파일 정리"""
    print("\n🧹 임시 파일 정리 중...")
    
    files_to_remove = [
        'version_info.txt',
        'QuickBuild_release.spec'
    ]
    
    dirs_to_remove = [
        'build'  # PyInstaller 작업 디렉토리 (임시 파일)
    ]
    
    for file in files_to_remove:
        try:
            if Path(file).exists():
                Path(file).unlink()
                print(f"  ✓ {file} 삭제")
        except Exception as e:
            print(f"  ⚠ {file} 삭제 실패: {e}")
    
    for dir_name in dirs_to_remove:
        try:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)
                print(f"  ✓ {dir_name}/ 폴더 삭제")
        except Exception as e:
            print(f"  ⚠ {dir_name}/ 삭제 실패: {e}")
    
    print("✅ 정리 완료")


def main():
    """메인 빌드 프로세스"""
    print("=" * 60)
    print("QuickBuild 릴리즈 빌드 (onefile 모드)")
    print("=" * 60)
    
    # 1. 버전 정보 로드 및 파일 생성
    version = create_version_file()
    
    # 2. spec 파일 생성
    create_spec_file(version)
    
    # 3. PyInstaller 실행
    if not run_pyinstaller():
        print("\n❌ 빌드 실패")
        cleanup()  # 실패해도 임시 파일 정리
        sys.exit(1)
    
    # 4. ZIP 패키징
    if not create_zip_package(version):
        print("\n❌ 패키징 실패")
        cleanup()  # 실패해도 임시 파일 정리
        sys.exit(1)
    
    # 5. 정리
    cleanup()
    
    print("\n" + "=" * 60)
    print("✅ 빌드 완료!")
    print("=" * 60)
    print(f"📦 버전: {version}")
    print(f"📁 출력 파일: dist/QuickBuild_{version}.zip")
    print(f"🗑️  임시 파일: 정리됨 (build/, *.spec, version_info.txt)")
    print("\n다음 단계:")
    print("  python deploy_github.py  # GitHub Release 배포")
    print("=" * 60)


if __name__ == '__main__':
    main()

