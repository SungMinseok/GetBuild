"""AWS 배포 관련 작업 모듈 (기존 aws.py 정리 버전)"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import subprocess
import time
import requests
import re
import os
import sys
import zipfile
import shutil
import psutil
from exporter import export_upload_result


class AWSManager:
    """AWS 배포 관련 작업 관리"""
    
    # ChromeDriver 관련 상수
    CHROME_USER_DATA_DIR = r'C:\ChromeTEMP'
    CHROME_DEBUGGING_PORT = 9222
    
    @staticmethod
    def teamcity_auto_login(driver, teamcity_id: str = '', teamcity_pw: str = ''):
        """
        Teamcity 자동 로그인 시도
        
        Args:
            driver: Selenium WebDriver
            teamcity_id: Teamcity 아이디
            teamcity_pw: Teamcity 비밀번호
        
        Returns:
            bool: 로그인 성공 여부
        """
        try:
            # 로그인 정보가 없으면 스킵
            if not teamcity_id or not teamcity_pw:
                print("[Teamcity 로그인] 로그인 정보가 없습니다. 스킵합니다.")
                return False
            
            # 로그인 페이지가 있는지 확인
            wait = WebDriverWait(driver, 5)
            
            # ID 입력란 찾기
            try:
                print("[Teamcity 로그인] 로그인 페이지 감지됨. 자동 로그인 시도...")
                id_input = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '/html/body/div[1]/div/div/div[2]/form/div[1]/input')
                ))
                
                # ID 입력
                print(f"[Teamcity 로그인] ID 입력: {teamcity_id}")
                id_input.clear()
                id_input.send_keys(teamcity_id)
                time.sleep(0.5)
                
                # 비밀번호 입력
                pw_input = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[2]/form/div[2]/input')
                print("[Teamcity 로그인] 비밀번호 입력")
                pw_input.clear()
                pw_input.send_keys(teamcity_pw)
                time.sleep(0.5)
                
                # 로그인 버튼 클릭
                login_button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[2]/form/div[4]/input')
                print("[Teamcity 로그인] 로그인 버튼 클릭")
                AWSManager._safe_click(driver, login_button)
                
                # 로그인 완료 대기 (페이지 로드)
                time.sleep(3)
                print("[Teamcity 로그인] ✅ 자동 로그인 완료")
                return True
                
            except TimeoutException:
                # 로그인 페이지가 없음 (이미 로그인됨)
                print("[Teamcity 로그인] 로그인 페이지가 없습니다. (이미 로그인된 상태)")
                return True
            except Exception as e:
                print(f"[Teamcity 로그인] ⚠️ 자동 로그인 실패: {e}")
                return False
        
        except Exception as e:
            print(f"[Teamcity 로그인] ⚠️ 로그인 시도 중 오류: {e}")
            return False
    
    @staticmethod
    def wait_for_teamcity_page_ready(driver, url_link: str, timeout: int = 30):
        """
        TeamCity 페이지 이동/리다이렉트 이후, 실제 페이지가 로드되었는지 확인.
        - driver가 이미 존재하는 경우에도 url 이동이 누락되어 다음 단계로 넘어가는 문제를 방지한다.
        """
        expected_base = url_link.split('#')[0].split('?')[0].rstrip('/')
        wait = WebDriverWait(driver, timeout)

        # URL이 기대하는 base로 이동했는지(혹은 그 하위로) 확인
        try:
            wait.until(lambda d: expected_base in (d.current_url or ""))
        except TimeoutException:
            raise Exception(
                f"[빌드굽기] ❌ URL 이동 실패: {expected_base} 로 이동하지 못했습니다. 현재 URL: {driver.current_url}"
            )

        # 문서 로드 완료 확인
        try:
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            raise Exception(
                f"[빌드굽기] ❌ 페이지 로딩 완료 대기 실패(document.readyState). 현재 URL: {driver.current_url}"
            )

        # TeamCity 빌드 페이지의 핵심 컨테이너가 존재하는지 확인
        try:
            wait.until(EC.presence_of_element_located((By.ID, "main-content-tag")))
        except TimeoutException:
            raise Exception(
                f"[빌드굽기] ❌ TeamCity 빌드 페이지 확인 실패(main-content-tag). 현재 URL: {driver.current_url}"
            )

    @staticmethod
    def get_base_path():
        """실행 파일 기준 경로 반환"""
        if getattr(sys, 'frozen', False):
            # 실행 파일로 실행 중
            return os.path.dirname(sys.executable)
        else:
            # 스크립트로 실행 중
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @staticmethod
    def get_driver_dir():
        """driver 폴더 경로 반환 (없으면 생성)"""
        base_path = AWSManager.get_base_path()
        driver_dir = os.path.join(base_path, 'driver')
        if not os.path.exists(driver_dir):
            os.makedirs(driver_dir)
            print(f"[get_driver_dir] driver 폴더 생성: {driver_dir}")
        return driver_dir

    @staticmethod
    def get_chrome_version():
        """시스템에 설치된 Chrome 버전 확인

        Returns:
            str: Chrome 버전 문자열 (예: "131.0.6778.86") 또는 None
        """
        chrome_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
        ]

        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                try:
                    # wmic 명령어로 버전 확인
                    escaped_path = chrome_path.replace('\\', '\\\\')
                    result = subprocess.run(
                        ['wmic', 'datafile', 'where', f'name="{escaped_path}"', 'get', 'Version', '/value'],
                        capture_output=True, text=True, timeout=10
                    )
                    for line in result.stdout.split('\n'):
                        if 'Version=' in line:
                            version = line.split('=')[1].strip()
                            if version:
                                print(f"[get_chrome_version] 시스템 Chrome 버전: {version}")
                                return version
                except Exception as e:
                    print(f"[get_chrome_version] 버전 확인 실패: {e}")

        print("[get_chrome_version] Chrome을 찾을 수 없습니다.")
        return None

    @staticmethod
    def get_chromedriver_major_version(chromedriver_path):
        """ChromeDriver 경로에서 메이저 버전 추출

        Args:
            chromedriver_path: ChromeDriver 실행 파일 경로

        Returns:
            str: 메이저 버전 (예: "144") 또는 None
        """
        try:
            version_str = os.path.basename(os.path.dirname(chromedriver_path))
            return version_str.split('.')[0]
        except:
            return None

    @staticmethod
    def is_chromedriver_compatible():
        """현재 ChromeDriver가 Chrome과 호환되는지 확인

        Chrome과 ChromeDriver는 메이저 버전이 일치해야 함
        예: Chrome 144.x.x.x → ChromeDriver 144.x.x.x 필요

        Returns:
            tuple: (is_compatible: bool, chrome_version: str, driver_version: str, chromedriver_path: str)
        """
        chrome_version = AWSManager.get_chrome_version()
        if not chrome_version:
            return (True, None, None, None)  # Chrome 버전 확인 불가 시 호환 가정

        chrome_major = chrome_version.split('.')[0]

        try:
            chromedriver_path = AWSManager.get_chromedriver_path()
            driver_version = os.path.basename(os.path.dirname(chromedriver_path))
            driver_major = driver_version.split('.')[0]

            is_compatible = (driver_major == chrome_major)
            print(f"[is_chromedriver_compatible] Chrome: {chrome_major}, ChromeDriver: {driver_major}, 호환: {is_compatible}")
            return (is_compatible, chrome_version, driver_version, chromedriver_path)
        except FileNotFoundError:
            return (False, chrome_version, None, None)  # ChromeDriver 없음

    @staticmethod
    def cleanup_old_chromedrivers(keep_version=None, progress_callback=None):
        """구버전 ChromeDriver 폴더 삭제

        Args:
            keep_version: 유지할 버전 (None이면 모두 삭제)
            progress_callback: 진행 상황 콜백 함수

        Returns:
            list: 삭제된 버전 목록
        """
        def log(msg):
            print(msg)
            if progress_callback:
                progress_callback(msg)

        driver_dir = AWSManager.get_driver_dir()
        deleted_versions = []
        failed_versions = []

        if not os.path.exists(driver_dir):
            return deleted_versions

        # 삭제 전 ChromeDriver 프로세스 종료 시도
        log("[cleanup] ChromeDriver 프로세스 종료 시도...")
        AWSManager.kill_all_chromedrivers()
        time.sleep(1)  # 프로세스 종료 대기

        for item in os.listdir(driver_dir):
            item_path = os.path.join(driver_dir, item)
            if os.path.isdir(item_path):
                # 유지할 버전이 아니면 삭제
                if keep_version is None or item != keep_version:
                    try:
                        # 먼저 파일 권한 문제 해결 시도
                        for root, dirs, files in os.walk(item_path):
                            for f in files:
                                try:
                                    os.chmod(os.path.join(root, f), 0o777)
                                except:
                                    pass
                        shutil.rmtree(item_path)
                        deleted_versions.append(item)
                        log(f"[cleanup] 구버전 삭제됨: {item}")
                    except PermissionError as e:
                        failed_versions.append(item)
                        log(f"[cleanup] 삭제 실패 ({item}): 파일 사용 중 - 수동 삭제 필요")
                    except Exception as e:
                        failed_versions.append(item)
                        log(f"[cleanup] 삭제 실패 ({item}): {e}")

        if deleted_versions:
            log(f"[cleanup] {len(deleted_versions)}개 구버전 삭제 완료")
        if failed_versions:
            log(f"[cleanup] {len(failed_versions)}개 삭제 실패 (수동 삭제 필요: {', '.join(failed_versions)})")
        if not deleted_versions and not failed_versions:
            log("[cleanup] 삭제할 구버전 없음")

        return deleted_versions
    
    @staticmethod
    def download_latest_chromedriver(progress_callback=None):
        """최신 ChromeDriver 다운로드 및 설치 (chromedriver_autoinstaller 사용)

        - 시스템 Chrome 버전에 맞는 ChromeDriver 자동 다운로드
        - 설치 성공 시 구버전 자동 삭제
        - chromedriver_autoinstaller 캐시 무시하고 강제 재설치

        Args:
            progress_callback: 진행 상황 콜백 함수 (message: str) -> None

        Returns:
            str: 설치된 ChromeDriver 경로
        """
        def log(msg):
            print(msg)
            if progress_callback:
                progress_callback(msg)

        try:
            log("[ChromeDriver 다운로드] 시작...")

            # 0. 먼저 모든 ChromeDriver 프로세스 종료
            log("[0/5] ChromeDriver 프로세스 종료 중...")
            killed = AWSManager.kill_all_chromedrivers()
            if killed > 0:
                log(f"[0/5] {killed}개 ChromeDriver 프로세스 종료됨")
                time.sleep(2)  # 프로세스 완전 종료 대기

            # 1. 시스템 Chrome 버전 확인
            chrome_version = AWSManager.get_chrome_version()
            if chrome_version:
                log(f"[1/5] 시스템 Chrome 버전: {chrome_version}")
            else:
                log("[1/5] [경고] 시스템 Chrome 버전을 확인할 수 없습니다.")

            import chromedriver_autoinstaller

            # 2. chromedriver_autoinstaller 캐시 삭제하여 강제 재설치
            log("[2/5] chromedriver_autoinstaller 캐시 확인 중...")
            try:
                # chromedriver_autoinstaller의 캐시 경로 확인 및 삭제
                import chromedriver_autoinstaller.utils as cda_utils
                chrome_major_version = cda_utils.get_chrome_version()
                if chrome_major_version:
                    log(f"[2/5] Chrome 메이저 버전: {chrome_major_version}")
                    # 캐시 폴더 삭제하여 강제 재다운로드
                    cda_cache_path = os.path.join(os.path.dirname(chromedriver_autoinstaller.__file__), chrome_major_version)
                    if os.path.exists(cda_cache_path):
                        shutil.rmtree(cda_cache_path)
                        log(f"[2/5] 캐시 삭제됨: {cda_cache_path}")
            except Exception as cache_err:
                log(f"[2/5] 캐시 삭제 건너뜀: {cache_err}")

            # driver 폴더를 chromedriver 설치 경로로 지정
            driver_dir = AWSManager.get_driver_dir()

            # 3. ChromeDriver 다운로드 및 설치
            log("[3/5] ChromeDriver 다운로드 및 설치 중...")
            installed_path = chromedriver_autoinstaller.install(cwd=True)

            if not installed_path or not os.path.exists(installed_path):
                raise Exception("ChromeDriver 자동 설치 실패")

            log(f"[3/5] ChromeDriver 설치됨: {installed_path}")

            # 버전 정보 추출 (경로에서)
            # 예: C:\Users\...\131.0.6778.86\chromedriver.exe
            installed_dir = os.path.dirname(installed_path)
            version = os.path.basename(installed_dir)

            # driver 폴더로 복사
            target_dir = os.path.join(driver_dir, version)
            final_driver_path = os.path.join(target_dir, 'chromedriver.exe')

            # 4. 동일 버전 폴더가 있으면 확인
            need_copy = True
            if os.path.exists(target_dir):
                if os.path.exists(final_driver_path):
                    log(f"[4/5] 동일 버전 이미 존재, 기존 파일 사용: {target_dir}")
                    need_copy = False
                else:
                    # 폴더는 있지만 chromedriver.exe가 없는 경우 삭제 후 재설치
                    log(f"[4/5] 동일 버전 폴더 불완전, 재설치 시도: {target_dir}")
                    deleted = False
                    for retry in range(3):
                        try:
                            shutil.rmtree(target_dir)
                            deleted = True
                            break
                        except PermissionError:
                            if retry < 2:
                                log(f"[4/5] 삭제 실패, 재시도 중... ({retry + 1}/3)")
                                AWSManager.kill_all_chromedrivers()
                                time.sleep(2)
                            else:
                                log(f"[4/5] 삭제 실패")

                    if not deleted:
                        # 삭제 실패해도 폴더 안에 직접 파일 복사 시도
                        log(f"[4/5] 폴더 삭제 실패, 파일 직접 복사 시도")
                        try:
                            src_exe = os.path.join(installed_dir, 'chromedriver.exe')
                            shutil.copy2(src_exe, final_driver_path)
                            need_copy = False
                            log(f"[4/5] chromedriver.exe 직접 복사 완료")
                        except Exception as e:
                            log(f"[4/5] 직접 복사 실패: {e}")
                            raise Exception(f"ChromeDriver 설치 실패: {target_dir} 폴더 삭제/복사 불가")

            if need_copy:
                log(f"[4/5] driver 폴더로 복사: {target_dir}")
                shutil.copytree(installed_dir, target_dir)

            # 5. 구버전 자동 삭제
            log("[5/5] 구버전 ChromeDriver 정리 중...")
            deleted_versions = AWSManager.cleanup_old_chromedrivers(keep_version=version, progress_callback=progress_callback)

            # 루트 폴더의 chromedriver 캐시 폴더도 정리 (chromedriver_autoinstaller가 생성한 폴더)
            base_path = AWSManager.get_base_path()
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path) and item.isdigit():
                    # chromedriver.exe가 있는 폴더만 삭제 (chromedriver 캐시 폴더)
                    if os.path.exists(os.path.join(item_path, 'chromedriver.exe')):
                        try:
                            shutil.rmtree(item_path)
                            log(f"[정리] 루트 캐시 삭제됨: {item}")
                        except Exception as e:
                            log(f"[정리] 루트 캐시 삭제 실패 ({item}): 수동 삭제 필요")

            log(f"[완료] ChromeDriver 설치 완료!")
            log(f"   버전: {version}")
            log(f"   경로: {final_driver_path}")
            if deleted_versions:
                log(f"   삭제된 구버전: {', '.join(deleted_versions)}")

            return final_driver_path

        except Exception as e:
            error_msg = f"[실패] ChromeDriver 다운로드 실패: {e}"
            log(error_msg)
            raise Exception(error_msg)
    
    @staticmethod
    def kill_all_chromedrivers():
        """모든 ChromeDriver 프로세스 강제 종료
        
        Returns:
            int: 종료된 프로세스 수
        """
        killed_count = 0
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = (proc.info.get('name') or proc.name() or '')
                    if not proc_name:
                        continue
                    if 'chromedriver' in proc_name.lower():
                        proc.kill()
                        killed_count += 1
                        print(f"[kill_chromedrivers] 종료: PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError, TypeError):
                    pass
            
            if killed_count > 0:
                print(f"[kill_chromedrivers] 총 {killed_count}개의 ChromeDriver 프로세스 종료")
                
        except Exception as e:
            print(f"[kill_chromedrivers] 오류: {e}")
        
        return killed_count
    
    @staticmethod
    def clear_chrome_cache():
        """Chrome 사용자 데이터 디렉터리 삭제
        
        Returns:
            bool: 성공 여부
        """
        try:
            cache_dir = AWSManager.CHROME_USER_DATA_DIR
            
            if not os.path.exists(cache_dir):
                print(f"[clear_cache] 캐시 디렉터리 없음: {cache_dir}")
                return True
            
            # Chrome 프로세스 종료 확인
            chrome_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    chrome_running = True
                    print(f"[clear_cache] 경고: Chrome 실행 중 (PID: {proc.info['pid']})")
            
            if chrome_running:
                raise Exception("Chrome이 실행 중입니다. 먼저 Chrome을 종료해주세요.")
            
            # 캐시 디렉터리 삭제
            print(f"[clear_cache] 캐시 삭제 중: {cache_dir}")
            shutil.rmtree(cache_dir)
            print("[clear_cache] ✅ 캐시 삭제 완료")
            
            return True
            
        except Exception as e:
            error_msg = f"[clear_cache] ❌ 캐시 삭제 실패: {e}"
            print(error_msg)
            raise Exception(error_msg)
    
    @staticmethod
    def get_chromedriver_path():
        """현재 실행 파일 경로 기준으로 ChromeDriver 찾기
        
        우선순위:
        1. driver 폴더 내 버전별 폴더 (예: driver/131.0.6778.86/chromedriver.exe)
        2. 루트 폴더 내 버전별 폴더 (예: 141/chromedriver.exe) - 하위 호환성
        """
        base_path = AWSManager.get_base_path()
        chrome_driver_dirs = []
        
        # 1. driver 폴더 확인 (우선순위 1)
        driver_dir = os.path.join(base_path, 'driver')
        if os.path.exists(driver_dir):
            for item in os.listdir(driver_dir):
                item_path = os.path.join(driver_dir, item)
                if os.path.isdir(item_path):
                    driver_exe = os.path.join(item_path, 'chromedriver.exe')
                    if os.path.isfile(driver_exe):
                        # 버전 문자열을 숫자로 변환 (예: "131.0.6778.86" -> 131006778086)
                        try:
                            version_parts = item.split('.')
                            version_number = int(''.join(part.zfill(3) for part in version_parts))
                            chrome_driver_dirs.append((version_number, driver_exe, item))
                        except:
                            # 버전 파싱 실패 시 0으로 처리
                            chrome_driver_dirs.append((0, driver_exe, item))
        
        # 2. 루트 폴더 내 숫자 폴더 확인 (하위 호환성 - 낮은 우선순위)
        # driver 폴더가 우선이므로, 루트 폴더의 버전은 더 낮은 우선순위 부여
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path) and item.isdigit():
                driver_exe = os.path.join(item_path, 'chromedriver.exe')
                if os.path.isfile(driver_exe):
                    # 하위 호환성용 - driver 폴더보다 낮은 우선순위
                    version_number = int(item)  # 단순 버전 번호만 사용
                    chrome_driver_dirs.append((version_number, driver_exe, item))
        
        if chrome_driver_dirs:
            # 버전 번호가 가장 높은 것 사용
            chrome_driver_dirs.sort(reverse=True)
            chromedriver_path = chrome_driver_dirs[0][1]
            version_str = chrome_driver_dirs[0][2]
            print(f"[get_chromedriver_path] ChromeDriver 발견: {chromedriver_path} (버전: {version_str})")
            return chromedriver_path
        else:
            error_msg = f"""ChromeDriver를 찾을 수 없습니다.

