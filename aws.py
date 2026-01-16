from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import subprocess
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import requests
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from exporter import export_upload_result

# def start_driver():
#     #driver_name = fr"C:\chromedriver-win64\chromedriver.exe"
#     subprocess.Popen(fr'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\ChromeTEMP')

#     chrome_options = Options()
#     chrome_options.debugger_address = "127.0.0.1:9222"
#     chromedriver_autoinstaller.install(True)
#     driver = webdriver.Chrome( options=chrome_options)
    
#     return driver

def start_driver():
    chrome_debugging_address = "http://127.0.0.1:9222/json"
    chrome_user_data_dir = r'"C:\ChromeTEMP"'
    chrome_executable_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    
    try:
        # Check if Chrome is already running with remote debugging
        response = requests.get(chrome_debugging_address)
        if response.status_code == 200:
            # If running, connect to the existing instance
            chrome_options = Options()
            chrome_options.debugger_address = "127.0.0.1:9222"
            driver = webdriver.Chrome(options=chrome_options)
            
            # Open a new tab and switch to it
            driver.execute_script("window.open('');")
            new_tab = driver.window_handles[-1]
            driver.switch_to.window(new_tab)
            
            return driver
    except requests.ConnectionError:
        pass # Continue to start a new instance

    # If not running, start a new instance
    subprocess.Popen(f'{chrome_executable_path} --remote-debugging-port=9222 --user-data-dir={chrome_user_data_dir}')

    # Wait for the Chrome instance to start
    time.sleep(2)

    chrome_options = Options()
    chrome_options.debugger_address = "127.0.0.1:9222"
    chromedriver_autoinstaller.install(True)
    driver = webdriver.Chrome(options=chrome_options)
    
    # Open a new tab and switch to it
    driver.execute_script("window.open('');")
    new_tab = driver.window_handles[-1]
    driver.switch_to.window(new_tab)
    
    return driver


