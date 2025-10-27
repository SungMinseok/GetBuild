"""AWS 배포 관련 작업 모듈 (기존 aws.py 정리 버전)"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import chromedriver_autoinstaller
import subprocess
import time
import requests
import re
from exporter import export_upload_result


class AWSManager:
    """AWS 배포 관련 작업 관리"""
    
    @staticmethod
    def start_driver():
        """Chrome 디버깅 모드 드라이버 시작"""
        chrome_debugging_address = "http://127.0.0.1:9222/json"
        chrome_user_data_dir = r'"C:\ChromeTEMP"'
        chrome_executable_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
        
        try:
            # 이미 실행 중인지 확인
            response = requests.get(chrome_debugging_address)
            if response.status_code == 200:
                chrome_options = Options()
                chrome_options.debugger_address = "127.0.0.1:9222"
                driver = webdriver.Chrome(options=chrome_options)
                
                # 새 탭 열기
                driver.execute_script("window.open('');")
                new_tab = driver.window_handles[-1]
                driver.switch_to.window(new_tab)
                return driver
        except requests.ConnectionError:
            pass
        
        # 새로 시작
        subprocess.Popen(f'{chrome_executable_path} --remote-debugging-port=9222 --user-data-dir={chrome_user_data_dir}')
        time.sleep(2)
        
        chrome_options = Options()
        chrome_options.debugger_address = "127.0.0.1:9222"
        chromedriver_autoinstaller.install(True)
        driver = webdriver.Chrome(options=chrome_options)
        
        # 새 탭 열기
        driver.execute_script("window.open('');")
        new_tab = driver.window_handles[-1]
        driver.switch_to.window(new_tab)
        
        return driver
    
    @staticmethod
    def upload_server_build(driver, revision: int, zip_path: str, aws_link: str, 
                           branch: str = 'game', build_type: str = 'DEV', 
                           full_build_name: str = 'TEST'):
        """서버 빌드 업로드"""
        try:
            if driver is None:
                driver = AWSManager.start_driver()
                driver.implicitly_wait(10)
                driver.get(aws_link)
                driver.implicitly_wait(10)
                try:
                    driver.find_element(By.XPATH, '//*[@id="social-oidc"]').click()
                except:
                    print('로그인 스킵...')
            
            driver.implicitly_wait(10)
            
            # CONTAINER GAMESERVERS 클릭
            driver.find_element(By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/ul/li[3]/a/span").click()
            driver.implicitly_wait(5)
            time.sleep(0.5)
            
            # UPLOAD CUSTOM SERVER 클릭
            driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[6]/span/span').click()
            time.sleep(0.5)
            driver.implicitly_wait(5)
            
            # Your local location
            val_yourLocalLocation = '/html/body/div[3]/div[1]/div[2]/form/div[1]/div[2]/div/div'
            driver.find_element(By.XPATH, val_yourLocalLocation).click()
            driver.find_element(By.XPATH, val_yourLocalLocation).send_keys('Seoul')
            driver.find_element(By.XPATH, val_yourLocalLocation).send_keys(Keys.RETURN)
            time.sleep(0.5)
            
            # Branch
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/form/div[2]/div[2]/div/input').send_keys(branch)
            
            # Revision
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/form/div[3]/div[2]/div/input').send_keys(f'{build_type}_{revision}')
            
            # Input File
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/form/div[4]/div[2]/input').send_keys(zip_path)
            
            # Upload 버튼 클릭
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/form/div[5]/div/button').click()
            driver.implicitly_wait(5)
            
            # 업로드 진행률 모니터링
            count = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/form/div[6]/div/div/div[2]')
            while True:
                text = count.text
                match = re.findall(r"\d+\.\d+|\d+", text)
                if match:
                    progress_value = float(match[0])
                    print(f"업로드 진행률: {progress_value}%")
                    if progress_value >= 100:
                        print("커스텀 업로드 완료")
                        try:
                            export_upload_result(aws_link, full_build_name, "aws_upload", ":update_done:")
                        except:
                            print("export_upload_result 오류")
                        time.sleep(1)
                        break
                else:
                    print("진행률 추출 실패:", text)
                time.sleep(1)
        except Exception as e:
            print(f"업로드 오류: {e}")
            try:
                export_upload_result(aws_link, full_build_name, "aws_upload", ":failed:")
            except:
                print("export_upload_result 오류")
    
    @staticmethod
    def update_server_container(driver, revision: int, aws_link: str, branch: str = 'game', 
                               build_type: str = 'DEV', is_debug: bool = False, 
                               full_build_name: str = 'none'):
        """서버 컨테이너 패치"""
        try:
            if branch == "":
                branch = 'game'
            
            if driver is None:
                driver = AWSManager.start_driver()
                driver.implicitly_wait(10)
                driver.get(aws_link)
                driver.implicitly_wait(10)
                try:
                    driver.find_element(By.XPATH, '//*[@id="social-oidc"]').click()
                except:
                    print('로그인 스킵...')
            
            driver.implicitly_wait(10)
            
            # CONTAINER GAMESERVERS 클릭
            driver.find_element(By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/ul/li[3]/a/span").click()
            driver.implicitly_wait(5)
            time.sleep(0.5)
            
            # SELECT ALL
            driver.find_element(By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[1]").click()
            driver.implicitly_wait(5)
            
            # 돋보기 (필터)
            driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/div/button').click()
            time.sleep(0.5)
            driver.implicitly_wait(5)
            
            # 브랜치 입력
            time.sleep(1.5)
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(branch)
            time.sleep(1.5)
            
            # 정확히 일치하는 branch 선택
            for x in range(1, 10):
                try:
                    element = driver.find_element(By.XPATH, f'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[{x}]/span')
                    if element.text == branch:
                        element.click()
                        break
                except Exception as e:
                    print(f"요소 {x} 찾기 실패: {e}")
            
            time.sleep(0.5)
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]').click()
            
            # TAG 입력
            time.sleep(1)
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(f'{branch}-{build_type}_{revision}')
            time.sleep(1)
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[1]/span').click()
            time.sleep(0.5)
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]').click()
            
            # Build config 체크박스
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div/div/div[2]').click()
            time.sleep(0.5)
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]').click()
            
            # SELECT 클릭
            time.sleep(0.5)
            driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/button').click()
            
            # APPLY 클릭
            time.sleep(0.5)
            driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[3]').click()
            
            if not is_debug:
                # 팝업 OK 버튼
                time.sleep(0.5)
                driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/div/button[1]').click()
                try:
                    export_upload_result(aws_link, full_build_name, "aws_apply", ":update_done:")
                except:
                    print("export_upload_result 오류")
        except Exception as e:
            print(f"패치 오류: {e}")
            try:
                export_upload_result(aws_link, full_build_name, "aws_apply", ":failed:")
            except:
                print("export_upload_result 오류")
    
    @staticmethod
    def run_teamcity_build(driver, url_link: str = 'https://pbbseoul6-w.bluehole.net/buildConfiguration/BlackBudget_CompileBuild?mode=builds#all-projects',
                          branch: str = 'game', is_debug: bool = False):
        """TeamCity 빌드 실행"""
        if driver is None:
            driver = AWSManager.start_driver()
            driver.implicitly_wait(10)
            driver.get(url_link)
        
        wait = WebDriverWait(driver, 10)
        
        # RUN 버튼 클릭 (재시도 로직)
        for _ in range(3):
            try:
                button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content-tag"]/div[4]/div/div[1]/div[1]/div/div[1]/div/button')))
                button.click()
                break
            except StaleElementReferenceException:
                print("StaleElementReferenceException, 재시도...")
                continue
            except TimeoutException:
                print("버튼을 찾지 못했습니다.")
                break
        
        driver.find_element(By.XPATH, '//*[@id="tab-0"]/p/a').click()
        driver.implicitly_wait(5)
        
        driver.find_element(By.XPATH, '//*[@id="moveToTop"]').click()
        driver.implicitly_wait(5)
        
        driver.find_element(By.XPATH, '//*[@id="tab-2"]/p/a').click()
        driver.implicitly_wait(5)
        
        driver.find_element(By.XPATH, '//*[@id="runBranchSelector_container"]/span/button/span[3]/span').click()
        driver.implicitly_wait(5)
        
        # 브랜치 선택
        wait = WebDriverWait(driver, 10)
        input_box = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Filter branches"]')))
        input_box.send_keys(branch)
        
        button = wait.until(EC.element_to_be_clickable((By.XPATH, f'//span[@class="ring-list-label" and @title="{branch}"]')))
        button.click()
        
        time.sleep(3)
        driver.find_element(By.XPATH, '//*[@id="tab-3"]/p/a').click()
        driver.implicitly_wait(5)
        
        # 옵션 설정
        driver.find_element(By.XPATH, '//*[@id="mcb_custom_control_parameter_build_creation_cfg_8054699_container_2"]').click()
        driver.find_element(By.XPATH, '//*[@id="mcb_custom_control_parameter_build_creation_cfg_8054699_container_3"]').click()
        driver.implicitly_wait(5)
        
        driver.find_element(By.XPATH, '//*[@id="parameter_build_docker_2083990112"]').click()
        driver.implicitly_wait(5)
        
        if not is_debug:
            driver.find_element(By.XPATH, '//*[@id="runCustomBuildButton"]').click()

