import sys
import os
import shutil
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QProgressDialog, QTimeEdit, QCheckBox, QLabel, QMenuBar, QAction, QDialog, QTextEdit)
from PyQt5.QtCore import (Qt, QTime, QTimer, QUrl, QDateTime)
from PyQt5.QtGui import QPixmap, QDesktopServices, QIcon
import zipfile
from tqdm import tqdm
from datetime import datetime, timedelta
import aws
from makelog import *
import time
import subprocess


servers = [
    "sel-game-unrealclientproxy.pbb-qa.pubg.io:443",
    "sel-game2-unrealclientproxy.pbb-qa.pubg.io:443",
    "sel-game3-unrealclientproxy.pbb-qa.pubg.io:443",
    "sel-game4-unrealclientproxy.pbb-qa.pubg.io:443",
    "sel-game5-unrealclientproxy.pbb-qa.pubg.io:443",
    "sel-game6-unrealclientproxy.pbb-qa.pubg.io:443",
    "sel-progression-unrealclientproxy.pbb-qa.pubg.io:443",
    "10.160.2.239:5259"
]


class FolderCopyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = 'settings.json'
        self.initUI()
        self.resize(850, self.height())
        self.first_size = self.width(), self.height()
        self.load_settings()
        self.isReserved = False
        self.last_reserved_time = None

    def initUI(self):
        # Apply the custom stylesheet
        self.setWindowIcon(QIcon('ico.ico'))
        self.load_stylesheet(fr"qss\default.qss")
        #self.load_stylesheet(fr"qss/red.qss")
#         self.setStyleSheet("""
#     QWidget {
#         background-color: #1a1a1a;
#         color: #ffffff;
#         border-radius: 10px;
#         border: 1px solid #333333;
#         font-family: 'Malgun Gothic', sans-serif;
#         font-size: 11pt;
#         font-weight: bold
#     }

#     QLineEdit {
#         background-color: #333333;
#         border: 1px solid #555555;
#         padding: 5px;
#         border-radius: 5px;
#         font-family: 'Malgun Gothic', sans-serif;
#     }

#     QPushButton {
#         background-color: #444444;
#         border: 1px solid #666666;
#         border-radius: 5px;
#         padding: 5px;
#         font-family: 'Malgun Gothic', sans-serif;
#     }

#     QPushButton:hover {
#         background-color: #555555;
#     }

#     QPushButton:pressed {
#         background-color: #666666;
#     }

#     QComboBox {
#         background-color: #333333;
#         border: 1px solid #555555;
#         padding: 5px;
#         border-radius: 5px;
#         font-family: 'Malgun Gothic', sans-serif;
#     }

#     QCheckBox {
#         background-color: transparent;
#         border: none;
#         font-family: 'Malgun Gothic', sans-serif;
#     }

#     QProgressDialog {
#         background-color: #1a1a1a;
#         color: #ffffff;
#         border-radius: 10px;
#         border: 1px solid #333333;
#         font-family: 'Malgun Gothic', sans-serif;
#     }