def aws_update_custom(driver,revision,aws_link, branch = 'game'):
    
    if driver == None :
        driver = start_driver()

        driver.implicitly_wait(10)
        #driver.get("https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2")
        driver.get(aws_link)


        driver.implicitly_wait(10)
        try:
            driver.find_element(By.XPATH,'//*[@id="social-oidc"]').click()
        except:
            print('pass login...')
            pass
    driver.implicitly_wait(10)
    #GAMESERVER
    driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/ul/li[3]").click()
    driver.implicitly_wait(5)
    time.sleep(0.5)
    #CHECKBOX
    driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div/div/table/thead/tr[1]/th[1]/div/span/span/div/div[2]").click()

    
    driver.implicitly_wait(5)
    #MENU
    driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div/div/table/thead/tr[1]/th[10]/div/span/span[1]/button').click()
    time.sleep(0.5)
    driver.implicitly_wait(5)
    #MENU - update
    driver.find_element(By.XPATH,'/html/body/div[4]/div/ul/li[1]/div/div').click()
    time.sleep(0.5)
    driver.implicitly_wait(5)
    #os.system("pause")
    
    driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/fieldset/div/div/div[2]/div[2]/div/button').click()
    time.sleep(0.5)
    
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys('CUSTOM')
    time.sleep(1.5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li/span').click()
    time.sleep(0.5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
    time.sleep(1.5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(branch)
    time.sleep(1.5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li/span').click()
    time.sleep(0.5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
    time.sleep(1)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(f'{revision}')
    time.sleep(1)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li/span').click()
    time.sleep(0.5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
    time.sleep(0.5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/button').click()
    time.sleep(0.5)
    driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/fieldset/div/div/div[4]/div/button').click()
    time.sleep(0.5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/button[1]').click()
    #os.system("pause")

# def aws_update_sel(driver,revision,aws_link, branch = 'game'):
#     if branch == "":
#         branch = 'game';

#     if driver == None :
#         driver = start_driver()

#         driver.implicitly_wait(10)
#         #driver.get("https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2")
#         driver.get(aws_link)


#         driver.implicitly_wait(10)
#         try:
#             driver.find_element(By.XPATH,'//*[@id="social-oidc"]').click()
#         except:
#             print('pass login...')
#             pass
#     driver.implicitly_wait(10)
#     #GAMESERVER
#     driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/ul/li[3]").click()
#     driver.implicitly_wait(5)
#     time.sleep(0.5)
#     #CHECKBOX
#     driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div/div/table/thead/tr[1]/th[1]/div/span/span/div/div[2]").click()

    
#     driver.implicitly_wait(5)
#     #MENU
#     driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div/div/table/thead/tr[1]/th[10]/div/span/span[1]/button').click()
#     time.sleep(0.5)
#     driver.implicitly_wait(5)
#     #MENU - update
#     driver.find_element(By.XPATH,'/html/body/div[4]/div/ul/li[1]/div/div').click()
#     time.sleep(0.5)
#     driver.implicitly_wait(5)
#     #os.system("pause")
    
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/fieldset/div/div/div[2]/div[2]/div/button').click()
#     time.sleep(0.5)
    
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys('SEL')
#     time.sleep(1.5)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li/span').click()
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
#     time.sleep(1.5)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(branch)
#     time.sleep(1.5)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li/span').click()
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
#     time.sleep(1)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(f'{revision}')
#     time.sleep(1)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li/span').click()
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/button').click()
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/fieldset/div/div/div[4]/div/button').click()
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/button[1]').click()
#     #os.system("pause")

def aws_update_container(driver,revision, aws_link, branch = 'game', buildType = 'DEV', isDebug = False, full_build_name = 'none'):
    '''서버패치'''
    try:
        if branch == "":
            branch = 'game'

        if driver == None :
            driver = start_driver()

            driver.implicitly_wait(10)
            #driver.get("https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2")
            driver.get(aws_link)


            driver.implicitly_wait(10)
            try:
                driver.find_element(By.XPATH,'//*[@id="social-oidc"]').click()
            except:
                print('pass login...')
                pass
        driver.implicitly_wait(10)
        #CONTAINER GAMESERVERS
        driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/ul/li[3]/a/span").click()
        driver.implicitly_wait(5)
        time.sleep(0.5)
        #SELECT ALL
        driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[1]").click()

        
        driver.implicitly_wait(5)
        #돋보기
        driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/div/button').click()
        time.sleep(0.5)
        driver.implicitly_wait(5)

        #브랜치입력
        time.sleep(1.5)
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(branch)
        time.sleep(1.5)
        #추후 소문자/대문자 구분해서 정확히 일치하는 것 클릭하도록 변경 필요
    # /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[1]/span
    # /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[2]/span
    # /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[5]/span
        #driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[2]/span').click()
            
            # branch 값과 일치하는 요소 클릭
        for x in range(1, 10):  # 예시: 1부터 9까지 반복
            try:
                element = driver.find_element(By.XPATH, f'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[{x}]/span')
                if element.text == branch:
                    element.click()
                    break
            except Exception as e:
                print(f"요소 {x} 찾기 실패: {e}")
        
        
        
        
        time.sleep(0.5)
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]').click()
        
        #TAG 입력
        time.sleep(1)
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(f'{branch}-{buildType}_{revision}')
        time.sleep(1)
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[1]/span').click()
        time.sleep(0.5)
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]').click()

        #Build config 체크박스 클릭
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div/div/div[2]').click()
        time.sleep(0.5)
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]').click()

        
        #SELCET 클릭
        time.sleep(0.5)
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/button').click()

        #APPLY 클릭
        time.sleep(0.5)
        driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[3]').click()
        
        if not isDebug :
            #팝업 내 OK 버튼 클릭
            time.sleep(0.5)
            driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/button[1]').click()
            time.sleep(0.5)
            #마지막 버튼 클릭
            driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/form/fieldset/div/div/div[7]/div/button').click()
            try:
                export_upload_result(aws_link,full_build_name,"aws_apply",":update_done:")
            except:
                print("export_upload_result error")
    except:
        try:
            export_upload_result(aws_link,full_build_name,"aws_apply",":failed:")
        except:
            print("export_upload_result error")



def aws_upload_custom2(driver,revision,zip_path,aws_link, branch = 'game',buildType = 'DEV', full_build_name = 'TEST'):
    '''250204'''
    try:
        if driver == None :
            driver = start_driver()

            driver.implicitly_wait(10)
            #driver.get("https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2")
            driver.get(aws_link)


            driver.implicitly_wait(10)
            try:
                driver.find_element(By.XPATH,'//*[@id="social-oidc"]').click()
            except:
                print('pass login...')
                pass
        driver.implicitly_wait(10)

        #CONTAINER GAMESERVERS
        driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/ul/li[3]/a/span").click()
        driver.implicitly_wait(5)
        time.sleep(0.5)

        #UPLOAD CUSTOM SERVER
        driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/form/div/button[6]/span/span').click()
        time.sleep(0.5)
        driver.implicitly_wait(5)

        #Your local location
        val_yourLocalLocation = '/html/body/div[3]/div[1]/div[2]/form/div[1]/div[2]/div/div'
        driver.find_element(By.XPATH,val_yourLocalLocation).click()
        driver.find_element(By.XPATH,val_yourLocalLocation).send_keys('Seoul')
        driver.find_element(By.XPATH,val_yourLocalLocation).send_keys(Keys.RETURN)
        time.sleep(0.5)
        driver.implicitly_wait(5)

        #Branch
        val_branch=branch
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/div[2]/div[2]/div/input').send_keys(val_branch)
        
        #Revision
        val_buildType = buildType
        val_revision = revision
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/div[3]/div[2]/div/input').send_keys(f'{val_buildType}_{val_revision}')


        #Input File
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/div[4]/div[2]/input').send_keys(zip_path)

        #Upload 버튼 클릭
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/div[5]/div/button').click()
        
        driver.implicitly_wait(5)
        #time.sleep(1)
        #for i in range(0,10):
        import re
        count = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[2]/form/div[6]/div/div/div[2]')
        while True:
            text = count.text  # 예: '11.17%'
            # 소수점 포함 숫자 추출
            match = re.findall(r"\d+\.\d+|\d+", text)
            if match:
                progress_value = float(match[0])  # 첫 번째 값을 사용
                print(progress_value)
                if progress_value >= 100:
                    print("커스텀 업로드 완료")
                    
                    try:
                        export_upload_result(aws_link,full_build_name,"aws_upload",":update_done:")
                    except:
                        print("export_upload_result error")
                    time.sleep(1)
                    break
            else:
                print("숫자를 추출하지 못함:", text)
            time.sleep(1)
    except:
        
        try:
            export_upload_result(aws_link,full_build_name,"aws_upload",":failed:")
        except:
            print("export_upload_result error")
        time.sleep(1)
        #break
        


def aws_delete(driver,revision,zip_path,aws_links):
    '''250220'''
    if driver == None :
        driver = start_driver()
        driver.implicitly_wait(10)
        driver.get(aws_link)


        driver.implicitly_wait(10)
        try:
            driver.find_element(By.XPATH,'//*[@id="social-oidc"]').click()
        except:
            print('pass login...')
            pass
    driver.implicitly_wait(10)

    for i in range(0,len(aws_link)):

        #CONTAINER GAMESERVERS
        driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/ul/li[4]/a").click()
        driver.implicitly_wait(5)
        time.sleep(0.5)

        #Select all
        driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div[1]/div/form/div/button[1]").click()
        time.sleep(0.5)
        driver.implicitly_wait(5)


def run_teamcity(driver, url_link='https://pbbseoul6-w.bluehole.net/buildConfiguration/BlackBudget_CompileBuild?mode=builds#all-projects', branch='game', isDebug = False):
    
    if driver == None :
        driver = start_driver()
        driver.implicitly_wait(10)
        driver.get(url_link)

        # driver.implicitly_wait(10)
        # try:
        #     driver.find_element(By.XPATH,'//*[@id="social-oidc"]').click()
        # except:
        #     print('pass login...')
        #     pass
    #driver.implicitly_wait(10)
    #RUN
    #driver.find_element(By.XPATH,'//*[@id="main-content-tag"]/div[4]/div/div[1]/div[1]/div/div[1]/div/button').click()
    # wait = WebDriverWait(driver, 10)
    # button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content-tag"]/div[4]/div/div[1]/div[1]/div/div[1]/div/button')))
    # button.click()
    # driver.implicitly_wait(5) # 
    # time.sleep(1)

    wait = WebDriverWait(driver, 10)
    for _ in range(3):  # 최대 3번 재시도
        try:
            button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content-tag"]/div[4]/div/div[1]/div[1]/div/div[1]/div/button')))
            button.click()
            break
        except StaleElementReferenceException:
            print("StaleElementReferenceException 발생, 버튼을 다시 찾습니다.")
            continue
        except TimeoutException:
            print("버튼을 찾지 못했습니다.")
            break

    driver.find_element(By.XPATH,'//*[@id="tab-0"]/p/a').click()
    driver.implicitly_wait(5)

    driver.find_element(By.XPATH,'//*[@id="moveToTop"]').click()
    driver.implicitly_wait(5)


    driver.find_element(By.XPATH,'//*[@id="tab-2"]/p/a').click()
    driver.implicitly_wait(5)

    driver.find_element(By.XPATH,'//*[@id="runBranchSelector_container"]/span/button/span[3]/span').click()
    driver.implicitly_wait(5) 

    wait = WebDriverWait(driver, 10)
    input_box = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Filter branches"]')))
    input_box.send_keys(branch)
    
    wait = WebDriverWait(driver, 10)
    button = wait.until(EC.element_to_be_clickable((By.XPATH, f'//span[@class="ring-list-label" and @title="{branch}"]')))

    button.click()

    time.sleep(3)
    driver.find_element(By.XPATH,'//*[@id="tab-3"]/p/a').click()
    driver.implicitly_wait(5) #

    #dev 해제, Test 추가가

    driver.find_element(By.XPATH,'//*[@id="mcb_custom_control_parameter_build_creation_cfg_8054699_container_2"]').click()
    driver.find_element(By.XPATH,'//*[@id="mcb_custom_control_parameter_build_creation_cfg_8054699_container_3"]').click()
    driver.implicitly_wait(5) #

    driver.find_element(By.XPATH,'//*[@id="parameter_build_docker_2083990112"]').click()
    driver.implicitly_wait(5) #

    # driver.find_element(By.XPATH,'//*[@id="parameter_build_zip_1402101855"]').click()
    # driver.implicitly_wait(5) #

    # driver.find_element(By.XPATH,'//*[@id="parameter_build_zip_by_build_type_587265756"]').click()
    # driver.implicitly_wait(5) #

    # driver.find_element(By.XPATH,'//*[@id="parameter_upload_aws_s3_192415550"]').click()
    # driver.implicitly_wait(5) #

    # driver.find_element(By.XPATH,'//*[@id="parameter_upload_aws_s3_bucket_495183514"]').send_keys('SEL')

    if not isDebug:
        driver.find_element(By.XPATH,'//*[@id="runCustomBuildButton"]').click()
        return
    #driver.find_element(By.XPATH,'//*[@id="runCustomBuildButton"]').click()
    



    #SELECT ALL
#     driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div[1]/div/form/div/button[1]").click()

    
#     driver.implicitly_wait(5)
#     #돋보기
#     driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div[1]/div/form/div/div/button').click()
#     time.sleep(0.5)
#     driver.implicitly_wait(5)

#     #브랜치입력
#     time.sleep(1.5)
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(branch)
#     time.sleep(1.5)
#     #추후 소문자/대문자 구분해서 정확히 일치하는 것 클릭하도록 변경 필요
# # /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[1]/span
# # /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[2]/span
# # /html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[5]/span
#     #driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[2]/span').click()
        
#         # branch 값과 일치하는 요소 클릭
#     for x in range(1, 10):  # 예시: 1부터 9까지 반복
#         try:
#             element = driver.find_element(By.XPATH, f'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[{x}]/span')
#             if element.text == branch:
#                 element.click()
#                 break
#         except Exception as e:
#             print(f"요소 {x} 찾기 실패: {e}")
    
    
    
    
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
#     #TAG 입력
#     time.sleep(1)
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(f'{branch}-{buildType}_{revision}')
#     time.sleep(1)
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li[1]/span').click()
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]').click()

#     #Build config 체크박스 클릭
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/div/div/div[2]').click()
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[2]/a[2]').click()

    
#     #SELCET 클릭
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/div/div[1]/div/button').click()

#     #APPLY 클릭
#     time.sleep(0.5)
#     driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div[1]/div/form/div/button[3]').click()
    
#     if not isDebug :
#         #팝업 내 OK 버튼 클릭
#         time.sleep(0.5)
#         driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/button[1]').click()
#         #os.system("pause")





def aws_stop():
    
    driver = jira2.start_driver()

    driver.implicitly_wait(10)
    #driver.get("https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2")
    driver.get("https://awsdeploy.pbb-qa.pubg.io/environment")
    
    title_list = []
    driver.implicitly_wait(5)
    for i in range(1,99):
        try:
            temp_name = driver.find_element(By.XPATH,f'/html/body/div[1]/div[3]/div/div[2]/div/table/tbody/tr[{i}]/td[1]/span')
            title = temp_name.get_attribute("title")
            title_list.append(title)
            print(title)        
        except: 
            break
    print(len(title_list))
    os.system("pause")
    




if __name__ == '__main__':
    #driver = start_driver()
    #run_teamcity(None,branch='Ftr_hideoutstriketeam',isDebug=True)
    #run_teamcity(None,branch='game_progression',isDebug=True)
    # zip_path = fr'C:\mybuild\CompileBuild_DEV_game_SEL114483_158662\WindowsServer.zip'
    # aws_link = "https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2"

    # driver = start_driver()

    # driver.implicitly_wait(10)
    # #driver.get("https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2")
    # driver.get("https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2")


    # driver.implicitly_wait(10)
    # try:
    #     driver.find_element(By.XPATH,'//*[@id="social-oidc"]').click()
    # except:
    #     print('pass login...')
    #     pass

    aws_link = "https://awsdeploy.pbb-qa.pubg.io/environment/sel-game5"
    
    # aws_upload_custom(driver,"157023_a",zip_path)
    #aws_update_custom(driver,"159435",aws_link=aws_link)

    aws_update_container(driver= None,revision=213917,aws_link='https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2',branch='game',
                        buildType='TEST',isDebug=True)

    #aws_stop()
    #aws_upload_custom2(driver=None,revision="252251",zip_path,aws_link=aws_link,branch='stage_coreloop')
    os.system("pause")
