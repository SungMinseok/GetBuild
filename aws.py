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

def aws_upload_custom(driver, revision, zip_path, aws_link, branch = 'game'):
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
    driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/ul/li[3]").click()
    driver.implicitly_wait(5)
    driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div/div/table/tbody/tr[1]/td[10]/span/button[1]').click()
    driver.implicitly_wait(5)
    driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/fieldset/div/div/div[3]/div/button').click()
    driver.implicitly_wait(5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/form/div[1]/div[2]/div/div').send_keys('seoul')
    driver.find_element(By.XPATH,'//*[@id="Branch"]').send_keys(branch)
    driver.find_element(By.XPATH,'//*[@id="Revision"]').send_keys(f'{revision}')
    driver.implicitly_wait(5)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/form/div[4]/div[2]/input').send_keys(zip_path)
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/form/div[5]/div/button').click()
    
    driver.implicitly_wait(5)
    #time.sleep(1)
    #for i in range(0,10):
    count = driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/form/div[6]/div/div')
    while True: 
        progress_value = float(count.get_attribute("aria-valuenow"))
        print(progress_value)
        time.sleep(1)
        if progress_value >= 100 :
            print("커스텀 업로드 완료")
            time.sleep(1)
            break
    
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[1]/a/span').click()

    #os.system("pause")

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

def aws_update_sel(driver,revision,aws_link, branch = 'game'):
    if branch == "":
        branch = 'game';

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
    
    driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys('SEL')
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

def aws_update_container(driver,revision, aws_link, branch = 'game', buildType = 'DEV', isDebug = False):
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
    driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/ul/li[4]/a").click()
    driver.implicitly_wait(5)
    time.sleep(0.5)
    #SELECT ALL
    driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div[1]/div/form/div/button[1]").click()

    
    driver.implicitly_wait(5)
    #돋보기
    driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div[1]/div/form/div/div/button').click()
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
    driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[2]/div/div[1]/div/form/div/button[3]').click()
    
    if not isDebug :
        #팝업 내 OK 버튼 클릭
        time.sleep(0.5)
        driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/div/button[1]').click()
        #os.system("pause")


def aws_upload_custom2(driver,revision,zip_path,aws_link, branch = 'game',buildType = 'DEV'):
    '''250204'''
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
    driver.find_element(By.XPATH,"/html/body/div[1]/div[3]/div/div[2]/ul/li[4]/a").click()
    driver.implicitly_wait(5)
    time.sleep(0.5)

    #UPLOAD CUSTOM SERVER
    driver.find_element(By.XPATH,'/html/body/div[1]/div[3]/div/div[2]/div/div/div/div/div[1]/div[2]/button[3]').click()
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
    driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/div[5]/div/button').click()
    
    driver.implicitly_wait(5)
    #time.sleep(1)
    #for i in range(0,10):
    count = driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/div[6]/div/div/div[2]/span')
    while True: 
        progress_value = float(count.get_attribute("aria-valuenow"))
        print(progress_value)
        time.sleep(1)
        if progress_value >= 100 :
            print("커스텀 업로드 완료")
            time.sleep(1)
            break

    #os.system("pause")
    
    # driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/fieldset/div/div/div[2]/div[2]/div/button').click()
    # time.sleep(0.5)
    
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys('CUSTOM')
    # time.sleep(1.5)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li/span').click()
    # time.sleep(0.5)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
    # time.sleep(1.5)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(branch)
    # time.sleep(1.5)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li/span').click()
    # time.sleep(0.5)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
    # time.sleep(1)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[2]/div/input').send_keys(f'{revision}')
    # time.sleep(1)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/div[3]/ul/li/span').click()
    # time.sleep(0.5)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[2]/a[2]').click()
    
    # time.sleep(0.5)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/div/div[1]/div/button').click()
    # time.sleep(0.5)
    # driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[2]/form/fieldset/div/div/div[4]/div/button').click()
    # time.sleep(0.5)
    # driver.find_element(By.XPATH,'/html/body/div[4]/div[1]/div[2]/div/button[1]').click()
    # #os.system("pause")


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
    #aws_update_container(driver= None,revision=213917,aws_link='https://awsdeploy.pbb-qa.pubg.io/environment/sel-game2',branch='game',
    #                     buildType='TEST',isDebug=True)
    #aws_stop()
    #aws_upload_custom2(driver=None,revision="252251",zip_path,aws_link=aws_link,branch='stage_coreloop')
    os.system("pause")