#     QTimeEdit {
#         background-color: #333333;
#         border: 1px solid #555555;
#         padding: 5px;
#         border-radius: 5px;
#         font-family: 'Malgun Gothic', sans-serif;
#     }
# """)
        # Create a menu bar //lambda event: QDesktopServices.openUrl(QUrl("https://github.com/SungMinseok/GetBuild/issues"))
        menu_bar = QMenuBar(self)
        about_menu = menu_bar.addMenu("메뉴")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_action1 = QAction("Report Bugs", self)
        about_action1.triggered.connect(lambda event: QDesktopServices.openUrl(QUrl("https://github.com/SungMinseok/GetBuild/issues")))
        about_action2 = QAction("Guide", self)
        about_action2.triggered.connect(lambda event: QDesktopServices.openUrl(QUrl("https://wiki.krafton.com/pages/viewpage.action?pageId=4926105897")))
        about_action3 = QAction("Check Update", self)
        about_action3.triggered.connect(self.run_quickbuild_updater)
        about_menu.addActions([about_action,about_action1,about_action2,about_action3])

        layout = QVBoxLayout()
        layout.setMenuBar(menu_bar)
        # The rest of your UI initialization code remains the same
        #layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        h_layout2 = QHBoxLayout()
        h_layout2_1 = QHBoxLayout()
        h_layout3 = QHBoxLayout()
        h_layout3_1 = QHBoxLayout()
        h_layout4 = QHBoxLayout()
        h_layout5 = QVBoxLayout()

        # First row
        self.new_label_1 = QLabel('빌드 소스 경로', self)
        self.new_label_1.setFixedWidth(120)
        #print(self.new_label_1.width())

        
        self.buildSource_comboBox = QComboBox(self)
        self.buildSource_comboBox.addItems([fr'\\pubg-pds\PBB\Builds',fr'\\pbb-ams-dev\p\builds'])
        #self.buildSource_comboBox.setFixedWidth(120)
        #self.input_box1 = QLineEdit(self)
        #self.input_box1.setText(fr'\\pubg-pds\PBB\Builds')
        self.open_folder_button1 = QPushButton('📂', self)        
        self.open_folder_button1.setFixedWidth(25)
        self.open_folder_button1.clicked.connect(lambda: self.open_folder(self.buildSource_comboBox.currentText()))       
        self.folder_button1 = QPushButton('...', self)
        #self.folder_button1.setFixedWidth(120)
        self.folder_button1.setFixedWidth(25)
        self.folder_button1.clicked.connect(lambda: self.choose_folder(self.buildSource_comboBox))
        # self.open_folder_button1 = QPushButton('OPEN', self)        
        # self.open_folder_button1.setFixedWidth(60)
        # self.open_folder_button1.clicked.connect(self.open_folder1)
        h_layout1.addWidget(self.new_label_1)
        h_layout1.addWidget(self.buildSource_comboBox)
        h_layout1.addWidget(self.folder_button1)
        h_layout1.addWidget(self.open_folder_button1)
        #h_layout1.addWidget(self.open_folder_button1)

        # Second row
        self.new_label_2 = QLabel('로컬 저장 경로', self)
        self.new_label_2.setFixedWidth(120)
        self.input_box2 = QLineEdit(self)
        self.open_folder_button2 = QPushButton('📂', self)        
        self.open_folder_button2.setFixedWidth(25)
        self.open_folder_button2.clicked.connect(lambda: self.open_folder(self.input_box2.text()))      
        self.folder_button2 = QPushButton('...', self)        
        self.folder_button2.setFixedWidth(25)
        self.folder_button2.clicked.connect(lambda: self.choose_folder(self.input_box2))
        h_layout2.addWidget(self.new_label_2)
        h_layout2.addWidget(self.input_box2)
        h_layout2.addWidget(self.folder_button2)
        h_layout2.addWidget(self.open_folder_button2)

        # Additional second row
        # self.input_box2_1 = QLineEdit(self)
        # self.folder_button2_1 = QPushButton('SET SERVER DIRECTORY', self)
        # self.folder_button2_1.setFixedWidth(186)
        # self.folder_button2_1.clicked.connect(lambda: self.choose_folder(self.input_box2_1))
        # h_layout2_1.addWidget(self.input_box2_1)
        # h_layout2_1.addWidget(self.folder_button2_1)

        # Third row
        self.new_label_3 = QLabel('빌드명', self)
        self.new_label_3.setFixedWidth(120)
        self.input_box4 = QLineEdit(self)
        self.input_box4.setPlaceholderText('스트링필터(;로 구분)')
        self.input_box4.setFixedWidth(200)
        self.combo_box = QComboBox(self)#
        self.combo_box.currentTextChanged.connect(self.update_window_title)
        self.open_folder_button3 = QPushButton('📂', self)        
        self.open_folder_button3.setFixedWidth(25)
        self.open_folder_button3.clicked.connect(lambda: self.open_folder(os.path.join(self.input_box2.text(),self.combo_box.currentText())))     
        self.capa_button = QPushButton('ℹ️', self)
        self.capa_button.setFixedWidth(25)
        self.capa_button.clicked.connect(self.show_build_time_info)#show_last_modification_time,show_creation_time
        self.refresh_button = QPushButton('🔍', self)
        self.refresh_button.setFixedWidth(25)
        self.refresh_button.clicked.connect(self.refresh_dropdown_revision2)
        
        h_layout3.addWidget(self.new_label_3)
        h_layout3.addWidget(self.input_box4)
        h_layout3.addWidget(self.combo_box)
        h_layout3.addWidget(self.open_folder_button3)
        h_layout3.addWidget(self.capa_button)
        h_layout3.addWidget(self.refresh_button)

        
        self.new_label_4 = QLabel('실행 옵션', self)
        self.new_label_4.setFixedWidth(120)
        self.time_edit = QTimeEdit(self)
        self.time_edit.setDisplayFormat("HH:mm")
        self.checkbox_reservation = QCheckBox('예약 실행', self)
        self.combo_box2 = QComboBox(self)
        #self.combo_box2.addItems(['클라복사','전체복사','서버복사','서버업로드','서버패치','서버삭제','서버패치(구)','SEL패치(구)','TEST'])
        self.combo_box2.addItems(['클라복사','전체복사','서버업로드','서버패치','서버삭제','서버복사','빌드굽기','TEST'])
        self.combo_box2.setFixedWidth(120)
        self.combo_box2.currentTextChanged.connect(lambda: self.handle_combo_change(self.combo_box2.currentText()))
        self.copy_button = QPushButton('지금 실행', self)
        self.copy_button.clicked.connect(self.execute_copy)
        self.copy_button.setFixedWidth(125)
        # self.copy_button = QPushButton('COPY CLIENT', self)
        # self.copy_button.setFixedWidth(120)
        # self.copy_button.clicked.connect(lambda : self.copy_folder(self.input_box2.text(),self.combo_box.currentText(),'WindowsClient'))
        # self.copy_button1 = QPushButton('COPY SERVER', self)
        # self.copy_button1.setFixedWidth(120)
        # self.copy_button1.clicked.connect(lambda : self.copy_folder(self.input_box2_1.text(),self.combo_box.currentText(),'WindowsServer'))
        # self.copy_button2 = QPushButton('COPY ALL', self)
        # self.copy_button2.setFixedWidth(120)
        # self.copy_button2.clicked.connect(lambda : self.copy_folder(self.input_box2.text(),self.combo_box.currentText(),''))
        h_layout3_1.addWidget(self.new_label_4)
        h_layout3_1.addWidget(self.combo_box2)
        h_layout3_1.addStretch() 
        h_layout3_1.addWidget(self.copy_button)
        h_layout3_1.addWidget(self.time_edit)
        h_layout3_1.addWidget(self.checkbox_reservation)
        # h_layout3.addWidget(self.copy_button1)
        # h_layout3.addWidget(self.copy_button2)

        # Time settings
        #h_layout4.addWidget(self.combo_box1)

        # 서버삭제 리스트 위젯젯
        self.detail_container = QWidget()
        self.detail_container.hide()
        detail_container_layout = QVBoxLayout()
        
        self.new_label_7 = QLabel('AWS URL LIST', self)
        self.new_label_7.setFixedWidth(120)
        self.textarea0 = QTextEdit(self)#서버삭제 url list
        detail_container_layout.addWidget(self.new_label_7)
        detail_container_layout.addWidget(self.textarea0)
        self.detail_container.setLayout(detail_container_layout)

        #AWS 위젯젯
        self.aws_container = QWidget()
        self.aws_container.hide()
        aws_container_layout = QHBoxLayout()

        self.new_label_5 = QLabel('AWS URL', self)
        self.new_label_5.setFixedWidth(120)
        self.input_box5 = QLineEdit(self)
        self.input_box5.setPlaceholderText('AWS 주소')
        self.new_label_6 = QLabel('Branch', self)
        self.new_label_6.setFixedWidth(120)
        self.input_box6 = QLineEdit(self)
        self.input_box6.setPlaceholderText('branch')
        self.input_box6.setFixedWidth(120)
        # self.combo_box1 = QComboBox(self)
        # self.combo_box1.addItems(['Only Client','Only Server','All'])
        # self.combo_box1.setFixedWidth(120)
        aws_container_layout.addWidget(self.new_label_5)
        aws_container_layout.addWidget(self.input_box5)
        aws_container_layout.addWidget(self.new_label_6)
        aws_container_layout.addWidget(self.input_box6)

        self.aws_container.setLayout(aws_container_layout)
        #self.detail_container.addWidget(self.textarea0)
       # h_layout5 = QHBoxLayout(self.detail_container)
        #detail_container_layout.addWidget(self.textarea0)
        

        

        # Set the layout
        layout.addLayout(h_layout1)
        layout.addLayout(h_layout2)
        layout.addLayout(h_layout2_1)
        layout.addLayout(h_layout3)
        layout.addLayout(h_layout3_1)
        layout.addLayout(h_layout4)
        layout.addWidget(self.detail_container)
        layout.addWidget(self.aws_container)
        #layout.addLayout(h_layout5)
        #layout.addStretch()
        self.setLayout(layout)



        self.setWindowTitle('BUILD ttalkkag2')
        self.setGeometry(300, 300, 650, 100)
        self.show()

        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_time)
        self.check_timer.start(1000)

    def handle_combo_change(self, text):
        self.adjust_detail_conainer()

        if text == '서버삭제' :
            self.detail_container.show()
        elif text == '서버업로드' or text == '서버패치' : 
            self.aws_container.show()

    def adjust_detail_conainer(self):
        self.detail_container.hide()
        self.aws_container.hide()
        self.adjustSize()
        self.resize(self.first_size[0], self.first_size[1])

    def choose_folder(self, return_input_box):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_path:
            try:
                return_input_box.setText(folder_path)
            except:
                return_input_box.setCurrentText(folder_path)
            #self.refresh_dropdown()

    def choose_folder2(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_path:
            self.input_box2.setText(folder_path)

    def refresh_dropdown(self):
        '''
        sort by last modified time
        '''
        
        self.combo_box.clear()
        folder_path = self.buildSource_comboBox.currentText()
        filter_texts = self.input_box4.text().split(';') if self.input_box4.text() else []

        if os.path.isdir(folder_path):
            folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
            folders.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)

            for folder in folders:
                if any(filter_text in folder for filter_text in filter_texts):
                    self.combo_box.addItem(folder)

    # Function to extract the revision number (integer after '_r')
    def extract_revision_number(self,folder_name):
        # Split the folder name by '_r' and take the last part
        try:
            return int(folder_name.split('_r')[-1])
        except ValueError:
            return 0  # In case of an invalid format, return 0 as the default
    def refresh_dropdown_revision(self):        
        '''
        sort by revision
        '''
        print(f'refresh_dropdown_revision starttime {datetime.now()}')
        
        self.load_stylesheet(fr"qss/red.qss")
        time.sleep(1)

        self.combo_box.clear()
        folder_path = self.buildSource_comboBox.currentText()
        filter_texts = self.input_box4.text().split(';') if self.input_box4.text() else []

        check_file_count = False # 최신순으로 파일 개수 체크 후, 조건을 만족하는 순간 TRUE, 더 이상 체크하지 않음

        if os.path.isdir(folder_path):
            folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
            folders.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)

            for folder in folders:
                if not check_file_count :
                    temp_file_count = self.get_file_count(os.path.join(folder_path,folder))
                    if temp_file_count < 620:
                        print(f'{folder}의 파일 개수 미달로 패스 : {temp_file_count}')
                        continue
                if len(filter_texts) != 0 :
                    if not check_file_count :
                        print(f'{folder}의 파일 개수 통과, 더 이상 체크 안함 : {temp_file_count}')
                        check_file_count = True
                    if any(filter_text in folder for filter_text in filter_texts):
                        self.combo_box.addItem(folder)
                else:
                    self.combo_box.addItem(folder)


        # Get the list of items in the dropdown
        items = [self.combo_box.itemText(i) for i in range(self.combo_box.count())]


        # Sort the items based on the extracted revision number in descending order
        sorted_items = sorted(items, key=self.extract_revision_number, reverse=True)

        # Clear the combo box and repopulate it with the sorted items
        self.combo_box.clear()
        self.combo_box.addItems(sorted_items)
        self.load_stylesheet(fr"qss\default.qss")
        print(f'refresh_dropdown_revision endtime {datetime.now()}')

    def refresh_dropdown_revision2(self):        
        '''
        sort by revision with optimized logic
        '''
        print(f'refresh_dropdown_revision starttime {datetime.now()}')
                
        # 최신화 중 메시지 박스 생성
        # progress_message = QMessageBox(self)
        # progress_message.setWindowTitle("진행 중")
        # progress_message.setText("최신화 중입니다. 잠시만 기다려주세요...")
        # progress_message.setStandardButtons(QMessageBox.NoButton)  # 버튼 제거
        # progress_message.setWindowModality(Qt.ApplicationModal)
        # progress_message.show()
        # 최신화 중 팝업 생성
        progress_dialog = QProgressDialog(self)
        progress_dialog.setWindowTitle("최신화 중...")
        progress_dialog.setWindowFlags(progress_dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.show()

        try:
            self.load_stylesheet(fr"qss/red.qss")
            self.combo_box.clear()
            folder_path = self.buildSource_comboBox.currentText()
            filter_texts = self.input_box4.text().split(';') if self.input_box4.text() else []

            if not os.path.isdir(folder_path):
                QMessageBox.critical(self, 'Error', 'Source path is not a valid directory.')
                return

            folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
            print(f'폴더 개수 : {len(folders)}')
            #folders.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
                
            # 리비전 숫자를 기준으로 내림차순 정렬
            folders.sort(key=lambda x: self.extract_revision_number(x), reverse=True)

            added_count = 0  # 추가된 폴더 개수 추적

            for folder in folders:
                if added_count >= 50:  # 최대 5개까지만 추가
                    break

                folder_full_path = os.path.join(folder_path, folder)
                version_file_path = os.path.join(folder_full_path, "version.txt")

                # 메인 폴더에 version.txt가 있는 경우만 추가
                if added_count >= 1 or os.path.isfile(version_file_path):
                    if len(filter_texts) == 0 or any(filter_text in folder for filter_text in filter_texts):
                        self.combo_box.addItem(folder)
                        added_count += 1

            # Get the list of items in the dropdown
            items = [self.combo_box.itemText(i) for i in range(self.combo_box.count())]

            # Sort the items based on the extracted revision number in descending order
            #sorted_items = sorted(items, key=self.extract_revision_number, reverse=True)

            # Clear the combo box and repopulate it with the sorted items
            self.combo_box.clear()
            self.combo_box.addItems(items)
            self.load_stylesheet(fr"qss\default.qss")
            print(f'refresh_dropdown_revision endtime {datetime.now()}')

        finally:
            # 작업 완료 후 팝업 닫기
            progress_dialog.close()

    def copy_folder(self, dest_folder, target_folder, target_name):
        '''
        dest_folder:저장할 위치 'C:/mybuild'\n
        target_folder:저장할 빌드명 'self.combo_box.currentText()'\n
        target_name:저장할 폴더명 'WindowsClient'
        '''
        log_execution()
        src_folder = self.buildSource_comboBox.currentText()
        #dest_folder = self.input_box2.text()
        #clinet_folder = self.combo_box.currentText()
        folder_to_copy = os.path.join(src_folder, target_folder, target_name)

        if not os.path.isdir(src_folder):
            QMessageBox.critical(self, 'Error', 'Source path is not a valid directory.')
            return
        if not os.path.isdir(dest_folder):
            QMessageBox.critical(self, 'Error', 'Destination path is not a valid directory.')
            return
        if not os.path.isdir(folder_to_copy):
            QMessageBox.critical(self, 'Error', f'{folder_to_copy} does not exist.')
            return
        
        main_path = os.path.join(dest_folder, target_folder)
        if not os.path.exists(main_path):
            os.makedirs(main_path)
        self.generate_backend_bat_files(servers,main_path)

        try:
            dest_path = os.path.join(dest_folder, target_folder, target_name)
            self.progress_dialog = QProgressDialog(f"Copying {target_name} files...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)

            #dest_path = os.path.join(self.input_box2.text(), self.combo_box.currentText())

            for root, dirs, files in os.walk(folder_to_copy):
                for file in files:
                    if self.progress_dialog.wasCanceled():
                        QMessageBox.information(self, 'Cancelled', 'Copying cancelled.')
                        return

                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(root, folder_to_copy)
                    dest_dir = os.path.join(dest_path, rel_path)
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    shutil.copy(src_file, dest_dir)
                                
                    # Update progress
                    progress = (files.index(file) + 1) / len(files) * 100
                    self.progress_dialog.setValue(int(progress))

            self.progress_dialog.setValue(100)
            log_execution()
            QMessageBox.information(self, 'Success', 'Folder copied successfully.')
        except Exception as e:
            log_execution()
            QMessageBox.critical(self, 'Error', f'Failed to copy folder: {str(e)}')

    def zip_folder(self, dest_folder,target_folder, target_name, update:bool):
        '''
        dest_folder:저장할 위치 'C:/mybuild'\n
        target_folder:저장할 빌드명 'self.combo_box.currentText()'\n
        target_name:저장할 폴더명 'WindowsClient'
            self.copy_folder(self.input_box2.text(),self.combo_box.currentText(),'WindowsClient')

        update : true, upload + update실행, false upload만 실행
        '''
        #print(revision)
        log_execution()
        src_folder = self.buildSource_comboBox.currentText()
        #src_folder = 'c:/source'
        client_folder = self.combo_box.currentText()
        buildType = self.combo_box.currentText().split('_')[1]
        folder_to_zip = os.path.join(src_folder, target_folder, target_name)

        if not os.path.isdir(src_folder):
            QMessageBox.critical(self, 'Error', 'Source path is not a valid directory.')
            return
        if not os.path.isdir(dest_folder):
            QMessageBox.critical(self, 'Error', 'Destination path is not a valid directory.')
            return
        if not os.path.isdir(folder_to_zip):
            QMessageBox.critical(self, 'Error', f'{folder_to_zip} does not exist.')
            return

        try:
            
            dest_path = os.path.join(dest_folder, target_folder)
    
            if not os.path.exists(dest_path):
                os.makedirs(dest_path)
            zip_file = os.path.join(dest_path, f"{target_name}.zip")
            if not os.path.isfile(zip_file):

                self.progress_dialog = QProgressDialog(f"Zipping {target_name} files...", "Cancel", 0, 100, self)
                self.progress_dialog.setWindowModality(Qt.WindowModal)
                self.progress_dialog.setValue(0)

                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(folder_to_zip):
                        for file in files:
                            if self.progress_dialog.wasCanceled():
                                QMessageBox.information(self, 'Cancelled', 'Zipping cancelled.')
                                return

                            src_file = os.path.join(root, file)
                            rel_path = os.path.relpath(root, folder_to_zip)
                            zipf.write(src_file, os.path.join(rel_path, file))

                            # Update progress
                            progress = (files.index(file) + 1) / len(files) * 100
                            self.progress_dialog.setValue(int(progress))

                self.progress_dialog.setValue(100)
                log_execution()
                #QMessageBox.information(self, 'Success', 'Folder zipped successfully.')
                print('Folder zipped successfully.')

            else:
                log_execution()
                print('zip is already created.')
                pass
            
            revision = self.extract_revision_number(target_folder)
            aws_url = self.input_box5.text()
            branch = self.input_box6.text()
            aws.aws_upload_custom2(None,revision,zip_file,aws_link=aws_url,branch=branch,buildType=buildType)
            if(update):
                aws.aws_update_custom(None,revision,aws_url,branch=branch)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to zip folder: {str(e)}')

    def aws_update_directly(self):
        log_execution()
        try:
            target_folder = self.combo_box.currentText()
            
            revision = self.extract_revision_number(target_folder)
            aws_url = self.input_box5.text()
            branch = self.input_box6.text()
            aws.aws_update_sel(None,revision,aws_link=aws_url,branch=branch)


        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to aws_update_directly: {str(e)}')


    def aws_update_container(self):
        log_execution()
        try:
            target_folder = self.combo_box.currentText()
            buildType = self.combo_box.currentText().split('_')[1]
            revision = self.extract_revision_number(target_folder)
            aws_url = self.input_box5.text()
            branch = self.input_box4.text()
            aws.aws_update_container(driver= None,revision=revision,aws_link=aws_url,branch=branch,buildType=buildType,isDebug=False)


        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to aws_update_container: {str(e)}')


    def run_teamcity(self):
        log_execution()
        try:
            #target_folder = self.combo_box.currentText()
            # buildType = self.combo_box.currentText().split('_')[1]
            # revision = self.extract_revision_number(target_folder)
            # aws_url = self.input_box5.text()
            branch = self.input_box4.text()
            aws.run_teamcity(driver=None,branch=branch)


        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to aws_update_container: {str(e)}')

    def open_folder(self, path):
        try:
            os.startfile(path)
        except:
            QMessageBox.critical(self, 'Error', 'Invalid directory.')

    def check_time(self):
        if self.checkbox_reservation.isChecked():
            current_time = QTime.currentTime()
            set_time = self.time_edit.time()

            if current_time.hour() == set_time.hour() and current_time.minute() == set_time.minute():
                now = datetime.now()

                # ✅ 주말이면 실행 안 함
                if now.weekday() >= 5:  # 5 = 토요일, 6 = 일요일
                    print("주말에는 예약 실행을 건너뜁니다.")
                    return

                # ✅ 이전에 실행한 적 있으면 건너뜀
                if self.last_reserved_time:
                    if now.strftime("%Y-%m-%d %H:%M") == self.last_reserved_time.strftime("%Y-%m-%d %H:%M"):
                        print(f"예약 시간 {self.last_reserved_time.strftime('%Y-%m-%d %H:%M')}에 이미 실행됨")
                        return

                self.last_reserved_time = now
                self.checkbox_reservation.setChecked(False)
                self.isReserved = True
                self.execute_copy(refresh=True)

    def execute_copy(self, refresh = False):
        log_execution()
        reservation_option = self.combo_box2.currentText() #Only Client, Only Server, All
        #QMessageBox.information(self, 'Test', 'Timer executed.')
        #self.zip_folder(self.input_box2_1.text(),self.combo_box.currentText(),'WindowsServer')
        #self.zip_folder('c:/mybuild','tempbuild','WindowsServer')
        if refresh :
            self.refresh_dropdown_revision()

        build_fullname = self.combo_box.currentText()
        buildType = build_fullname.split('_')[1]
        #print(f'대상빌드 : {self.input_box2.text()}')
        if reservation_option == "클라복사":
            self.copy_folder(self.input_box2.text(),build_fullname,'WindowsClient')
        elif reservation_option == "서버복사":
            self.copy_folder(self.input_box2.text(),build_fullname,'WindowsServer')
        elif reservation_option == "전체복사":
            self.copy_folder(self.input_box2.text(),build_fullname,'')
        elif reservation_option == "서버패치":
            self.aws_update_container()
        elif reservation_option == "서버업로드":
            self.zip_folder(self.input_box2.text(),build_fullname,'WindowsServer',False)
        elif reservation_option == "서버패치(구)":
            self.zip_folder(self.input_box2.text(),build_fullname,'WindowsServer',True)
        elif reservation_option == "SEL패치(구)":
            self.aws_update_directly()
        elif reservation_option == "빌드굽기":
            self.run_teamcity()
        elif reservation_option == "TEST":
            self.execute_test()
            #self.show_build_time_info()
        #self.copy_folder(self.input_box2.text(),self.combo_box.currentText(),'WindowsClient')
        if self.isReserved :
            self.isReserved = False
            self.checkbox_reservation.setChecked(True)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as file:
                settings = json.load(file)
                #self.input_box1.setText(settings.get('input_box1', ''))
                self.input_box2.setText(settings.get('input_box2', ''))
                #self.input_box2_1.setText(settings.get('input_box2_1', ''))
                self.combo_box.addItems(settings.get('combo_box', []))
                self.input_box4.setText(settings.get('input_box4', ''))
                self.input_box5.setText(settings.get('input_box5', ''))
                time_value = settings.get('time_edit', '')
            if time_value:
                self.time_edit.setTime(QTime.fromString(time_value, 'HH:mm'))

    def save_settings(self):
        settings = {
            'input_box1': self.buildSource_comboBox.currentText(),
            'input_box2': self.input_box2.text(),
#            'input_box2_1': self.input_box2_1.text(),
            'combo_box': [self.combo_box.itemText(i) for i in range(self.combo_box.count())],
            'input_box4': self.input_box4.text(),
            'input_box5': self.input_box5.text(),
            'time_edit': self.time_edit.time().toString('HH:mm'),
        }
        with open(self.settings_file, 'w') as file:
            json.dump(settings, file)

    def read_version_from_file(self):
        with open("version.txt", "r", encoding="utf-8") as f:
            version = f.read().strip()
            return  version
        # version.txt에서 버전 읽기
    # def read_version_from_file(self):
    #     try:
    #         with open("version.txt", "r", encoding="utf-8") as f:
    #             return f.read().strip()
    #     except FileNotFoundError:
    #         return "Unknown"

        
        
    def show_about_dialog(self):
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About")
        # about_dialog.setStyleSheet("""
        #     QWidget {
        #         background-color: #fafafa;
        #         color: #000000;
        #         font-family: 'NanumSquareEB', sans-serif;
        #         font-size: 12pt;
        #     }
        # """)

        layout = QVBoxLayout()
        recent_file_name, recent_moditime = self.get_most_recent_file()

        version_label = QLabel(f"Version : {self.read_version_from_file()}", about_dialog)
        #last_update_label = QLabel(f"Last update date: {recent_moditime}", about_dialog)
        #last_update_label = QLabel(f"Last update date: 2024-12-23", about_dialog)
        created_by_label = QLabel("Ask : mssung@pubg.com", about_dialog)
        first_production_date_label = QLabel("From : 2024-07-01", about_dialog)
        # giturl_label = QLabel(about_dialog)
        # giturl_label.setTextFormat(Qt.RichText)
        # giturl_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        # giturl_label.setOpenExternalLinks(True)
        # giturl_label.setText('''
        #     <a href="https://github.com/SungMinseok/GetBuild" style="color: #4fc3f7; text-decoration: none;">
        #         <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="16" height="16" style="vertical-align: middle; margin-right: 4px;">
        #         GitHub
        #     </a>
        # ''')
        report_label = QLabel(about_dialog)
        report_label.setTextFormat(Qt.RichText)
        report_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        report_label.setOpenExternalLinks(True)
        report_label.setText('''
            <a href="https://github.com/SungMinseok/GetBuild/issues" style="color: #4fc3f7; text-decoration: none;">
                🐞 Bugs
            </a>
        ''')#⚒️
        
        guide_label = QLabel(about_dialog)
        guide_label.setTextFormat(Qt.RichText)
        guide_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        guide_label.setOpenExternalLinks(True)
        guide_label.setText('''
            <a href="https://krafton.atlassian.net/wiki/spaces/P2/pages/124523484/mssung+PBB+Build+Auto" style="color: #4fc3f7; text-decoration: none;">
                📖 Guide
            </a>
        ''')
        #github_label = QLabel("GitHub link:", about_dialog)
        # github_icon = QLabel("Issues", about_dialog)
        # pixmap = QPixmap("github_icon.png")  # Replace with the path to your GitHub icon
        # github_icon.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # github_icon.setCursor(Qt.PointingHandCursor)
        # github_icon.mousePressEvent = lambda event: QDesktopServices.openUrl(QUrl("https://github.com/SungMinseok/GetBuild/issues"))

        layout.addWidget(version_label)
        #layout.addWidget(last_update_label)
        layout.addWidget(created_by_label)
        layout.addWidget(first_production_date_label)
        #layout.addWidget(giturl_label)
        layout.addWidget(report_label)
        layout.addWidget(guide_label)

        h_layout = QHBoxLayout()
        #h_layout.addWidget(github_label)
        #h_layout.addWidget(github_icon)
        layout.addLayout(h_layout)

        about_dialog.setLayout(layout)
        about_dialog.exec_()

    def check_capacity(self):
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combo_box.currentText())
        
        if not os.path.isdir(folder_path):
            QMessageBox.critical(self, 'Error', 'Selected path is not a valid directory.')
            return

        total_size = 0
        for dirpath, dirnames, filenames in tqdm(os.walk(folder_path)):
            for file in filenames:
                fp = os.path.join(dirpath, file)
                total_size += os.path.getsize(fp)
            print(total_size)

        total_size_mb = total_size / (1024 * 1024)  # Convert to MB
        QMessageBox.information(self, 'Folder Capacity', f'Total size of {self.combo_box.currentText()} is {total_size_mb:.2f} MB')

    def show_last_modification_time(self):
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combo_box.currentText())
        
        if not os.path.isdir(folder_path):
            QMessageBox.critical(self, 'Error', 'Selected path is not a valid directory.')
            return

        # Get the last modification time of the folder
        last_mod_time = os.path.getmtime(folder_path)
        last_mod_datetime = datetime.fromtimestamp(last_mod_time)
        formatted_time = last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate the time passed since the last modification
        current_time = datetime.now()
        time_passed = current_time - last_mod_datetime
        
        # Format the time passed as days, hours, minutes, and seconds
        days, seconds = time_passed.days, time_passed.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        time_passed_str = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        
        QMessageBox.information(self, 'Last Modification Time', 
                                f'Last modification time of {self.combo_box.currentText()} is {formatted_time}\n'
                                f'Time passed since last modification: {time_passed_str}')

    def show_creation_time(self):
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combo_box.currentText())
        
        if not os.path.isdir(folder_path):
            QMessageBox.critical(self, 'Error', 'Selected path is not a valid directory.')
            return

        # Get the creation time of the folder
        try:
            creation_time = os.path.getctime(folder_path)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Unable to retrieve creation time: {str(e)}')
            return

        creation_datetime = datetime.fromtimestamp(creation_time)
        formatted_time = creation_datetime.strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate the time passed since the creation
        current_time = datetime.now()
        time_passed = current_time - creation_datetime
        
        # Format the time passed as days, hours, minutes, and seconds
        days, seconds = time_passed.days, time_passed.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        time_passed_str = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        
        QMessageBox.information(self, 'Folder Creation Time', 
                                f'Creation time of {self.combo_box.currentText()} is {formatted_time}\n'
                                f'Time passed since creation: {time_passed_str}')
        
    def show_build_time_info(self):
        print(f'show_build_time_info starttime {datetime.now()}')
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combo_box.currentText())
        
        if not self.combo_box.currentText() or not os.path.isdir(folder_path):
            QMessageBox.critical(self, 'Error', 'Selected path is not a valid directory.')
            return

        # Get the last modification time of the folder
        last_mod_time = os.path.getmtime(folder_path)
        last_mod_datetime = datetime.fromtimestamp(last_mod_time)
        last_mod_formatted_time = last_mod_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
        # Get the modification time of version.txt
        version_file_path = os.path.join(folder_path, "version.txt")
        if os.path.isfile(version_file_path):
            version_mod_time = os.path.getmtime(version_file_path)
            version_mod_datetime = datetime.fromtimestamp(version_mod_time)
            version_mod_formatted_time = version_mod_datetime.strftime("%Y-%m-%d %H:%M:%S")
        else:
            version_mod_formatted_time = "version.txt not found"

        # Calculate the time passed since the version.txt modification
        current_time = datetime.now()
        time_passed = current_time - version_mod_datetime

        # Format the time passed as hours and minutes
        hours = time_passed.seconds // 3600
        minutes = (time_passed.seconds % 3600) // 60

        # Get the creation time of the folder
        # try:
        #     creation_time = os.path.getctime(folder_path)
        # except Exception as e:
        #     QMessageBox.critical(self, 'Error', f'Unable to retrieve creation time: {str(e)}')
        #     return

        #creation_datetime = datetime.fromtimestamp(creation_time)
        #creation_formatted_time = creation_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Format the time passed as days, hours, minutes, and seconds
        #days, seconds = time_passed.days, time_passed.seconds
        # hours = seconds // 3600
        # minutes = (seconds % 3600) // 60
        # seconds = seconds % 60
        
        #time_passed_str = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        #file_count = sum([len(files) for _, _, files in os.walk(folder_path)])
        print(f'show_build_time_info endtime {datetime.now()}')
        
        QMessageBox.information(self, 'Folder Creation Time', 
                                f'{self.combo_box.currentText()}\n'
                               # f'생성시간: {creation_formatted_time}\n'
                                f'업로드 시각: {version_mod_formatted_time} ({hours}시간 {minutes}분 전)\n'
                               # f'소요시간: {last_mod_datetime-creation_datetime}\n'
                               # f'총 파일개수: {file_count}\n'
                               f'* 위는 빌드 생성 시작 시각이 아닙니다.'
        )
            
    def show_file_count(self):
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combo_box.currentText())
        
        if not os.path.isdir(folder_path):
            QMessageBox.critical(self, 'Error', 'Selected path is not a valid directory.')
            return

        # Count all files in the folder
        #file_count = sum([len(files) for _, _, files in os.walk(folder_path)])
        file_count = self.get_file_count(folder_path)

        # Show the file count in a pop-up
        QMessageBox.information(self, 'File Count', 
                                f'Total number of files in {self.combo_box.currentText()} is {file_count}')
    
    def get_file_count(self, folder_path):
        return sum([len(files) for _, _, files in os.walk(folder_path)])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F12:
            self.debug_function()  # Call the function to execute on F12 press

    def debug_function(self):
        #self.show_file_count()
        # Replace this with whatever you want to happen when F12 is pressed
        #QMessageBox.information(self, 'Debugging', 'F12 pressed: Debugging function executed.')

        #self.zip_folder(self.input_box2.text(),self.combo_box.currentText(),'WindowsServer')
        
        # target_folder = self.combo_box.currentText()
        # revision = self.extract_revision_number(target_folder)
        # aws_url = self.input_box5.text()
        # aws.aws_upload_custom(None,revision,zip_file,aws_link=aws_url)
        # aws.aws_update_custom(None,revision,aws_url)
        #self.set_loading_state(True)
        print(self.get_most_recent_file())
        pass


    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def set_loading_state(self, is_loading):
        if is_loading:
            self.setStyleSheet("background-color: darkblue;")
            self.setDisabled(True)
        else:
            self.setStyleSheet("")
            self.setDisabled(False)

    def load_stylesheet(self, filepath):
        with open(filepath, "r") as file:
            self.setStyleSheet(file.read())

    def get_most_recent_file(self):
        # Get a list of all files in the current directory
        #files = [f for f in os.listdir('.') if os.path.isfile(f)]
        files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.exe')]
        #files = [f for f in os.listdir('.') if os.path.isfile(f) and not f.endswith('.json')]
        # Initialize variables to track the most recent file and its modification time
        most_recent_file = None
        most_recent_time = 0
        
        for file in files:
            # Get the last modification time
            mod_time = os.path.getmtime(file)
            
            # Check if this file is the most recent one we've encountered
            if mod_time > most_recent_time:
                most_recent_time = mod_time
                most_recent_file = file
        
        if most_recent_file:
            # Convert the most recent time to a readable format
            most_recent_time_readable = datetime.fromtimestamp(most_recent_time).strftime('%Y-%m-%d %H:%M:%S')
            return most_recent_file, most_recent_time_readable
        else:
            return None, None
        
    def update_window_title(self):
        try:
            target_folder = self.combo_box.currentText()
            buildType = self.combo_box.currentText().split('_')[1]
            revision = self.extract_revision_number(target_folder)
            aws_url = self.input_box5.text()
            branch = self.input_box4.text()
            self.setWindowTitle(f'{branch}-{buildType}_{revision}')
        except:
            pass

    def toggle_layouts(self, target):
        if target.isVisible():
            target.hide()
        else:
            target.show()

            

    def generate_backend_bat_files(self,server_list, output_dir="."):
        """
        주어진 서버 주소 리스트를 기반으로 .bat 파일을 생성합니다.

        :param server_list: 백엔드 서버 주소 리스트 (예: ['10.160.2.239:5259', 'sel-game-unrealclientproxy.pbb-qa.pubg.io:443'])
        :param output_dir: bat 파일이 저장될 디렉토리 (기본: 현재 디렉토리)
        :param client_path: 실행할 클라이언트 경로 (기본: WindowsClient\Client.exe)
        """
        base_command = f'start WindowsClient\Client.exe -HardwareBenchmark -gpucrashdebugging -aftermathall -norenderdoc -nosteam'

        for server in server_list:
            sanitized_name = server.replace(":", "_").replace(".", "_")
            bat_filename = f"{sanitized_name}.bat"
            full_path = os.path.join(output_dir, bat_filename)

            with open(full_path, "w", encoding="utf-8") as f:
                command = f'{base_command} -Backend="{server}" -Backend_ssl=yes -Backend_root_cert=""'
                f.write(command)
            #print(f"BAT 파일 생성됨: {full_path}")

    def show_last_file_info(self):
        print(f'show_last_file_info starttime {datetime.now()}')
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combo_box.currentText())
        
        if not self.combo_box.currentText() or not os.path.isdir(folder_path):
            QMessageBox.critical(self, 'Error', 'Selected path is not a valid directory.')
            return

        # Get the most recently modified file in the folder
        most_recent_file = None
        most_recent_time = 0

        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                mod_time = os.path.getmtime(file_path)
                if mod_time > most_recent_time:
                    most_recent_time = mod_time
                    most_recent_file = file_path

        if most_recent_file:
            most_recent_datetime = datetime.fromtimestamp(most_recent_time)
            formatted_time = most_recent_datetime.strftime("%Y-%m-%d %H:%M:%S")
            QMessageBox.information(self, 'Last Modified File Info', 
                                    f'가장 최근 수정된 파일: {os.path.basename(most_recent_file)}\n'
                                    f'파일 경로: {most_recent_file}\n'
                                    f'수정 시간: {formatted_time}')
        else:
            QMessageBox.information(self, 'Last Modified File Info', '폴더에 파일이 없습니다.')

        print(f'show_last_file_info endtime {datetime.now()}')

    def run_quickbuild_updater(self):

        if os.path.exists("QuickBuild_updater.exe"):
            proc = subprocess.call(["QuickBuild_updater.exe"])
        else:
            proc = subprocess.call([sys.executable, "updater.py"])

        # try:
        #     #proc = subprocess.Popen([sys.executable, "updater.py"])
        #     time.sleep(1)
        #     if proc.poll() is not None:
        #         QMessageBox.critical(self, "테스트 실패", "notepad.exe가 즉시 종료되었습니다.")
        #     else:
        #         QMessageBox.information(self, "테스트 성공", "notepad.exe가 정상 실행되었습니다.")
        # except Exception as e:
        #     QMessageBox.critical(self, "실행 오류", f"오류:\n{e}")

    def execute_test(self):
        dest_path = os.path.join(self.input_box2.text(), self.combo_box.currentText())
        #self.generate_backend_bat_files(servers,dest_path)
        self.show_last_file_info()

    

if __name__ == '__main__':
    if os.path.exists("QuickBuild_updater.exe"):
        subprocess.call(["QuickBuild_updater.exe", "--silent"])
    else:
        subprocess.call([sys.executable, "updater.py", "--silent"])

    app = QApplication(sys.argv)
    ex = FolderCopyApp()
    sys.exit(app.exec_())