해결 방법:
1. Settings 메뉴에서 'ChromeDriver 자동 다운로드' 실행
2. 수동 설치: {base_path}\\driver 폴더에 버전별 폴더를 만들고 chromedriver.exe를 넣어주세요.
   예: {base_path}\\driver\\131.0.6778.86\\chromedriver.exe"""
            raise FileNotFoundError(error_msg)
    
    @staticmethod
    def find_chrome_for_testing(chromedriver_path):
        """ChromeDriver와 같은 버전의 Chrome for Testing 찾기"""
        # ChromeDriver가 있는 폴더에서 Chrome 찾기
        chromedriver_dir = os.path.dirname(chromedriver_path)
        
        # 가능한 Chrome 경로들
        chrome_paths = [
            os.path.join(chromedriver_dir, 'chrome-win64', 'chrome.exe'),
            os.path.join(chromedriver_dir, 'chrome', 'chrome.exe'),
            os.path.join(chromedriver_dir, 'chrome.exe'),
        ]
        
        for path in chrome_paths:
            if os.path.isfile(path):
                print(f"[find_chrome_for_testing] Chrome for Testing 발견: {path}")
                return path
        
        return None
    
    @staticmethod
    def kill_chrome_on_debug_port(port=9222):
        """포트를 사용하는 Chrome 프로세스만 종료 (앱 전용 C:\\ChromeTEMP 인스턴스)
        
        사용자 Chrome은 건드리지 않고, 앱 전용 디버깅 포트의 Chrome만 종료
        """
        killed_count = 0
        try:
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0 or not result.stdout:
                return killed_count
            
            pids_to_kill = set()
            for line in result.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[-1].isdigit():
                    pids_to_kill.add(int(parts[-1]))
            
            for pid in pids_to_kill:
                try:
                    proc = psutil.Process(pid)
                    if proc.name() and 'chrome' in proc.name().lower():
                        proc.kill()
                        killed_count += 1
                        print(f"[kill_chrome_on_debug_port] 포트 {port} Chrome 종료: PID {pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if killed_count > 0:
                print(f"[kill_chrome_on_debug_port] 총 {killed_count}개 프로세스 종료")
        except Exception as e:
            print(f"[kill_chrome_on_debug_port] 오류 (무시): {e}")
        
        return killed_count
    
    @staticmethod
    def cleanup_chrome_processes():
        """ChromeDriver 프로세스만 종료 (사용자 Chrome은 유지하여 작업 손실 방지)"""
        print("[cleanup_chrome_processes] ChromeDriver 프로세스 정리 중...")
        
        killed = AWSManager.kill_all_chromedrivers()
        if killed > 0:
            print("[cleanup_chrome_processes] 프로세스 종료 대기 중 (3초)...")
            time.sleep(3)
        
        print("[cleanup_chrome_processes] ✅ 정리 완료")
    
    @staticmethod
    def _scroll_into_view(driver, element):
        """요소를 뷰포트 내로 스크롤 (화면 쏠림 시 요소 미노출 방지)"""
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
            time.sleep(0.2)
        except Exception:
            pass

    @staticmethod
    def _safe_click(driver, element):
        """JS 클릭 - 모니터 꺼짐/해상도 변경/원격접속 환경에서도 뷰포트와 무관하게 동작"""
        driver.execute_script("arguments[0].click();", element)
    
    _AWS_DEPLOY_SOCIAL_OIDC_XPATH = '//*[@id="social-oidc"]'
    
    @staticmethod
    def _ensure_aws_deploy_social_oidc_clicked(driver, log_prefix: str, wait_sec: int = 15):
        """AWS 배포 페이지에서 OIDC 로그인 버튼이 보이면 클릭해야만 진행한다.
        클릭 실패를 bare except로 '이미 로그인' 처리하지 않는다."""
        xpath = AWSManager._AWS_DEPLOY_SOCIAL_OIDC_XPATH
        wait = WebDriverWait(driver, wait_sec)
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
        except TimeoutException:
            print(f"{log_prefix} OIDC 로그인 버튼 없음 (이미 로그인된 상태로 간주)")
            return
        
        print(f"{log_prefix} 로그인 확인 중... (OIDC 버튼 클릭)")
        time.sleep(0.5)
        last_error = None
        for attempt in range(10):
            try:
                buttons = driver.find_elements(By.XPATH, xpath)
                if not buttons:
                    print(f"{log_prefix} OIDC 버튼 제거됨 → 로그인 플로우 진행")
                    return
                btn = buttons[0]
                if not btn.is_displayed():
                    print(f"{log_prefix} OIDC 버튼 비표시 → 로그인 플로우 진행")
                    return
                AWSManager._scroll_into_view(driver, btn)
                btn = driver.find_element(By.XPATH, xpath)
                AWSManager._safe_click(driver, btn)
                print(f"{log_prefix} 로그인 버튼 클릭 완료")
                time.sleep(2)
                return
            except StaleElementReferenceException:
                last_error = None
                time.sleep(0.35)
                continue
            except TimeoutException as e:
                last_error = e
                try:
                    buttons = driver.find_elements(By.XPATH, xpath)
                    if not buttons:
                        print(f"{log_prefix} OIDC 버튼 대기 중 사라짐 → 로그인 플로우 진행")
                        return
                    if not buttons[0].is_displayed():
                        print(f"{log_prefix} OIDC 버튼 비표시 → 로그인 플로우 진행")
                        return
                except StaleElementReferenceException:
                    pass
                time.sleep(0.5)
                continue
            except Exception as e:
                last_error = e
                if attempt >= 6:
                    try:
                        btn = driver.find_element(By.XPATH, xpath)
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"{log_prefix} 로그인 버튼 JS 클릭 완료")
                            time.sleep(2)
                            return
                    except Exception as js_e:
                        last_error = js_e
                time.sleep(0.5)
        
        raise Exception(
            f"{log_prefix} OIDC 로그인 버튼(#social-oidc) 클릭 실패. "
            f"페이지 로드·팝업 차단·수동 로그인 여부를 확인하세요. 마지막 오류: {last_error}"
        )
    
    _KEYCLOAK_HOST = "keycloak.pbb-qa.pubg.io"
    _KEYCLOAK_KRAFTON_XPATH = "/html/body/div/div/main/div[2]/div[2]/div[2]/ul/li/a"

    @staticmethod
    def _ensure_keycloak_login(driver, log_prefix: str, wait_sec: int = 10):
        """Keycloak 로그인 페이지가 감지되면 'Sign in through KRAFTON' 버튼을 클릭한다."""
        try:
            current_url = driver.current_url
        except Exception:
            return

        if AWSManager._KEYCLOAK_HOST not in current_url:
            print(f"{log_prefix} Keycloak 로그인 페이지 아님 (이미 로그인된 상태)")
            return

        print(f"{log_prefix} Keycloak 로그인 페이지 감지됨. 'Sign in through KRAFTON' 클릭 시도...")
        xpath = AWSManager._KEYCLOAK_KRAFTON_XPATH
        wait = WebDriverWait(driver, wait_sec)
        try:
            btn = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            AWSManager._scroll_into_view(driver, btn)
            AWSManager._safe_click(driver, btn)
            print(f"{log_prefix} 'Sign in through KRAFTON' 클릭 완료")
            # 로그인 후 리다이렉트 대기
            time.sleep(3)
            # keycloak 호스트에서 벗어날 때까지 대기 (최대 30초)
            for _ in range(30):
                try:
                    if AWSManager._KEYCLOAK_HOST not in driver.current_url:
                        print(f"{log_prefix} Keycloak 로그인 완료, 원래 페이지로 리다이렉트됨")
                        time.sleep(2)
                        return
                except Exception:
                    pass
                time.sleep(1)
            print(f"{log_prefix} ⚠️ Keycloak 리다이렉트 대기 타임아웃 (30초). 계속 진행합니다.")
        except TimeoutException:
            raise Exception(
                f"{log_prefix} Keycloak 'Sign in through KRAFTON' 버튼을 찾을 수 없습니다. "
                f"페이지 구조가 변경되었을 수 있습니다. XPath: {xpath}"
            )
        except Exception as e:
            raise Exception(
                f"{log_prefix} Keycloak 로그인 처리 중 오류: {e}"
            )

    @staticmethod
    def _ensure_work_tab(driver):
        """새 탭을 열고 포커스를 그 탭으로 고정 (이후 driver.get 등은 항상 새 탭에서 수행)"""
        handles_before = set(driver.window_handles)
        tab_ok = False
        try:
            from selenium.webdriver.common.window import WindowTypes
            driver.switch_to.new_window(WindowTypes.TAB)
            tab_ok = True
        except Exception:
            try:
                if hasattr(driver.switch_to, 'new_window'):
                    driver.switch_to.new_window('tab')
                    tab_ok = True
            except Exception:
                tab_ok = False
        if not tab_ok:
            driver.execute_script("window.open('about:blank','_blank');")
            new_handle = None
            for _ in range(40):
                time.sleep(0.1)
                now = driver.window_handles
                extra = [h for h in now if h not in handles_before]
                if extra:
                    new_handle = extra[-1]
                    break
            if not new_handle:
                raise RuntimeError(
                    "[start_driver] 새 탭을 열 수 없습니다. 팝업 차단 여부와 Chrome 버전을 확인하세요."
                )
            driver.switch_to.window(new_handle)
        else:
            cur = driver.current_window_handle
            if cur in handles_before:
                extra = [h for h in driver.window_handles if h not in handles_before]
                if extra:
                    driver.switch_to.window(extra[-1])
        try:
            driver.maximize_window()
            time.sleep(0.5)
        except Exception:
            pass
        # 모니터 꺼짐/원격접속 시 maximize가 0x0이 될 수 있으므로 항상 강제 설정
        try:
            driver.set_window_size(1920, 1080)
        except Exception:
            pass
        try:
            driver.execute_script("document.body.style.zoom='100%'")
        except Exception:
            pass
        print("[start_driver] 작업용 새 탭 열기·전환 완료 (current handle 보장)")
    
    @staticmethod
    def start_driver():
        """Chrome 디버깅 모드 드라이버 시작"""
        chrome_debugging_address = "http://127.0.0.1:9222/json"
        chrome_user_data_dir = r'C:\ChromeTEMP'
        
        print("[start_driver] Chrome 드라이버 시작...")
        
        # 좀비 ChromeDriver 프로세스 정리 (타임아웃 방지)
        killed = AWSManager.kill_all_chromedrivers()
        if killed > 0:
            print(f"[start_driver] 기존 ChromeDriver 프로세스 {killed}개 정리 완료")
            time.sleep(2)  # 프로세스 종료 대기
        
        # 사용자 데이터 디렉터리 확인 및 생성
        if not os.path.exists(chrome_user_data_dir):
            os.makedirs(chrome_user_data_dir)
            print(f"[start_driver] 사용자 데이터 디렉터리 생성: {chrome_user_data_dir}")
        else:
            print(f"[start_driver] 기존 사용자 데이터 디렉터리 사용: {chrome_user_data_dir}")
        
        # ChromeDriver 경로 찾기
        try:
            chromedriver_path = AWSManager.get_chromedriver_path()
            chromedriver_version = os.path.basename(os.path.dirname(chromedriver_path))
        except FileNotFoundError as e:
            print(f"[start_driver] 오류: {e}")
            raise
        
        # 1. ChromeDriver와 같은 버전의 Chrome for Testing 찾기 (우선순위 1)
        chrome_for_testing = AWSManager.find_chrome_for_testing(chromedriver_path)
        
        if chrome_for_testing:
            chrome_executable_path = chrome_for_testing
            print(f"[start_driver] [성공] Chrome for Testing 사용 (버전 {chromedriver_version})")
            print(f"[start_driver] Chrome 경로: {chrome_executable_path}")
        else:
            # 2. 시스템 Chrome 사용 (백업)
            system_chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
            if not os.path.isfile(system_chrome):
                alt_path = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
                if os.path.isfile(alt_path):
                    system_chrome = alt_path
                else:
                    error_msg = f"""
Chrome을 찾을 수 없습니다!

ChromeDriver 버전: {chromedriver_version}

해결 방법:
1. Chrome for Testing {chromedriver_version} 다운로드:
   https://googlechromelabs.github.io/chrome-for-testing/

2. 다운로드한 chrome-win64.zip을 다음 경로에 압축 해제:
   {os.path.dirname(chromedriver_path)}\\chrome-win64\\

3. 프로그램 재실행

또는 시스템 Chrome을 설치하세요.
"""
                    print(error_msg)
                    raise FileNotFoundError(error_msg)
            
            chrome_executable_path = system_chrome
            print(f"[start_driver] [경고] 시스템 Chrome 사용 (버전 불일치 가능)")
            print(f"[start_driver] Chrome 경로: {chrome_executable_path}")
            print(f"[start_driver] ChromeDriver 버전 {chromedriver_version}과 일치하지 않으면 오류가 발생할 수 있습니다.")
        
        try:
            # 이미 실행 중인지 확인
            print("[start_driver] 기존 Chrome 디버깅 세션 확인 중...")
            response = requests.get(chrome_debugging_address, timeout=5)
            if response.status_code == 200:
                print("[start_driver] [성공] 기존 Chrome 세션 발견, 연결 중... (로그인 캐시 유지)")
                chrome_options = Options()
                chrome_options.debugger_address = "127.0.0.1:9222"
                
                try:
                    service = Service(executable_path=chromedriver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    
                    # 창 최대화 (화면 쏠림/입력 안됨 방지)
                    try:
                        driver.maximize_window()
                    except Exception:
                        pass
                    
                    AWSManager._ensure_work_tab(driver)
                    print("[start_driver] 기존 Chrome 세션 연결 완료 (로그인 상태 유지됨)")
                    return driver
                except Exception as e:
                    # 기존 세션 연결 실패 시 포트 9222 Chrome만 종료 후 재시작 (사용자 Chrome 유지)
                    print(f"[start_driver] [경고] 기존 Chrome 세션 연결 실패: {e}")
                    print("[start_driver] 포트 9222 Chrome 프로세스만 종료 후 새로 시작합니다...")
                    AWSManager.kill_chrome_on_debug_port(port=AWSManager.CHROME_DEBUGGING_PORT)
                    time.sleep(3)
        except requests.ConnectionError:
            print("[start_driver] 기존 Chrome 세션 없음, 새로 시작...")
        except requests.Timeout:
            print("[start_driver] [경고] Chrome 디버깅 포트 응답 없음 (타임아웃), 새로 시작...")
        except Exception as e:
            print(f"[start_driver] 기존 Chrome 연결 오류: {e}")
        
        # 새로 시작
        print(f"[start_driver] Chrome 브라우저 실행: {chrome_executable_path}")
        print(f"[start_driver] 사용자 데이터 디렉터리: {chrome_user_data_dir}")
        print(f"[start_driver] [정보] 로그인 정보는 {chrome_user_data_dir}에 저장됩니다.")
        
        # Chrome 실행 옵션 설정 (--start-maximized: 화면 쏠림/입력 안됨 방지)
        chrome_args = [
            chrome_executable_path,
            '--remote-debugging-port=9222',
            f'--user-data-dir={chrome_user_data_dir}',
            '--no-first-run',  # 첫 실행 팝업 제거
            '--no-default-browser-check',  # 기본 브라우저 확인 제거
            '--start-maximized',  # 창 최대화 (뷰포트 쏠림 버그 방지)
            '--window-size=1920,1080',  # 최소 크기 보장 (고해상도/다중 모니터)
            '--force-device-scale-factor=1',  # DPI 스케일 100% 고정
            '--disable-gpu',
            '--disable-backgrounding-occluded-windows',  # 가려진 창 최적화 비활성화 (모니터 꺼짐 대응)
            '--disable-renderer-backgrounding',          # 백그라운드 렌더러 비활성화 (원격접속 대응)
        ]
        
        try:
            process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"[start_driver] Chrome 프로세스 시작됨 (PID: {process.pid})")
        except Exception as e:
            print(f"[start_driver] Chrome 실행 오류: {e}")
            raise
        
        time.sleep(4)  # Chrome 시작 대기
        
        print(f"[start_driver] WebDriver 연결 시도... (ChromeDriver: {chromedriver_path})")
        chrome_options = Options()
        chrome_options.debugger_address = "127.0.0.1:9222"
        
        try:
            service = Service(executable_path=chromedriver_path)
            print("[start_driver] WebDriver 연결 시도 중... (최대 180초 대기)")
            
            # Selenium 타임아웃 설정 증가
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("[start_driver] [성공] WebDriver 연결 성공")
            
            # 창 최대화 (화면 쏠림/입력 안됨 방지)
            try:
                driver.maximize_window()
            except Exception:
                pass
        except Exception as e:
            error_msg = str(e)
            print(f"[start_driver] [실패] WebDriver 연결 실패: {error_msg}")
            
            # 타임아웃인 경우 추가 정보 제공
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                print("[start_driver] [팁] 해결 방법:")
                print("  1. Chrome 프로세스를 수동으로 종료하세요 (작업 관리자)")
                print("  2. ChromeDriver 프로세스를 종료하세요")
                print("  3. C:\\ChromeTEMP 폴더를 삭제하고 재시도하세요")
                print("  4. 방화벽/백신이 localhost 통신을 차단하는지 확인하세요")
            
            raise Exception(f"ChromeDriver 연결 실패 (타임아웃): {error_msg}")
        
        AWSManager._ensure_work_tab(driver)
        
        print("[start_driver] Chrome 드라이버 시작 완료")
        print("[start_driver] [팁] 이 Chrome 창을 닫지 않고 유지하면 다음 실행 시 로그인 상태가 유지됩니다.")
        return driver
    
    @staticmethod
    def upload_server_build(driver, revision: int, zip_path: str, aws_link: str, 
                           branch: str = 'game', build_type: str = 'DEV', 
                           full_build_name: str = 'TEST', 
                           teamcity_id: str = '', teamcity_pw: str = '',
                           teamcity_url: str = ''):
        """서버 빌드 업로드 (TeamCity 방식)"""
        try:
            if driver is None:
                print("[서버업로드] ChromeDriver 시작 중...")
                
                # 기존 Chrome 및 ChromeDriver 프로세스 정리
                AWSManager.cleanup_chrome_processes()
                
                try:
                    driver = AWSManager.start_driver()
                except Exception as e:
                    # ChromeDriver 시작 실패 시 재시도
                    print(f"[서버업로드] ⚠️ ChromeDriver 시작 실패, 5초 후 재시도...")
                    print(f"[서버업로드] 오류: {e}")
                    time.sleep(5)
                    
                    # 모든 Chrome/ChromeDriver 프로세스 강제 종료 (재시도)
                    AWSManager.cleanup_chrome_processes()
                    
                    # 재시도
                    print("[서버업로드] ChromeDriver 재시작 시도...")
                    driver = AWSManager.start_driver()
            
            # 1. TeamCity 빌드 배포 페이지 접속 (teamcity_url 미지정 시 기본값 사용)
            default_teamcity_url = "https://pbbseoul6-w.bluehole.net/buildConfiguration/BlackBudget_Deployment_DeployBuild?mode=branches#all-projects"
            tc_url = teamcity_url or default_teamcity_url
            print(f"[서버업로드] TeamCity 페이지 접속: {tc_url}")
            driver.get(tc_url)
            driver.implicitly_wait(10)
            time.sleep(2)
            
            # 자동 로그인 시도 (로그인 페이지 리다이렉트 시 대비)
            AWSManager.teamcity_auto_login(driver, teamcity_id, teamcity_pw)
            driver.get(tc_url)
            time.sleep(2)
            
            # 2. Run 버튼 클릭 (클릭 가능할 때까지 대기)
            run_button_xpath0 = '//*[@id="main-content-tag"]/div[4]/div/div[1]/div[1]/div/div[1]/div/button'
            run_button_xpath1 = '//*[@id="main-content-tag"]/div[4]/div/div[1]/div[1]/div/div[2]/div[1]/div/button'
            wait = WebDriverWait(driver, 60)  # 타임아웃을 60초로 증가
            
            # 페이지 로드 완료 대기
            time.sleep(3)
            
            try:
                print("[서버업로드] [단계 1/6] Run 버튼 대기 중...")
                run_button_clicked = False
                
                # 첫 번째 XPath 시도
                try:
                    run_button = wait.until(EC.presence_of_element_located((By.XPATH, run_button_xpath0)))
                    print("[서버업로드] [단계 1/6] Run 버튼 클릭 (XPath 0)")
                    AWSManager._safe_click(driver, run_button)
                    run_button_clicked = True
                    print("[서버업로드] [단계 1/6] ✅ Run 버튼 클릭 완료 (XPath 0)")
                except TimeoutException:
                    print("[서버업로드] [단계 1/6] ⚠️ XPath 0 실패, XPath 1 시도 중...")
                    # 두 번째 XPath 시도
                    try:
                        run_button = wait.until(EC.presence_of_element_located((By.XPATH, run_button_xpath1)))
                        print("[서버업로드] [단계 1/6] Run 버튼 클릭 (XPath 1)")
                        AWSManager._safe_click(driver, run_button)
                        run_button_clicked = True
                        print("[서버업로드] [단계 1/6] ✅ Run 버튼 클릭 완료 (XPath 1)")
                    except TimeoutException:
                        pass  # 다음 except 블록에서 처리
                
                if not run_button_clicked:
                    raise TimeoutException("[서버업로드] [단계 1/6] Run 버튼을 찾을 수 없습니다 (XPath 0, 1 모두 실패)")
            except TimeoutException:
                print("[서버업로드] [단계 1/6] ⚠️ Run 버튼을 찾을 수 없습니다. 대체 XPath 시도...")
                # 대체 XPath 시도
                alternative_xpath = "//button[contains(@class, 'btn-run') or contains(text(), 'Run')]"
                try:
                    run_button = wait.until(EC.presence_of_element_located((By.XPATH, alternative_xpath)))
                    AWSManager._safe_click(driver, run_button)
                    print("[서버업로드] [단계 1/6] ✅ 대체 XPath로 Run 버튼 클릭 성공")
                except Exception as e:
                    raise Exception(f"[서버업로드] [단계 1/6 실패] Run 버튼을 찾을 수 없습니다. TeamCity 페이지 구조가 변경되었거나 로그인이 필요합니다. XPath: {run_button_xpath}, 대체: {alternative_xpath}")
            
            time.sleep(2)
            
            # 탭 0 클릭
            try:
                print("[서버업로드] [단계 2/6] 탭 0 클릭")
                tab0 = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tab-0"]/p/a')))
                AWSManager._safe_click(driver, tab0)
                time.sleep(0.5)
                print("[서버업로드] [단계 2/6] ✅ 탭 0 클릭 완료")
            except TimeoutException:
                raise Exception(f"[서버업로드] [단계 2/6 실패] 탭 0을 찾을 수 없습니다. XPath: //*[@id=\"tab-0\"]/p/a")

            # moveToTop 클릭
            try:
                print("[서버업로드] [단계 3/6] moveToTop 클릭")
                AWSManager._safe_click(driver, driver.find_element(By.XPATH, '//*[@id="moveToTop"]'))
                time.sleep(0.5)
                print("[서버업로드] [단계 3/6] ✅ moveToTop 클릭 완료")
            except TimeoutException:
                raise Exception(f"[서버업로드] [단계 3/6 실패] moveToTop 버튼을 찾을 수 없습니다. XPath: //*[@id=\"moveToTop\"]")

            # 탭 3 클릭
            try:
                print("[서버업로드] [단계 4/6] 탭 3 클릭")
                tab3 = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tab-3"]/p/a')))
                AWSManager._safe_click(driver, tab3)
                time.sleep(0.5)
                print("[서버업로드] [단계 4/6] ✅ 탭 3 클릭 완료")
            except TimeoutException:
                raise Exception(f"[서버업로드] [단계 4/6 실패] 탭 3을 찾을 수 없습니다. XPath: //*[@id=\"tab-3\"]/p/a")
            
            # 5. 빌드 경로 입력 (텍스트 입력 가능할 때까지 대기)
            path_input_xpath = '//*[@id="parameter_build_to_deploy_nas_path_804258969"]'
            
            try:
                print(f"[서버업로드] [단계 5/6] 빌드 경로 입력 필드 대기 중... (빌드: {full_build_name})")
                path_input = wait.until(EC.presence_of_element_located((By.XPATH, path_input_xpath)))
            except TimeoutException:
                print("[서버업로드] [단계 5/6] ⚠️ 빌드 경로 입력 필드를 찾을 수 없습니다. 대체 방법 시도...")
                # name 속성으로 찾기 시도
                try:
                    path_input = wait.until(EC.presence_of_element_located((By.NAME, "parameter_build_to_deploy_nas_path")))
                    print("[서버업로드] [단계 5/6] name 속성으로 입력 필드 찾기 성공")
                except:
                    # class나 placeholder로 찾기 시도
                    try:
                        path_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'path') or contains(@name, 'nas')]")))
                        print("[서버업로드] [단계 5/6] placeholder 속성으로 입력 필드 찾기 성공")
                    except Exception as e:
                        raise Exception(f"[서버업로드] [단계 5/6 실패] 빌드 경로 입력 필드를 찾을 수 없습니다. TeamCity 페이지 구조가 변경되었을 수 있습니다. XPath: {path_input_xpath}")
            
            # 빌드 경로 생성 (예: \\pubg-pds\PBB\Builds\CompileBuild_DEV_game_dev_SEL294706_r357283)
            build_path = f"\\\\pubg-pds\\PBB\\Builds\\{full_build_name}"
            print(f"[서버업로드] [단계 5/6] 빌드 경로 입력: {build_path}")
            path_input.clear()
            path_input.send_keys(build_path)
            time.sleep(2)
            print(f"[서버업로드] [단계 5/6] ✅ 빌드 경로 입력 완료")
            
            # 6. Run 버튼 클릭 (최종 실행, 클릭 가능할 때까지 대기)
            final_run_button_xpath = '//*[@id="runCustomBuildButton"]'
            
            try:
                print("[서버업로드] [단계 6/6] 최종 Run 버튼 대기 중...")
                final_run_button = wait.until(EC.presence_of_element_located((By.XPATH, final_run_button_xpath)))
                print("[서버업로드] [단계 6/6] 최종 Run 버튼 클릭")
                AWSManager._safe_click(driver, final_run_button)
                print("[서버업로드] [단계 6/6] ✅ 최종 Run 버튼 클릭 완료")
            except TimeoutException:
                print("[서버업로드] [단계 6/6] ⚠️ 최종 Run 버튼을 찾을 수 없습니다. 대체 방법 시도...")
                try:
                    # 대체 XPath 시도
                    alternative_final_xpath = "//button[contains(@id, 'runCustomBuild') or contains(text(), 'Run')]"
                    final_run_button = wait.until(EC.presence_of_element_located((By.XPATH, alternative_final_xpath)))
                    AWSManager._safe_click(driver, final_run_button)
                    print("[서버업로드] [단계 6/6] ✅ 대체 XPath로 최종 Run 버튼 클릭 성공")
                except Exception as e:
                    raise Exception(f"[서버업로드] [단계 6/6 실패] 최종 Run 버튼을 찾을 수 없습니다. TeamCity 페이지 구조가 변경되었을 수 있습니다. XPath: {final_run_button_xpath}")
            
            time.sleep(3)
            
            print("[서버업로드] ✅ 배포 요청 완료")
            try:
                export_upload_result(aws_link, full_build_name, "teamcity_deploy", ":update_done:")
            except:
                print("export_upload_result 오류")
                
        except TimeoutException as e:
            error_msg = f"[서버업로드] ❌ 타임아웃 오류: {str(e)}"
            print(error_msg)
            try:
                export_upload_result(aws_link, full_build_name, "teamcity_deploy", ":timeout:")
            except:
                print("[서버업로드] export_upload_result 오류")
            # 원본 예외를 그대로 발생시켜 단계 정보 유지
            raise
        except Exception as e:
            error_msg = f"[서버업로드] ❌ 오류: {str(e)}"
            print(error_msg)
            try:
                export_upload_result(aws_link, full_build_name, "teamcity_deploy", ":failed:")
            except:
                print("[서버업로드] export_upload_result 오류")
            # 예외를 다시 발생시켜서 호출자에게 실패를 알림 (단계 정보 포함)
            raise
    
    @staticmethod
    def update_server_container(driver, revision: int, aws_link: str, branch: str = 'game', 
                               build_type: str = 'DEV', is_debug: bool = False, 
                               full_build_name: str = 'none'):
        """서버 컨테이너 패치"""
        try:
            print(f"[update_server_container] 시작 - revision: {revision}, branch: {branch}, build_type: {build_type}")
            print(f"[update_server_container] AWS URL: {aws_link}")
            
            if branch == "":
                branch = 'game'
                print(f"[update_server_container] branch 기본값 설정: {branch}")
            
            if driver is None:
                print("[update_server_container] ChromeDriver 시작 중...")
                
                # 기존 Chrome 및 ChromeDriver 프로세스 정리
                AWSManager.cleanup_chrome_processes()
                
                try:
                    driver = AWSManager.start_driver()
                except Exception as e:
                    # ChromeDriver 시작 실패 시 재시도
                    print(f"[update_server_container] ⚠️ ChromeDriver 시작 실패, 5초 후 재시도...")
                    print(f"[update_server_container] 오류: {e}")
                    time.sleep(5)
                    
                    # 모든 Chrome/ChromeDriver 프로세스 강제 종료 (재시도)
                    AWSManager.cleanup_chrome_processes()
                    
                    # 재시도
                    print("[update_server_container] ChromeDriver 재시작 시도...")
                    driver = AWSManager.start_driver()
                
                driver.implicitly_wait(10)
                
                print(f"[update_server_container] AWS 페이지 이동: {aws_link}")
                driver.get(aws_link)
                driver.implicitly_wait(10)
                
                AWSManager._ensure_aws_deploy_social_oidc_clicked(driver, "[update_server_container]")
                AWSManager._ensure_keycloak_login(driver, "[update_server_container]")

            driver.implicitly_wait(10)
            print("[update_server_container] 패치 작업 시작...")
            
            # WebDriverWait 설정
            wait = WebDriverWait(driver, 20)
            
            # CONTAINER GAMESERVERS 클릭
            try:
                print("[update_server_container] [단계 1/11] CONTAINER GAMESERVERS 탭 클릭 대기 중...")
                container_tab = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/ul/li[3]/a/span")))
                AWSManager._safe_click(driver, container_tab)
                time.sleep(1)
                print("[update_server_container] [단계 1/11] ✅ CONTAINER GAMESERVERS 탭 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 1/11 실패] CONTAINER GAMESERVERS 탭을 찾을 수 없습니다. 로그인이 필요하거나 페이지 구조가 변경되었을 수 있습니다. XPath: /html/body/div[1]/div[3]/div/div[2]/ul/li[3]/a/span")

            # SELECT ALL 버튼 클릭
            try:
                print("[update_server_container] [단계 1/11] SELECT ALL 버튼 클릭 대기 중...")
                select_all_button = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[1]")))
                AWSManager._safe_click(driver, select_all_button)
                time.sleep(1)
                print("[update_server_container] [단계 1/11] ✅ SELECT ALL 버튼 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 1/11 실패] SELECT ALL 버튼을 찾을 수 없습니다. XPath: /html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[1]")

            # 돋보기 (필터) 버튼 클릭
            try:
                print("[update_server_container] [단계 2/11] 필터 버튼 클릭 대기 중...")
                filter_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/div/button')))
                AWSManager._safe_click(driver, filter_button)
                time.sleep(1)
                print("[update_server_container] [단계 2/11] ✅ 필터 버튼 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 2/11 실패] 필터 버튼을 찾을 수 없습니다. XPath: /html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/div/button")
            
            # 브랜치 입력
            try:
                print(f"[update_server_container] [단계 3/11] 브랜치 입력 필드 대기 중... (브랜치: {branch})")
                branch_input = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input')))
                AWSManager._scroll_into_view(driver, branch_input)
                branch_input.clear()
                branch_input.send_keys(branch)
                time.sleep(1.5)
                print(f"[update_server_container] [단계 3/11] ✅ 브랜치 '{branch}' 입력 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 3/11 실패] 브랜치 입력 필드를 찾을 수 없습니다. XPath: /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input")
            
            # 정확히 일치하는 branch 선택
            try:
                print(f"[update_server_container] [단계 4/11] 브랜치 '{branch}' 검색 중...")
                branch_found = False
                for x in range(1, 10):
                    try:
                        element = wait.until(EC.presence_of_element_located((By.XPATH, f'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[{x}]/span')))
                        if element.text == branch:
                            print(f"[update_server_container] [단계 4/11] 브랜치 '{branch}' 발견 (목록 {x}번째), 클릭")
                            AWSManager._scroll_into_view(driver, element)
                            AWSManager._safe_click(driver, element)
                            branch_found = True
                            break
                    except Exception as e:
                        if x == 9:
                            break
                        continue
                
                if not branch_found:
                    raise Exception(f"[단계 4/11 실패] 브랜치 '{branch}'를 목록에서 찾을 수 없습니다. 브랜치명이 정확한지 확인하세요.")
                
                print(f"[update_server_container] [단계 4/11] ✅ 브랜치 '{branch}' 선택 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 4/11 실패] 브랜치 목록을 찾을 수 없습니다. XPath: /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[x]/span")
            
            # Next 버튼 (브랜치)
            try:
                time.sleep(1)
                print("[update_server_container] [단계 5/11] Next 버튼 클릭 (브랜치)")
                next_button1 = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]')))
                AWSManager._scroll_into_view(driver, next_button1)
                AWSManager._safe_click(driver, next_button1)
                print("[update_server_container] [단계 5/11] ✅ Next 버튼 클릭 완료 (브랜치)")
            except TimeoutException as e:
                raise Exception(f"[단계 5/11 실패] Next 버튼을 찾을 수 없습니다 (브랜치). XPath: /html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]")
            
            # TAG 입력
            try:
                print(f"[update_server_container] [단계 6/11] TAG 입력 필드 대기 중... (TAG: {full_build_name})")
                tag_input = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input')))
                AWSManager._scroll_into_view(driver, tag_input)
                tag_input.clear()
                tag_input.send_keys(full_build_name)
                time.sleep(1)
                print(f"[update_server_container] [단계 6/11] ✅ TAG '{full_build_name}' 입력 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 6/11 실패] TAG 입력 필드를 찾을 수 없습니다. XPath: /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input")
            
            # TAG 선택
            try:
                print("[update_server_container] [단계 7/11] TAG 선택")
                tag_option = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[1]/span')))
                AWSManager._scroll_into_view(driver, tag_option)
                AWSManager._safe_click(driver, tag_option)
                time.sleep(1)
                print("[update_server_container] [단계 7/11] ✅ TAG 선택 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 7/11 실패] 해당 서버가 업로드 되지 않았습니다.\n{full_build_name}")

            # Next 버튼 (TAG)
            try:
                print("[update_server_container] [단계 8/11] Next 버튼 클릭 (TAG)")
                next_button2 = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]')))
                AWSManager._scroll_into_view(driver, next_button2)
                AWSManager._safe_click(driver, next_button2)
                print("[update_server_container] [단계 8/11] ✅ Next 버튼 클릭 완료 (TAG)")
            except TimeoutException as e:
                raise Exception(f"[단계 8/11 실패] Next 버튼을 찾을 수 없습니다 (TAG). XPath: /html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]")

            # Build config 체크박스
            try:
                print("[update_server_container] [단계 9/11] Build config 체크박스 클릭")
                build_config_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div/div/div[2]')))
                AWSManager._scroll_into_view(driver, build_config_checkbox)
                AWSManager._safe_click(driver, build_config_checkbox)
                time.sleep(1)
                print("[update_server_container] [단계 9/11] ✅ Build config 체크박스 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 9/11 실패] Build config 체크박스를 찾을 수 없습니다. XPath: /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div/div/div[2]")

            # Next 버튼 (Build config)
            try:
                print("[update_server_container] [단계 10/11] Next 버튼 클릭 (Build config)")
                next_button3 = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]')))
                AWSManager._scroll_into_view(driver, next_button3)
                AWSManager._safe_click(driver, next_button3)
                print("[update_server_container] [단계 10/11] ✅ Next 버튼 클릭 완료 (Build config)")
            except TimeoutException as e:
                raise Exception(f"[단계 10/11 실패] Next 버튼을 찾을 수 없습니다 (Build config). XPath: /html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]")

            # SELECT 버튼 클릭
            try:
                print("[update_server_container] [단계 11/11] SELECT 버튼 클릭")
                select_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/button')))
                AWSManager._scroll_into_view(driver, select_button)
                AWSManager._safe_click(driver, select_button)
                time.sleep(1)
                print("[update_server_container] [단계 11/11] ✅ SELECT 버튼 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 11/11 실패] SELECT 버튼을 찾을 수 없습니다. XPath: /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/button")

            # APPLY 버튼 클릭
            try:
                print("[update_server_container] [최종 단계] APPLY 버튼 클릭")
                apply_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[3]')))
                AWSManager._safe_click(driver, apply_button)
                print("[update_server_container] [최종 단계] ✅ APPLY 버튼 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[최종 단계 실패] APPLY 버튼을 찾을 수 없습니다. XPath: /html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[3]")

            if not is_debug:
                # 팝업 OK 버튼
                try:
                    print("[update_server_container] [확인] 팝업 OK 버튼 클릭")
                    ok_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/button[1]')))
                    AWSManager._safe_click(driver, ok_button)
                    print("[update_server_container] [확인] ✅ 팝업 OK 버튼 클릭 완료")
                    time.sleep(20)
                    print("[update_server_container] [확인] 팝업 OK 버튼 클릭 완료 후 20초 대기")
                    
                    # 첫 번째 탭 클릭
                    try:
                        print("[update_server_container] [완료 단계 1/3] 첫 번째 탭 클릭")
                        first_tab = None
                        for attempt in range(10):
                            try:
                                first_tab = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/ul/li[1]/a')))
                                break
                            except TimeoutException:
                                print(f"[update_server_container] [완료 단계 1/3] 첫 번째 탭 대기 중... ({attempt + 1}/10)")
                                time.sleep(1)

                        if first_tab is None:
                            raise TimeoutException("[완료 단계 1/3] 첫 번째 탭을 10초 동안 찾을 수 없습니다.")

                        AWSManager._safe_click(driver, first_tab)
                        time.sleep(0.5)
                        print("[update_server_container] [완료 단계 1/3] ✅ 첫 번째 탭 클릭 완료")
                    except TimeoutException as e:
                        raise Exception(f"[완료 단계 1/2 실패] 첫 번째 탭을 찾을 수 없습니다. XPath: /html/body/div[1]/div[3]/div/div[2]/ul/li[1]/a")

                    # Update with Sync 버튼 클릭
                    try:
                        print("[update_server_container] [완료 단계 2/3] Update with Sync 버튼 클릭")
                        final_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div/div/form/fieldset/div/div/div[7]/div/button')))
                        AWSManager._safe_click(driver, final_button)
                        time.sleep(0.5)
                        print("[update_server_container] [완료 단계 2/3] ✅ Update with Sync 버튼 클릭 완료")
                    except TimeoutException as e:
                        raise Exception(f"[완료 단계 2/2 실패] 최종 버튼을 찾을 수 없습니다. XPath: /html/body/div[1]/div[3]/div/div[2]/div/div/form/fieldset/div/div/div[7]/div/button")

                    #아래가 진짜 최종 버튼 OK /html/body/div[3]/div[1]/div[2]/div/button[1]
                    try:
                        print("[update_server_container] [완료 단계 3/3] Update with Sync OK 버튼 클릭")
                        final_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/button[1]')))
                        AWSManager._safe_click(driver, final_button)
                        time.sleep(0.5)
                        print("[update_server_container] [완료 단계 3/3] ✅ Update with Sync OK 버튼 클릭 완료")
                    except TimeoutException as e:
                        raise Exception(f"[완료 단계 3/3 실패] 최종 버튼을 찾을 수 없습니다. XPath: /html/body/div[3]/div[1]/div[2]/div/button[1]")

                    #아래가 진짜 최종 OK /html/body/div[3]/div[1]/div[2]/div/button[1]
                    try:
                        print("[update_server_container] [완료 단계 4/4] 최종 OK 버튼 클릭")
                        final_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/button[1]')))
                        AWSManager._safe_click(driver, final_button)
                        time.sleep(0.5)
                        print("[update_server_container] [완료 단계 4/4] ✅ 최종 OK 버튼 클릭 완료")
                    except TimeoutException as e:
                        raise Exception(f"[완료 단계 4/4 실패] 최종 OK 버튼을 찾을 수 없습니다. XPath: /html/body/div[3]/div[1]/div[2]/div/button[1]")
                    try:
                        export_upload_result(aws_link, full_build_name, "aws_apply", ":update_done:")
                    except:
                        print("[update_server_container] export_upload_result 오류")
                except TimeoutException as e:
                    raise Exception(f"[확인 단계 실패] 확인 팝업 OK 버튼을 찾을 수 없습니다. XPath: /html/body/div[3]/div[1]/div[2]/div/button[1]")
                    
            print("[update_server_container] ✅ 서버 패치 완료")
            
        except TimeoutException as e:
            error_msg = f"[update_server_container] ❌ 타임아웃: {str(e)}"
            print(error_msg)
            try:
                export_upload_result(aws_link, full_build_name, "aws_apply", ":timeout:")
            except:
                print("[update_server_container] export_upload_result 오류")
            # 원본 예외를 그대로 발생시켜 단계 정보 유지
            raise
        except Exception as e:
            error_msg = f"[update_server_container] ❌ 패치 오류: {str(e)}"
            print(error_msg)
            try:
                export_upload_result(aws_link, full_build_name, "aws_apply", ":failed:")
            except:
                print("[update_server_container] export_upload_result 오류")
            # 예외를 다시 발생시켜서 호출자에게 실패를 알림 (단계 정보 포함)
            raise
    
    @staticmethod
    def update_latest_server_container(driver, aws_link: str, branch: str = 'game',
                                        build_prefix: str = '', is_debug: bool = False):
        """서버최신강제패치 - TAG 목록에서 build_prefix에 맞는 최신 리비전으로 자동 패치

        Args:
            driver: Selenium WebDriver (None이면 새로 시작)
            aws_link: AWS 배포 페이지 URL
            branch: 브랜치명
            build_prefix: 세미콜론(;)으로 구분된 필터 키워드 (예: "DailyQLOC;game_dev_AMS")
            is_debug: 디버그 모드 (True면 최종 실행 버튼 클릭 안 함)
        """
        selected_tag = 'unknown'
        try:
            print(f"[서버최신강제패치] 시작 - branch: {branch}, build_prefix: {build_prefix}")
            print(f"[서버최신강제패치] AWS URL: {aws_link}")

            if branch == "":
                branch = 'game'
                print(f"[서버최신강제패치] branch 기본값 설정: {branch}")

            # build_prefix 파싱
            prefixes = [p.strip() for p in build_prefix.split(';') if p.strip()]
            if not prefixes:
                raise Exception("Build Prefix가 비어있습니다. 세미콜론(;)으로 구분하여 키워드를 입력하세요.")
            print(f"[서버최신강제패치] 필터 키워드: {prefixes}")

            if driver is None:
                print("[서버최신강제패치] ChromeDriver 시작 중...")

                # 기존 Chrome 및 ChromeDriver 프로세스 정리
                AWSManager.cleanup_chrome_processes()

                try:
                    driver = AWSManager.start_driver()
                except Exception as e:
                    print(f"[서버최신강제패치] ⚠️ ChromeDriver 시작 실패, 5초 후 재시도...")
                    print(f"[서버최신강제패치] 오류: {e}")
                    time.sleep(5)
                    AWSManager.cleanup_chrome_processes()
                    print("[서버최신강제패치] ChromeDriver 재시작 시도...")
                    driver = AWSManager.start_driver()

                driver.implicitly_wait(10)

                print(f"[서버최신강제패치] AWS 페이지 이동: {aws_link}")
                driver.get(aws_link)
                driver.implicitly_wait(10)

                AWSManager._ensure_aws_deploy_social_oidc_clicked(driver, "[서버최신강제패치]")
                AWSManager._ensure_keycloak_login(driver, "[서버최신강제패치]")

            driver.implicitly_wait(10)
            print("[서버최신강제패치] 패치 작업 시작...")

            wait = WebDriverWait(driver, 20)

            # [단계 1/11] CONTAINER GAMESERVERS 클릭
            try:
                print("[서버최신강제패치] [단계 1/11] CONTAINER GAMESERVERS 탭 클릭 대기 중...")
                container_tab = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/ul/li[3]/a/span")))
                AWSManager._safe_click(driver, container_tab)
                time.sleep(1)
                print("[서버최신강제패치] [단계 1/11] ✅ CONTAINER GAMESERVERS 탭 클릭 완료")
            except TimeoutException:
                raise Exception("[단계 1/11 실패] CONTAINER GAMESERVERS 탭을 찾을 수 없습니다.")

            # [단계 1/11] SELECT ALL 버튼 클릭
            try:
                print("[서버최신강제패치] [단계 1/11] SELECT ALL 버튼 클릭 대기 중...")
                select_all_button = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[1]")))
                AWSManager._safe_click(driver, select_all_button)
                time.sleep(1)
                print("[서버최신강제패치] [단계 1/11] ✅ SELECT ALL 버튼 클릭 완료")
            except TimeoutException:
                raise Exception("[단계 1/11 실패] SELECT ALL 버튼을 찾을 수 없습니다.")

            # [단계 2/11] 돋보기 (필터) 버튼 클릭
            try:
                print("[서버최신강제패치] [단계 2/11] 필터 버튼 클릭 대기 중...")
                filter_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/div/button')))
                AWSManager._safe_click(driver, filter_button)
                time.sleep(1)
                print("[서버최신강제패치] [단계 2/11] ✅ 필터 버튼 클릭 완료")
            except TimeoutException:
                raise Exception("[단계 2/11 실패] 필터 버튼을 찾을 수 없습니다.")

            # [단계 3/11] 브랜치 입력
            try:
                print(f"[서버최신강제패치] [단계 3/11] 브랜치 입력 필드 대기 중... (브랜치: {branch})")
                branch_input = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input')))
                branch_input.clear()
                branch_input.send_keys(branch)
                time.sleep(1.5)
                print(f"[서버최신강제패치] [단계 3/11] ✅ 브랜치 '{branch}' 입력 완료")
            except TimeoutException:
                raise Exception(f"[단계 3/11 실패] 브랜치 입력 필드를 찾을 수 없습니다.")

            # [단계 4/11] 정확히 일치하는 branch 선택
            try:
                print(f"[서버최신강제패치] [단계 4/11] 브랜치 '{branch}' 검색 중...")
                branch_found = False
                for x in range(1, 10):
                    try:
                        element = wait.until(EC.presence_of_element_located((By.XPATH, f'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[{x}]/span')))
                        if element.text == branch:
                            print(f"[서버최신강제패치] [단계 4/11] 브랜치 '{branch}' 발견 (목록 {x}번째), 클릭")
                            AWSManager._safe_click(driver, element)
                            branch_found = True
                            break
                    except Exception:
                        if x == 9:
                            break
                        continue

                if not branch_found:
                    raise Exception(f"[단계 4/11 실패] 브랜치 '{branch}'를 목록에서 찾을 수 없습니다.")

                print(f"[서버최신강제패치] [단계 4/11] ✅ 브랜치 '{branch}' 선택 완료")
            except TimeoutException:
                raise Exception(f"[단계 4/11 실패] 브랜치 목록을 찾을 수 없습니다.")

            # [단계 5/11] Next 버튼 (브랜치)
            try:
                time.sleep(1)
                print("[서버최신강제패치] [단계 5/11] Next 버튼 클릭 (브랜치)")
                next_button1 = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]')))
                AWSManager._safe_click(driver, next_button1)
                print("[서버최신강제패치] [단계 5/11] ✅ Next 버튼 클릭 완료 (브랜치)")
            except TimeoutException:
                raise Exception("[단계 5/11 실패] Next 버튼을 찾을 수 없습니다 (브랜치).")

            # [단계 6/11] TAG 목록에서 rz-multiselect-item의 aria-label 읽기
            try:
                print("[서버최신강제패치] [단계 6/11] TAG 드롭다운에서 항목 읽는 중...")
                # TAG 입력 필드 대기
                tag_input = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input')))
                time.sleep(1)

                # rz-multiselect-item 요소들의 aria-label 읽기
                items = driver.find_elements(By.CSS_SELECTOR, 'li.rz-multiselect-item')
                all_tags = []
                for item in items:
                    label = item.get_attribute('aria-label')
                    if label:
                        all_tags.append(label)

                print(f"[서버최신강제패치] [단계 6/11] 총 {len(all_tags)}개 TAG 항목 발견")
                if not all_tags:
                    raise Exception("[단계 6/11 실패] TAG 항목이 없습니다. 페이지 구조를 확인하세요.")

            except TimeoutException:
                raise Exception("[단계 6/11 실패] TAG 입력 필드를 찾을 수 없습니다.")

            # [단계 7/11] build_prefix로 필터링 후 최신 리비전 선택
            try:
                print(f"[서버최신강제패치] [단계 7/11] 필터링 중... (키워드: {prefixes})")
                matching_tags = []
                for label in all_tags:
                    if all(p in label for p in prefixes):
                        rev_match = re.search(r'_r(\d+)', label)
                        if rev_match:
                            revision = int(rev_match.group(1))
                            matching_tags.append((revision, label))
                            print(f"  [매칭] {label} (revision: {revision})")

                if not matching_tags:
                    raise Exception(
                        f"[단계 7/11 실패] build_prefix '{build_prefix}'에 해당하는 TAG를 찾을 수 없습니다.\n"
                        f"전체 TAG 목록 ({len(all_tags)}개): {all_tags[:10]}{'...' if len(all_tags) > 10 else ''}"
                    )

                # 최고 리비전 선택
                matching_tags.sort(reverse=True, key=lambda x: x[0])
                selected_revision, selected_tag = matching_tags[0]
                print(f"[서버최신강제패치] [단계 7/11] ✅ 선택된 TAG: {selected_tag} (revision: {selected_revision})")
                print(f"[서버최신강제패치] [단계 7/11] 매칭된 항목 수: {len(matching_tags)}")

            except TimeoutException:
                raise

            # [단계 8/11] 선택된 TAG 입력 및 선택
            try:
                print(f"[서버최신강제패치] [단계 8/11] TAG 입력: {selected_tag}")
                tag_input.clear()
                tag_input.send_keys(selected_tag)
                time.sleep(1)

                # 드롭다운에서 첫 번째 항목 클릭
                tag_option = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[1]/span')))
                AWSManager._safe_click(driver, tag_option)
                time.sleep(1)
                print(f"[서버최신강제패치] [단계 8/11] ✅ TAG '{selected_tag}' 선택 완료")
            except TimeoutException:
                raise Exception(f"[단계 8/11 실패] TAG '{selected_tag}' 선택에 실패했습니다.")

            # [단계 8/11] Next 버튼 (TAG)
            try:
                print("[서버최신강제패치] [단계 8/11] Next 버튼 클릭 (TAG)")
                next_button2 = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]')))
                AWSManager._safe_click(driver, next_button2)
                print("[서버최신강제패치] [단계 8/11] ✅ Next 버튼 클릭 완료 (TAG)")
            except TimeoutException:
                raise Exception("[단계 8/11 실패] Next 버튼을 찾을 수 없습니다 (TAG).")

            # [단계 9/11] Build config 체크박스
            try:
                print("[서버최신강제패치] [단계 9/11] Build config 체크박스 클릭")
                build_config_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div/div/div[2]')))
                AWSManager._safe_click(driver, build_config_checkbox)
                time.sleep(1)
                print("[서버최신강제패치] [단계 9/11] ✅ Build config 체크박스 클릭 완료")
            except TimeoutException:
                raise Exception("[단계 9/11 실패] Build config 체크박스를 찾을 수 없습니다.")

            # [단계 10/11] Next 버튼 (Build config)
            try:
                print("[서버최신강제패치] [단계 10/11] Next 버튼 클릭 (Build config)")
                next_button3 = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]')))
                AWSManager._safe_click(driver, next_button3)
                print("[서버최신강제패치] [단계 10/11] ✅ Next 버튼 클릭 완료 (Build config)")
            except TimeoutException:
                raise Exception("[단계 10/11 실패] Next 버튼을 찾을 수 없습니다 (Build config).")

            # [단계 11/11] SELECT 버튼 클릭
            try:
                print("[서버최신강제패치] [단계 11/11] SELECT 버튼 클릭")
                select_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/button')))
                AWSManager._safe_click(driver, select_button)
                time.sleep(1)
                print("[서버최신강제패치] [단계 11/11] ✅ SELECT 버튼 클릭 완료")
            except TimeoutException:
                raise Exception("[단계 11/11 실패] SELECT 버튼을 찾을 수 없습니다.")

            # APPLY 버튼 클릭
            try:
                print("[서버최신강제패치] [최종 단계] APPLY 버튼 클릭")
                apply_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[3]')))
                AWSManager._safe_click(driver, apply_button)
                print("[서버최신강제패치] [최종 단계] ✅ APPLY 버튼 클릭 완료")
            except TimeoutException:
                raise Exception("[최종 단계 실패] APPLY 버튼을 찾을 수 없습니다.")

            if not is_debug:
                # 팝업 OK 버튼
                try:
                    print("[서버최신강제패치] [확인] 팝업 OK 버튼 클릭")
                    ok_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/button[1]')))
                    AWSManager._safe_click(driver, ok_button)
                    print("[서버최신강제패치] [확인] ✅ 팝업 OK 버튼 클릭 완료")
                    time.sleep(20)
                    print("[서버최신강제패치] [확인] 팝업 OK 버튼 클릭 완료 후 20초 대기")

                    # 첫 번째 탭 클릭
                    try:
                        print("[서버최신강제패치] [완료 단계 1/3] 첫 번째 탭 클릭")
                        first_tab = None
                        for attempt in range(10):
                            try:
                                first_tab = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/ul/li[1]/a')))
                                break
                            except TimeoutException:
                                print(f"[서버최신강제패치] [완료 단계 1/3] 첫 번째 탭 대기 중... ({attempt + 1}/10)")
                                time.sleep(1)

                        if first_tab is None:
                            raise TimeoutException("[완료 단계 1/3] 첫 번째 탭을 10초 동안 찾을 수 없습니다.")

                        AWSManager._safe_click(driver, first_tab)
                        time.sleep(0.5)
                        print("[서버최신강제패치] [완료 단계 1/3] ✅ 첫 번째 탭 클릭 완료")
                    except TimeoutException as e:
                        raise Exception(f"[완료 단계 1/3 실패] 첫 번째 탭을 찾을 수 없습니다.")

                    # Update with Sync 버튼 클릭
                    try:
                        print("[서버최신강제패치] [완료 단계 2/3] Update with Sync 버튼 클릭")
                        final_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div/div/form/fieldset/div/div/div[7]/div/button')))
                        AWSManager._safe_click(driver, final_button)
                        time.sleep(0.5)
                        print("[서버최신강제패치] [완료 단계 2/3] ✅ Update with Sync 버튼 클릭 완료")
                    except TimeoutException:
                        raise Exception("[완료 단계 2/3 실패] Update with Sync 버튼을 찾을 수 없습니다.")

                    # Update with Sync OK 버튼
                    try:
                        print("[서버최신강제패치] [완료 단계 3/3] Update with Sync OK 버튼 클릭")
                        final_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/button[1]')))
                        AWSManager._safe_click(driver, final_button)
                        time.sleep(0.5)
                        print("[서버최신강제패치] [완료 단계 3/3] ✅ Update with Sync OK 버튼 클릭 완료")
                    except TimeoutException:
                        raise Exception("[완료 단계 3/3 실패] Update with Sync OK 버튼을 찾을 수 없습니다.")

                    # 최종 OK 버튼
                    try:
                        print("[서버최신강제패치] [완료 단계 4/4] 최종 OK 버튼 클릭")
                        final_button = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/button[1]')))
                        AWSManager._safe_click(driver, final_button)
                        time.sleep(0.5)
                        print("[서버최신강제패치] [완료 단계 4/4] ✅ 최종 OK 버튼 클릭 완료")
                    except TimeoutException:
                        raise Exception("[완료 단계 4/4 실패] 최종 OK 버튼을 찾을 수 없습니다.")
                    try:
                        export_upload_result(aws_link, selected_tag, "aws_apply", ":update_done:")
                    except:
                        print("[서버최신강제패치] export_upload_result 오류")
                except TimeoutException as e:
                    raise Exception(f"[확인 단계 실패] 확인 팝업 OK 버튼을 찾을 수 없습니다.")

            print(f"[서버최신강제패치] ✅ 서버 패치 완료 (TAG: {selected_tag})")
            return selected_tag

        except TimeoutException as e:
            error_msg = f"[서버최신강제패치] ❌ 타임아웃: {str(e)}"
            print(error_msg)
            try:
                export_upload_result(aws_link, selected_tag, "aws_apply", ":timeout:")
            except:
                print("[서버최신강제패치] export_upload_result 오류")
            raise
        except Exception as e:
            error_msg = f"[서버최신강제패치] ❌ 패치 오류: {str(e)}"
            print(error_msg)
            try:
                export_upload_result(aws_link, selected_tag, "aws_apply", ":failed:")
            except:
                print("[서버최신강제패치] export_upload_result 오류")
            raise

    @staticmethod
    def delete_server_container(driver, aws_link: str):
        """서버 컨테이너 삭제 (모두 선택)"""
        try:
            print(f"[delete_server_container] 시작")
            print(f"[delete_server_container] AWS URL: {aws_link}")
            
            if driver is None:
                print("[delete_server_container] 드라이버 시작 중...")
                
                # 기존 Chrome 및 ChromeDriver 프로세스 정리
                AWSManager.cleanup_chrome_processes()
                
                driver = AWSManager.start_driver()
                driver.implicitly_wait(10)
                
                print(f"[delete_server_container] AWS 페이지 이동: {aws_link}")
                driver.get(aws_link)
                
                # 페이지 로드 대기 (추가)
                time.sleep(2)
                
                AWSManager._ensure_aws_deploy_social_oidc_clicked(driver, "[delete_server_container]")
                AWSManager._ensure_keycloak_login(driver, "[delete_server_container]")

            # 페이지 완전 로드 대기 (추가)
            print("[delete_server_container] 페이지 로딩 대기 중...")
            time.sleep(2)
            
            driver.implicitly_wait(10)
            print("[delete_server_container] 삭제 작업 시작...")
            
            # 대기 시간 증가: 20초 → 30초
            wait = WebDriverWait(driver, 30)
            
            # CONTAINER GAMESERVERS 클릭
            try:
                print("[delete_server_container] [단계 1/4] CONTAINER GAMESERVERS 탭 대기 중...")
                container_tab = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/ul/li[3]/a/span")))
                print("[delete_server_container] [단계 1/4] 탭 요소 발견, 클릭...")
                AWSManager._safe_click(driver, container_tab)
                time.sleep(1)
                print("[delete_server_container] [단계 1/4] ✅ CONTAINER GAMESERVERS 탭 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 1/4 실패] CONTAINER GAMESERVERS 탭을 찾을 수 없습니다. 페이지가 완전히 로드되지 않았거나 로그인이 필요할 수 있습니다. XPath: /html/body/div[1]/div[3]/div/div[2]/ul/li[3]/a/span")

            # Select all 버튼 클릭
            try:
                print("[delete_server_container] [단계 2/4] Select All 버튼 클릭")
                select_all_btn = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[1]")))
                AWSManager._safe_click(driver, select_all_btn)
                time.sleep(0.5)
                print("[delete_server_container] [단계 2/4] ✅ Select All 버튼 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 2/4 실패] Select All 버튼을 찾을 수 없습니다. XPath: /html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[1]")

            # Delete Servers 버튼 클릭
            try:
                print("[delete_server_container] [단계 3/4] Delete Servers 버튼 클릭")
                delete_btn = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[4]")))
                AWSManager._safe_click(driver, delete_btn)
                time.sleep(0.5)
                print("[delete_server_container] [단계 3/4] ✅ Delete Servers 버튼 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 3/4 실패] Delete Servers 버튼을 찾을 수 없습니다. XPath: /html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[4]")

            # YES 버튼 클릭
            try:
                print("[delete_server_container] [단계 4/4] YES 버튼 클릭")
                yes_btn = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[1]/div[2]/div/button[1]")))
                AWSManager._safe_click(driver, yes_btn)
                time.sleep(0.5)
                print("[delete_server_container] [단계 4/4] ✅ YES 버튼 클릭 완료")
            except TimeoutException as e:
                raise Exception(f"[단계 4/4 실패] 확인 팝업의 YES 버튼을 찾을 수 없습니다. XPath: /html/body/div[3]/div[1]/div[2]/div/button[1]")
            
            print("[delete_server_container] ✅ 서버 삭제 작업 완료")
            
        except TimeoutException as e:
            error_msg = f"[delete_server_container] ❌ 타임아웃: {str(e)}"
            print(error_msg)
            # 원본 예외를 그대로 발생시켜 단계 정보 유지
            raise
        except Exception as e:
            error_msg = f"[delete_server_container] ❌ 서버 삭제 오류: {str(e)}"
            print(error_msg)
            # 예외를 다시 발생시켜서 호출자에게 실패를 알림 (단계 정보 포함)
            raise
    
    @staticmethod
    def run_teamcity_build(driver, url_link: str = 'https://pbbseoul6-w.bluehole.net/buildConfiguration/BlackBudget_CompileBuild?mode=builds#all-projects',
                          branch: str = 'game', is_debug: bool = False,
                          teamcity_id: str = '', teamcity_pw: str = ''):
        """TeamCity 빌드 실행"""
        try:
            if driver is None:
                print("[빌드굽기] 드라이버 시작 중...")
                
                # 기존 Chrome 및 ChromeDriver 프로세스 정리
                AWSManager.cleanup_chrome_processes()
                
                driver = AWSManager.start_driver()
                driver.implicitly_wait(10)
            
            # driver가 이미 존재해도 항상 목표 URL로 이동
            print(f"[빌드굽기] TeamCity 페이지 이동: {url_link}")
            driver.get(url_link)

            # 자동 로그인 먼저 시도 (미로그인 시 로그인 페이지로 리다이렉트되므로, wait_for_teamcity_page_ready 전에 로그인 수행)
            AWSManager.teamcity_auto_login(driver, teamcity_id, teamcity_pw)
            driver.get(url_link)
            AWSManager.wait_for_teamcity_page_ready(driver, url_link, timeout=30)
            
            wait = WebDriverWait(driver, 20)
            
            # RUN 버튼 클릭 (재시도 로직)
            run_button_clicked = False
            print(f"[빌드굽기] [단계 1/9] RUN 버튼 클릭 (브랜치: {branch})")
            for attempt in range(3):
                try:
                    button = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content-tag"]/div[4]/div/div[1]/div[1]/div/div[1]/div/button')))
                    AWSManager._safe_click(driver, button)
                    run_button_clicked = True
                    print(f"[빌드굽기] [단계 1/9] ✅ RUN 버튼 클릭 완료 (시도 {attempt + 1}/3)")
                    break
                except StaleElementReferenceException:
                    print(f"[빌드굽기] [단계 1/9] StaleElementReferenceException, 재시도 중... ({attempt + 1}/3)")
                    time.sleep(1)
                    continue
                except TimeoutException:
                    if attempt == 2:
                        raise Exception(f"[단계 1/9 실패] RUN 버튼을 찾을 수 없습니다 (3번 시도 실패). XPath: //*[@id=\"main-content-tag\"]/div[4]/div/div[1]/div[1]/div/div[1]/div/button")
                    time.sleep(1)
                    continue
            
            if not run_button_clicked:
                raise Exception(f"[단계 1/9 실패] RUN 버튼 클릭 실패")
            
            # 탭 네비게이션
            try:
                print("[빌드굽기] [단계 2/9] 탭 0 클릭")
                tab0 = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tab-0"]/p/a')))
                AWSManager._safe_click(driver, tab0)
                time.sleep(0.5)
                print("[빌드굽기] [단계 2/9] ✅ 탭 0 클릭 완료")
            except TimeoutException:
                raise Exception(f"[단계 2/9 실패] 탭 0을 찾을 수 없습니다. XPath: //*[@id=\"tab-0\"]/p/a")

            try:
                print("[빌드굽기] [단계 3/9] moveToTop 클릭")
                AWSManager._safe_click(driver, driver.find_element(By.XPATH, '//*[@id="moveToTop"]'))
                time.sleep(0.5)
                print("[빌드굽기] [단계 3/9] ✅ moveToTop 클릭 완료")
            except TimeoutException:
                raise Exception(f"[단계 3/9 실패] moveToTop 버튼을 찾을 수 없습니다. XPath: //*[@id=\"moveToTop\"]")

            try:
                print("[빌드굽기] [단계 4/9] 탭 2 클릭")
                tab2 = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tab-2"]/p/a')))
                AWSManager._safe_click(driver, tab2)
                time.sleep(0.5)
                print("[빌드굽기] [단계 4/9] ✅ 탭 2 클릭 완료")
            except TimeoutException:
                raise Exception(f"[단계 4/9 실패] 탭 2를 찾을 수 없습니다. XPath: //*[@id=\"tab-2\"]/p/a")

            try:
                print("[빌드굽기] [단계 5/9] 브랜치 선택기 열기")
                branch_selector = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="runBranchSelector_container"]/span/button/span[2]')))
                AWSManager._safe_click(driver, branch_selector)
                time.sleep(0.5)
                print("[빌드굽기] [단계 5/9] ✅ 브랜치 선택기 열기 완료")
            except TimeoutException:
                raise Exception(f"[단계 5/9 실패] 브랜치 선택기를 찾을 수 없습니다. XPath: //*[@id=\"runBranchSelector_container\"]/span/button/span[3]/span")
            
            # 브랜치 선택
            try:
                print(f"[빌드굽기] [단계 6/9] 브랜치 '{branch}' 입력 및 선택")
                input_box = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Filter branches"]')))
                input_box.send_keys(branch)
                time.sleep(1)
                
                branch_option = wait.until(EC.presence_of_element_located((By.XPATH, f'//span[@class="ring-list-label" and @title="{branch}"]')))
                AWSManager._safe_click(driver, branch_option)
                print(f"[빌드굽기] [단계 6/9] ✅ 브랜치 '{branch}' 선택 완료")
            except TimeoutException:
                raise Exception(f"[단계 6/9 실패] 브랜치 '{branch}'를 찾을 수 없습니다. 브랜치명이 정확한지 확인하세요.")
            
            try:
                time.sleep(3)
                print("[빌드굽기] [단계 7/9] 탭 3 클릭")
                tab3 = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tab-3"]/p/a')))
                AWSManager._safe_click(driver, tab3)
                time.sleep(0.5)
                print("[빌드굽기] [단계 7/9] ✅ 탭 3 클릭 완료")
            except TimeoutException:
                raise Exception(f"[단계 7/9 실패] 탭 3을 찾을 수 없습니다. XPath: //*[@id=\"tab-3\"]/p/a")
            
            # 옵션 설정
            try:
                print("[빌드굽기] [단계 8/9] 빌드 옵션 설정")
                # option1 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mcb_custom_control_parameter_build_creation_cfg_8054699_container_3"]')))
                # option1.click()
                AWSManager._safe_click(driver, driver.find_element(By.XPATH, '//*[@id="mcb_custom_control_parameter_build_creation_cfg_8054699_container_3"]'))
                time.sleep(0.3)

                AWSManager._safe_click(driver, driver.find_element(By.XPATH, '//*[@id="parameter_build_docker_2083990112"]'))
                time.sleep(0.5)
                
                # docker_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="parameter_build_docker_2083990112"]')))
                # docker_option.click()
                # time.sleep(0.5)
                print("[빌드굽기] [단계 8/9] ✅ 빌드 옵션 설정 완료")
            except TimeoutException:
                raise Exception(f"[단계 8/9 실패] 빌드 옵션 설정 요소를 찾을 수 없습니다. TeamCity 페이지 구조가 변경되었을 수 있습니다.")
            
            if not is_debug:
                try:
                    print("[빌드굽기] [단계 9/9] 최종 Run 버튼 클릭")
                    run_custom_build = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="runCustomBuildButton"]')))
                    AWSManager._safe_click(driver, run_custom_build)
                    print("[빌드굽기] [단계 9/9] ✅ 최종 Run 버튼 클릭 완료")
                except TimeoutException:
                    raise Exception(f"[단계 9/9 실패] 최종 Run 버튼을 찾을 수 없습니다. XPath: //*[@id=\"runCustomBuildButton\"]")
            
            print("[빌드굽기] ✅ 빌드 실행 완료")
            
        except TimeoutException as e:
            error_msg = f"[빌드굽기] ❌ 타임아웃: {str(e)}"
            print(error_msg)
            raise
        except Exception as e:
            error_msg = f"[빌드굽기] ❌ 오류: {str(e)}"
            print(error_msg)
            raise

