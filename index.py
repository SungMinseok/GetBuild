import sys
import os
import shutil
import json
from PyQt5.QtWidgets import (QSizePolicy, QWidgetAction, QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QProgressDialog, QTimeEdit, QCheckBox, QLabel, QMenuBar, QAction, QDialog, QTextEdit)
from PyQt5.QtCore import (Qt, QTime, QTimer, QUrl, QDateTime)
from PyQt5.QtGui import QPixmap, QDesktopServices, QIcon
import zipfile
from tqdm import tqdm
from datetime import datetime, timedelta
from makelog import *
import time
import subprocess
from exporter import export_upload_result

# 리팩토링된 core 모듈 import
from core import ConfigManager, ScheduleManager, BuildOperations
from core.aws_manager import AWSManager


class FolderCopyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = 'settings.json'
        self.config_file = 'config.json'
        
        # 리팩토링된 모듈 초기화
        self.config_mgr = ConfigManager(self.config_file, self.settings_file)
        self.schedule_mgr = ScheduleManager('schedule.json')
        self.build_ops = BuildOperations()
        
        self.initUI()
        self.resize(950, 164)
        self.first_size = self.width(), self.height()
        self.load_settings()
        self.isReserved = False
        self.last_reserved_time = None
        print(self.first_size)

    def initUI(self):
        # Apply the custom stylesheet
        self.setWindowIcon(QIcon('ico.ico'))
        self.load_stylesheet(fr"qss\pbb.qss")

        button_style0 = "QPushButton {background-color: #0D2038; border: 1px solid #2190FF; color: #CFF8FF;} QPushButton:hover {background-color: #19416D;}"

        
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

        funcMenu = menu_bar.addMenu("ETC")
        funcMenuAction0 = QAction("Open config", self)
        funcMenuAction0.triggered.connect(lambda: self.open_file(self.config_file))
        funcMenu.addActions([funcMenuAction0])

        # 메뉴바 우측에 버전 텍스트 표시
        version_label = QLabel(f"Version: {self.read_version_from_file()}", self)
        version_label.setStyleSheet("color: #cccccc; margin-right: 10px; font-weight: bold; font-size: 10pt;")
        menu_bar.setCornerWidget(version_label, Qt.TopRightCorner)


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
        # combo_box_buildname > combo_box_buildname
        self.new_label_3 = QLabel('빌드명(;로 구분)', self)
        self.new_label_3.setFixedWidth(120)
        #self.combo_box_buildname = QLineEdit(self)
        self.combo_box_buildname = QComboBox(self)
        #self.combo_box_buildname.setPlaceholderText('스트링필터')
        self.combo_box_buildname.setFixedWidth(200)
        self.pushbutton_buildname = QPushButton('+', self)
        self.pushbutton_buildname.setFixedWidth(25)
        self.pushbutton_buildname.clicked.connect(lambda: self.show_dropdown_input_dialog(self.combo_box_buildname, '빌드명 추가', 'buildnames'))
        self.pushbutton_buildname_delete = QPushButton('-', self)
        self.pushbutton_buildname_delete.setFixedWidth(25)
        self.pushbutton_buildname_delete.clicked.connect(lambda: self.delete_current_combobox(self.combo_box_buildname, 'buildnames'))
        self.combobox_buildFullName = QComboBox(self)#
        self.combobox_buildFullName.currentTextChanged.connect(self.update_window_title)
        self.open_folder_button3 = QPushButton('📂', self)        
        self.open_folder_button3.setFixedWidth(25)
        self.open_folder_button3.clicked.connect(lambda: self.open_folder(os.path.join(self.input_box2.text(),self.combobox_buildFullName.currentText())))     
        self.capa_button = QPushButton('ℹ️', self)
        self.capa_button.setFixedWidth(25)
        self.capa_button.clicked.connect(self.show_build_time_info)#show_last_modification_time,show_creation_time
        self.refresh_button = QPushButton('🔃', self)
        self.refresh_button.setFixedWidth(25)
        self.refresh_button.clicked.connect(self.refresh_dropdown_revision2)
        
        h_layout3.addWidget(self.new_label_3)
        h_layout3.addWidget(self.combo_box_buildname)
        h_layout3.addWidget(self.pushbutton_buildname)
        h_layout3.addWidget(self.pushbutton_buildname_delete)
        h_layout3.addWidget(self.combobox_buildFullName)
        h_layout3.addWidget(self.open_folder_button3)
        h_layout3.addWidget(self.capa_button)
        h_layout3.addWidget(self.refresh_button)

        
        self.new_label_4 = QLabel('실행 옵션', self)
        self.new_label_4.setFixedWidth(120)
        self.time_edit = QTimeEdit(self)
        self.time_edit.setDisplayFormat("HH:mm")
        self.checkbox_reservation = QCheckBox('예약 실행(주말 제외 해당 시각에 실행)', self)
        self.execute_option = QComboBox(self)
        #self.execute_option.addItems(['클라복사','전체복사','서버복사','서버업로드','서버패치','서버삭제','서버패치(구)','SEL패치(구)','TEST'])
        self.execute_option.addItems(['클라복사','전체복사','서버업로드및패치','서버업로드','서버패치','서버삭제','서버복사','빌드굽기','테스트(로그)','TEST'])
        self.execute_option.setFixedWidth(150)
        self.execute_option.currentTextChanged.connect(lambda: self.handle_combo_change(self.execute_option.currentText()))
        self.add_schedule_button = QPushButton('스케쥴 등록', self)
        self.add_schedule_button.setStyleSheet(button_style0)
        self.add_schedule_button.clicked.connect(self.add_new_schedule)
        self.clear_schedule_button = QPushButton('스케쥴 전체삭제', self)
        self.clear_schedule_button.setStyleSheet("QPushButton {background-color: #8B0000; border: 1px solid #FF0000; color: #FFFFFF;} QPushButton:hover {background-color: #A52A2A;}")
        self.clear_schedule_button.clicked.connect(self.clear_all_schedules)
        self.copy_button = QPushButton('실행', self)
        self.copy_button.setStyleSheet(button_style0)
        self.copy_button.clicked.connect(self.execute_copy)
        #self.copy_button.setFixedWidth(125)
        # self.copy_button = QPushButton('COPY CLIENT', self)
        # self.copy_button.setFixedWidth(120)
        # self.copy_button.clicked.connect(lambda : self.copy_folder(self.input_box2.text(),self.combobox_buildFullName.currentText(),'WindowsClient'))
        # self.copy_button1 = QPushButton('COPY SERVER', self)
        # self.copy_button1.setFixedWidth(120)
        # self.copy_button1.clicked.connect(lambda : self.copy_folder(self.input_box2_1.text(),self.combobox_buildFullName.currentText(),'WindowsServer'))
        # self.copy_button2 = QPushButton('COPY ALL', self)
        # self.copy_button2.setFixedWidth(120)
        # self.copy_button2.clicked.connect(lambda : self.copy_folder(self.input_box2.text(),self.combobox_buildFullName.currentText(),''))
        h_layout3_1.addWidget(self.new_label_4)
        h_layout3_1.addWidget(self.execute_option)
        h_layout3_1.addStretch() 
        h_layout3_1.addWidget(self.add_schedule_button)
        h_layout3_1.addWidget(self.clear_schedule_button)
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
        self.lineedit_awsurl = QLineEdit(self)
        self.lineedit_awsurl.setPlaceholderText('AWS 주소')
        self.new_label_6 = QLabel('Branch', self)
        self.new_label_6.setFixedWidth(120)
        self.lineedit_branch = QLineEdit(self)
        self.lineedit_branch.setPlaceholderText('branch')
        self.lineedit_branch.setFixedWidth(120)
        # self.combo_box1 = QComboBox(self)
        # self.combo_box1.addItems(['Only Client','Only Server','All'])
        # self.combo_box1.setFixedWidth(120)
        aws_container_layout.addWidget(self.new_label_5)
        aws_container_layout.addWidget(self.lineedit_awsurl)
        aws_container_layout.addWidget(self.new_label_6)
        aws_container_layout.addWidget(self.lineedit_branch)

        self.aws_container.setLayout(aws_container_layout)

        # --- 스케줄 표시 영역 추가 ---
        self.schedule_view = QTextEdit(self)
        self.schedule_view.setReadOnly(True)
        #self.schedule_view.setMinimumHeight(100)
        self.refresh_schedule_view()  # 최초 로딩

        

        # Set the layout
        layout.addLayout(h_layout1)
        layout.addLayout(h_layout2)
        layout.addLayout(h_layout2_1)
        layout.addLayout(h_layout3)
        layout.addLayout(h_layout3_1)
        layout.addLayout(h_layout4)
        layout.addWidget(self.detail_container)
        layout.addWidget(self.aws_container)

        layout.addWidget(self.schedule_view)
        #layout.addStretch()
        #layout.addLayout(h_layout5)
        #layout.addStretch()
        self.setLayout(layout)



        #self.setWindowTitle('BUILD ttalkkag2')
        self.setGeometry(300, 300, 650, 100)
        self.show()

        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_time)
        self.check_timer.start(1000)

    def handle_combo_change(self, text):
        self.adjust_detail_conainer()

        if text == '서버삭제' :
            self.detail_container.show()
        elif text == '서버업로드' or text == '서버패치' or text == '서버업로드및패치' : 
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
        
        self.combobox_buildFullName.clear()
        folder_path = self.buildSource_comboBox.currentText()
        filter_texts = self.combo_box_buildname.currentText().split(';') if self.combo_box_buildname.currentText() else []

        if os.path.isdir(folder_path):
            folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
            folders.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)

            for folder in folders:
                if any(filter_text in folder for filter_text in filter_texts):
                    self.combobox_buildFullName.addItem(folder)

    # Function to extract the revision number (integer after '_r')
    def extract_revision_number(self, folder_name):
        """
        folder_name에서 '_r' 뒤에 오는 숫자를 추출하여 반환합니다.
        예: CompileBuild_TEST_game_dev_SEL287878_r334412_MW -> 334412
        """
        return self.build_ops.extract_revision_number(folder_name)
    # def refresh_dropdown_revision(self):        
    #     '''
    #     sort by revision
    #     '''
    #     print(f'refresh_dropdown_revision starttime {datetime.now()}')
        
    #     self.load_stylesheet(fr"qss/red.qss")
    #     time.sleep(1)

    #     self.combobox_buildFullName.clear()
    #     folder_path = self.buildSource_comboBox.currentText()
    #     filter_texts = self.combo_box_buildname.currentText().split(';') if self.combo_box_buildname.currentText() else []

    #     check_file_count = False # 최신순으로 파일 개수 체크 후, 조건을 만족하는 순간 TRUE, 더 이상 체크하지 않음

    #     if os.path.isdir(folder_path):
    #         folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    #         folders.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)

    #         for folder in folders:
    #             if not check_file_count :
    #                 temp_file_count = self.get_file_count(os.path.join(folder_path,folder))
    #                 if temp_file_count < 620:
    #                     print(f'{folder}의 파일 개수 미달로 패스 : {temp_file_count}')
    #                     continue
    #             if len(filter_texts) != 0 :
    #                 if not check_file_count :
    #                     print(f'{folder}의 파일 개수 통과, 더 이상 체크 안함 : {temp_file_count}')
    #                     check_file_count = True
    #                 if any(filter_text in folder for filter_text in filter_texts):
    #                     self.combobox_buildFullName.addItem(folder)
    #             else:
    #                 self.combobox_buildFullName.addItem(folder)


    #     # Get the list of items in the dropdown
    #     items = [self.combobox_buildFullName.itemText(i) for i in range(self.combobox_buildFullName.count())]


    #     # Sort the items based on the extracted revision number in descending order
    #     sorted_items = sorted(items, key=self.extract_revision_number, reverse=True)

    #     # Clear the combo box and repopulate it with the sorted items
    #     self.combobox_buildFullName.clear()
    #     self.combobox_buildFullName.addItems(sorted_items)
    #     self.load_stylesheet(fr"qss\default.qss")
    #     print(f'refresh_dropdown_revision endtime {datetime.now()}')

    def refresh_dropdown_revision2(self):        
        '''
        sort by revision with optimized logic (리팩토링: BuildOperations 사용)
        '''
        print(f'refresh_dropdown_revision starttime {datetime.now()}')
                
        # 최신화 중 팝업 생성
        progress_dialog = QProgressDialog(self)
        progress_dialog.setWindowTitle("최신화 중...")
        progress_dialog.setWindowFlags(progress_dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.show()

        try:
            self.combobox_buildFullName.clear()
            folder_path = self.buildSource_comboBox.currentText()
            filter_texts = self.combo_box_buildname.currentText().split(';') if self.combo_box_buildname.currentText() else []

            if not os.path.isdir(folder_path):
                QMessageBox.critical(self, 'Error', 'Source path is not a valid directory.')
                return

            # BuildOperations 모듈 사용
            builds = self.build_ops.get_latest_builds(folder_path, filter_texts, max_count=50)
            self.combobox_buildFullName.addItems(builds)
            print(f'refresh_dropdown_revision endtime {datetime.now()}')

        finally:
            # 작업 완료 후 팝업 닫기
            progress_dialog.close()

    def copy_folder(self, dest_folder, target_folder, target_name):
        '''
        dest_folder:저장할 위치 'C:/mybuild'\n
        target_folder:저장할 빌드명 'self.combobox_buildFullName.currentText()'\n
        target_name:저장할 폴더명 'WindowsClient'
        '''
        log_execution()
        src_folder = self.buildSource_comboBox.currentText()
        #dest_folder = self.input_box2.text()
        #clinet_folder = self.combobox_buildFullName.currentText()
        folder_to_copy = os.path.join(src_folder, target_folder, target_name)

        # 디버그 로그 추가
        print(f"[copy_folder] src_folder: {src_folder}")
        print(f"[copy_folder] dest_folder: {dest_folder}")
        print(f"[copy_folder] target_folder: {target_folder}")
        print(f"[copy_folder] target_name: {target_name}")
        print(f"[copy_folder] folder_to_copy: {folder_to_copy}")

        if not os.path.isdir(src_folder):
            error_msg = f'Source path is not a valid directory.\n경로: {src_folder}'
            print(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, 'Error', error_msg)
            return
        if not os.path.isdir(dest_folder):
            error_msg = f'Destination path is not a valid directory.\n경로: {dest_folder}'
            print(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, 'Error', error_msg)
            return
        if not os.path.isdir(folder_to_copy):
            error_msg = f'{folder_to_copy} does not exist.'
            print(f"[ERROR] {error_msg}")
            QMessageBox.critical(self, 'Error', error_msg)
            return
        
        main_path = os.path.join(dest_folder, target_folder)
        if not os.path.exists(main_path):
            os.makedirs(main_path)
        self.generate_backend_bat_files(main_path)

        try:
            dest_path = os.path.join(dest_folder, target_folder, target_name)
            self.progress_dialog = QProgressDialog(f"Copying {target_name} files...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)

            #dest_path = os.path.join(self.input_box2.text(), self.combobox_buildFullName.currentText())

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
            #QMessageBox.information(self, 'Success', 'Folder copied successfully.')
            self.show_auto_close_message('Success', 'Folder copied successfully.')
        except Exception as e:
            log_execution()
            #QMessageBox.critical(self, 'Error', f'Failed to copy folder: {str(e)}')
            self.show_auto_close_message('Error', f'Failed to copy folder: {str(e)}')

    def zip_folder(self, dest_folder,target_folder, target_name, update:bool):
        '''
        dest_folder:저장할 위치 'C:/mybuild'\n
        target_folder:저장할 빌드명 'self.combobox_buildFullName.currentText()'\n
        target_name:저장할 폴더명 'WindowsClient'
            self.copy_folder(self.input_box2.text(),self.combobox_buildFullName.currentText(),'WindowsClient')

        update : true, upload + update실행, false upload만 실행
        '''
        #print(revision)
        log_execution()
        src_folder = self.buildSource_comboBox.currentText()
        #src_folder = 'c:/source'
        buildFullName = self.combobox_buildFullName.currentText()
        buildType = self.combobox_buildFullName.currentText().split('_')[1]
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
            aws_url = self.lineedit_awsurl.text()
            branch = self.lineedit_branch.text()
            # 리팩토링: AWSManager 사용
            AWSManager.upload_server_build(
                driver=None,
                revision=revision,
                zip_path=zip_file,
                aws_link=aws_url,
                branch=branch,
                build_type=buildType,
                full_build_name=buildFullName
            )
            # if(update): 
            #     # unused 250728 - 더 이상 사용하지 않음
        except Exception as e:
            #msg = QMessageBox(QMessageBox.Critical, "Error", f"Failed to zip folder: {str(e)}", parent=self)
            #msg.show()

            # 10초 후에 닫히도록 설정
            #QTimer.singleShot(10000, msg.close)
            print(f"Failed to zip folder: {str(e)}")

    def aws_update_directly(self):
        """구버전 AWS 업데이트 (deprecated, 사용하지 않음)"""
        log_execution()
        QMessageBox.warning(self, '경고', '이 기능은 더 이상 사용되지 않습니다. "서버패치"를 사용하세요.')
        # try:
        #     target_folder = self.combobox_buildFullName.currentText()
        #     revision = self.extract_revision_number(target_folder)
        #     aws_url = self.lineedit_awsurl.text()
        #     branch = self.lineedit_branch.text()
        #     # aws.aws_update_sel - deprecated
        # except Exception as e:
        #     QMessageBox.critical(self, 'Error', f'Failed to aws_update_directly: {str(e)}')


    def aws_update_container(self):
        """AWS 컨테이너 패치 (리팩토링: AWSManager 사용)"""
        log_execution()
        
        os.startfile('kill_chrome.bat')
        os.startfile('kill_chromedriver.bat')
        time.sleep(5)
        try:
            target_folder = self.combobox_buildFullName.currentText()
            buildType = self.combobox_buildFullName.currentText().split('_')[1]
            revision = self.extract_revision_number(target_folder)
            aws_url = self.lineedit_awsurl.text()
            branch = self.lineedit_branch.text().strip()
            if not branch:
                branch = self.combo_box_buildname.currentText().strip()

            AWSManager.update_server_container(
                driver=None, 
                revision=revision, 
                aws_link=aws_url, 
                branch=branch, 
                build_type=buildType, 
                is_debug=False, 
                full_build_name=self.combobox_buildFullName.currentText()
            )

        except Exception as e:
            print(f'Failed to aws_update_container: {str(e)}')


    def run_teamcity(self):
        """TeamCity 빌드 실행 (리팩토링: AWSManager 사용)"""
        log_execution()
        
        os.startfile('kill_chrome.bat')
        os.startfile('kill_chromedriver.bat')
        time.sleep(5)

        try:
            branch = self.combo_box_buildname.currentText()
            AWSManager.run_teamcity_build(driver=None, branch=branch)

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to run_teamcity: {str(e)}')

    def open_folder(self, path):
        try:
            os.startfile(path)
        except:
            QMessageBox.critical(self, 'Error', 'Invalid directory.')

    def check_time(self):
        """예약 실행 체크 - 단일 예약(체크박스) + 다중 스케줄(schedule.json) 모두 지원"""
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        # 주말 체크
        if now.weekday() >= 5:  # 5 = 토요일, 6 = 일요일
            return
        
        # 이미 이번 분에 실행했으면 건너뜀 (중복 실행 방지)
        if self.last_reserved_time:
            if now.strftime("%Y-%m-%d %H:%M") == self.last_reserved_time.strftime("%Y-%m-%d %H:%M"):
                return
        
        executed = False
        
        # 1. 기존 단일 예약 체크박스 처리
        if self.checkbox_reservation.isChecked():
            current_time = QTime.currentTime()
            set_time = self.time_edit.time()

            if current_time.hour() == set_time.hour() and current_time.minute() == set_time.minute():
                print(f"[예약실행] 단일 예약 실행: {current_time_str} - {self.execute_option.currentText()}")
                self.checkbox_reservation.setChecked(False)
                self.isReserved = True
                self.execute_copy(refresh=True)
                executed = True
        
        # 2. 다중 스케줄 처리 (schedule.json)
        due_schedules = self.schedule_mgr.get_due_schedules(current_time_str)
        for schedule in due_schedules:
            option = schedule.get('option', '')
            buildname = schedule.get('buildname', '')
            awsurl = schedule.get('awsurl', '')
            branch = schedule.get('branch', '')
            
            print(f"[예약실행] 스케줄 실행: {current_time_str} - {option} | {buildname}")
            
            # 스케줄 정보를 UI에 임시 설정하고 실행
            saved_option = self.execute_option.currentText()
            saved_buildname = self.combo_box_buildname.currentText()
            saved_awsurl = self.lineedit_awsurl.text()
            saved_branch = self.lineedit_branch.text()
            
            try:
                # 스케줄 정보로 UI 업데이트
                if option:
                    idx = self.execute_option.findText(option)
                    if idx >= 0:
                        self.execute_option.setCurrentIndex(idx)
                
                if buildname:
                    idx = self.combo_box_buildname.findText(buildname)
                    if idx >= 0:
                        self.combo_box_buildname.setCurrentIndex(idx)
                    self.refresh_dropdown_revision2()  # 빌드 목록 갱신
                
                if awsurl:
                    self.lineedit_awsurl.setText(awsurl)
                
                if branch:
                    self.lineedit_branch.setText(branch)
                
                # 실행
                self.isReserved = True
                self.execute_copy(refresh=False)  # 이미 refresh 했으므로 False
                executed = True
                
            except Exception as e:
                print(f"[예약실행 오류] {schedule}: {e}")
            
            finally:
                # UI 원복
                idx = self.execute_option.findText(saved_option)
                if idx >= 0:
                    self.execute_option.setCurrentIndex(idx)
                idx = self.combo_box_buildname.findText(saved_buildname)
                if idx >= 0:
                    self.combo_box_buildname.setCurrentIndex(idx)
                self.lineedit_awsurl.setText(saved_awsurl)
                self.lineedit_branch.setText(saved_branch)
        
        # 실행했으면 시간 기록
        if executed:
            self.last_reserved_time = now

    def execute_copy(self, refresh = False):
        log_execution()
        reservation_option = self.execute_option.currentText() #Only Client, Only Server, All
        
        # 디버그 로그 추가
        print(f"[execute_copy] 실행 시작")
        print(f"[execute_copy] reservation_option: '{reservation_option}'")
        print(f"[execute_copy] refresh: {refresh}")
        
        #QMessageBox.information(self, 'Test', 'Timer executed.')
        #self.zip_folder(self.input_box2_1.text(),self.combobox_buildFullName.currentText(),'WindowsServer')
        #self.zip_folder('c:/mybuild','tempbuild','WindowsServer')
        if refresh :
            self.refresh_dropdown_revision2()

        build_fullname = self.combobox_buildFullName.currentText()
        buildType = build_fullname.split('_')[1]
        print(f"[execute_copy] build_fullname: {build_fullname}")
        print(f"[execute_copy] buildType: {buildType}")
        print(f"[execute_copy] dest_folder (input_box2): {self.input_box2.text()}")
        
        #print(f'대상빌드 : {self.input_box2.text()}')
        if reservation_option == "클라복사":
            print(f"[execute_copy] '클라복사' 옵션 선택됨 - copy_folder 호출")
            self.copy_folder(self.input_box2.text(),build_fullname,'WindowsClient')
        elif reservation_option == "서버복사":
            self.copy_folder(self.input_box2.text(),build_fullname,'WindowsServer')
        elif reservation_option == "전체복사":
            self.copy_folder(self.input_box2.text(),build_fullname,'')
        elif reservation_option == "서버패치":
            self.aws_update_container()
        elif reservation_option == "서버업로드":
            self.zip_folder(self.input_box2.text(),build_fullname,'WindowsServer',False)
        elif reservation_option == "서버업로드및패치":
            self.zip_folder(self.input_box2.text(),build_fullname,'WindowsServer',False)
            self.show_wait_popup("서버 패치 전 대기합니다.", 1200)  # 5초 대기
            self.aws_update_container()
        elif reservation_option == "서버패치(구)":
            self.zip_folder(self.input_box2.text(),build_fullname,'WindowsServer',True)
        elif reservation_option == "SEL패치(구)":
            self.aws_update_directly()
        elif reservation_option == "빌드굽기":
            self.run_teamcity()
        elif reservation_option == "테스트(로그)":
            # 테스트용 로그 출력 (실제 작업은 하지 않음)
            test_log = f"""
[테스트 로그 출력]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
실행 옵션: {reservation_option}
빌드명: {self.combo_box_buildname.currentText()}
빌드 전체명: {build_fullname}
빌드 타입: {buildType}
소스 경로: {self.buildSource_comboBox.currentText()}
로컬 경로: {self.input_box2.text()}
AWS URL: {self.lineedit_awsurl.text()}
Branch: {self.lineedit_branch.text()}
예약 실행: {'Yes' if self.isReserved else 'No'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            print(test_log)
            QMessageBox.information(self, '테스트 로그', test_log)
        elif reservation_option == "TEST":
            print('TEST 실행')
            
            #self.generate_backend_bat_files(servers,dest_path)
            #export_upload_result("sel-game4","CompileBuild_DEV_game_SEL274898_r311044","aws_apply","pass")
            #self.show_wait_popup("서버 패치 전 대기합니다.", 1200)  # 5초 대기 
            print('TEST 실행 완료')
            self.execute_test()
            #self.show_build_time_info()
        #self.copy_folder(self.input_box2.text(),self.combobox_buildFullName.currentText(),'WindowsClient')
        if self.isReserved :
            self.isReserved = False
            self.checkbox_reservation.setChecked(True)

    def load_settings(self):
        """설정 로드 (리팩토링: ConfigManager 사용)"""
        # settings.json 로드
        settings = self.config_mgr.load_settings()
        self.input_box2.setText(settings.get('input_box2', ''))
        self.combobox_buildFullName.addItems(settings.get('combobox_buildFullName', []))
        self.lineedit_awsurl.setText(settings.get('lineedit_awsurl', ''))
        time_value = settings.get('time_edit', '')
        if time_value:
            self.time_edit.setTime(QTime.fromString(time_value, 'HH:mm'))

        # config.json에서 빌드명 로드
        try:
            buildnames = self.config_mgr.get_buildnames()
            if buildnames:
                self.combo_box_buildname.addItems(buildnames)
                self.combo_box_buildname.setCurrentIndex(0)
        except Exception as e:
            print(f"Config 로드 오류: {e}")

    def save_settings(self):
        """설정 저장 (리팩토링: ConfigManager 사용)"""
        settings = {
            'input_box1': self.buildSource_comboBox.currentText(),
            'input_box2': self.input_box2.text(),
            'combobox_buildFullName': [self.combobox_buildFullName.itemText(i) for i in range(self.combobox_buildFullName.count())],
            'combo_box_buildname': self.combo_box_buildname.currentText(),
            'lineedit_awsurl': self.lineedit_awsurl.text(),
            'time_edit': self.time_edit.time().toString('HH:mm'),
        }
        self.config_mgr.save_settings(settings)

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
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combobox_buildFullName.currentText())
        
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
        QMessageBox.information(self, 'Folder Capacity', f'Total size of {self.combobox_buildFullName.currentText()} is {total_size_mb:.2f} MB')

    def show_last_modification_time(self):
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combobox_buildFullName.currentText())
        
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
                                f'Last modification time of {self.combobox_buildFullName.currentText()} is {formatted_time}\n'
                                f'Time passed since last modification: {time_passed_str}')

    def show_creation_time(self):
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combobox_buildFullName.currentText())
        
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
                                f'Creation time of {self.combobox_buildFullName.currentText()} is {formatted_time}\n'
                                f'Time passed since creation: {time_passed_str}')
        
    def show_build_time_info(self):
        print(f'show_build_time_info starttime {datetime.now()}')
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combobox_buildFullName.currentText())
        
        if not self.combobox_buildFullName.currentText() or not os.path.isdir(folder_path):
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
                                f'{self.combobox_buildFullName.currentText()}\n'
                               # f'생성시간: {creation_formatted_time}\n'
                                f'업로드 시각: {version_mod_formatted_time} ({hours}시간 {minutes}분 전)\n'
                               # f'소요시간: {last_mod_datetime-creation_datetime}\n'
                               # f'총 파일개수: {file_count}\n'
                               f'* 위는 빌드 생성 시작 시각이 아닙니다.'
        )
            
    def show_file_count(self):
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combobox_buildFullName.currentText())
        
        if not os.path.isdir(folder_path):
            QMessageBox.critical(self, 'Error', 'Selected path is not a valid directory.')
            return

        # Count all files in the folder
        #file_count = sum([len(files) for _, _, files in os.walk(folder_path)])
        file_count = self.get_file_count(folder_path)

        # Show the file count in a pop-up
        QMessageBox.information(self, 'File Count', 
                                f'Total number of files in {self.combobox_buildFullName.currentText()} is {file_count}')
    
    def get_file_count(self, folder_path):
        """파일 개수 조회 (리팩토링: BuildOperations 사용)"""
        return self.build_ops.get_file_count(folder_path)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F12:
            self.debug_function()  # Call the function to execute on F12 press

    def debug_function(self):
        #self.show_file_count()
        # Replace this with whatever you want to happen when F12 is pressed
        #QMessageBox.information(self, 'Debugging', 'F12 pressed: Debugging function executed.')

        #self.zip_folder(self.input_box2.text(),self.combobox_buildFullName.currentText(),'WindowsServer')
        
        # target_folder = self.combobox_buildFullName.currentText()
        # revision = self.extract_revision_number(target_folder)
        # aws_url = self.lineedit_awsurl.text()
        # aws.aws_upload_custom(None,revision,zip_file,aws_link=aws_url)
        # aws.aws_update_custom(None,revision,aws_url)
        #self.set_loading_state(True)
        print(self.get_most_recent_file())
        pass


    def closeEvent(self, event):
        #self.save_settings()
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
            target_folder = self.combobox_buildFullName.currentText()
            buildType = self.combobox_buildFullName.currentText().split('_')[1]
            revision = self.extract_revision_number(target_folder)
            aws_url = self.lineedit_awsurl.text()
            branch = self.combo_box_buildname.currentText()
            self.setWindowTitle(f'{branch}-{buildType}_{revision}')
        except:
            pass

    def toggle_layouts(self, target):
        if target.isVisible():
            target.hide()
        else:
            target.show()

            

    def generate_backend_bat_files(self, output_dir="."):
        """백엔드 BAT 파일 생성 (리팩토링: BuildOperations 사용)"""
        server_list = self.config_mgr.get_awsurls()
        self.build_ops.generate_backend_bat_files(output_dir, server_list)

    def show_last_file_info(self):
        print(f'show_last_file_info starttime {datetime.now()}')
        folder_path = os.path.join(self.buildSource_comboBox.currentText(), self.combobox_buildFullName.currentText())
        
        if not self.combobox_buildFullName.currentText() or not os.path.isdir(folder_path):
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
        dest_path = os.path.join(self.input_box2.text(), self.combobox_buildFullName.currentText())
        self.generate_backend_bat_files(dest_path)
        #self.show_last_file_info()
        # Show the QMessageBox
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Success")
        message_box.setText("Folder copied successfully.")
        message_box.setStandardButtons(QMessageBox.Close)  # 닫기 버튼 유지
        message_box.show()

        # Set a QTimer to close the QMessageBox after 1 minute
        QTimer.singleShot(1000, lambda: message_box.done(QMessageBox.Close))

    def show_auto_close_message(self, title, message, timeout=60000):
        """
        Show a QMessageBox with a close button that automatically closes after a timeout.

        :param title: Title of the message box
        :param message: Message to display
        :param timeout: Time in milliseconds before the message box closes automatically (default: 60000ms)
        """
        message_box = QMessageBox(self)
        message_box.setWindowTitle(title)
        message_box.setText(message)
        message_box.setStandardButtons(QMessageBox.Close)  # 닫기 버튼 유지
        message_box.show()

        # Set a QTimer to close the QMessageBox after the specified timeout
        QTimer.singleShot(timeout, lambda: message_box.done(QMessageBox.Close))

    def show_dropdown_input_dialog(self, dropdown, title, key):
        """빌드명 추가 다이얼로그 (리팩토링: ConfigManager 사용)"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        input_box = QLineEdit(dialog)
        layout.addWidget(input_box)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        layout.addWidget(buttons)

        def on_accept():
            name = input_box.text().strip()
            if name:
                try:
                    if key == 'buildnames':
                        names = self.config_mgr.add_buildname(name)
                        dropdown.clear()
                        dropdown.addItems(names)
                        dropdown.setCurrentText(name)
                except Exception as e:
                    QMessageBox.critical(self, "오류", f"설정 저장 실패: {e}")
            dialog.accept()

        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(dialog.reject)
        dialog.exec_()

    def delete_current_combobox(self, dropdown, key):
        """빌드명 삭제 (리팩토링: ConfigManager 사용)"""
        name = dropdown.currentText().strip()
        if not name:
            QMessageBox.warning(self, "알림", "삭제할 빌드명이 선택되어 있지 않습니다.")
            return

        try:
            if key == 'buildnames':
                names = self.config_mgr.remove_buildname(name)
                dropdown.clear()
                dropdown.addItems(names)
                if names:
                    dropdown.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 실패: {e}")

    def show_wait_popup(self, message, seconds):
        """
        지정한 초(seconds) 동안 팝업을 띄우고, 남은 시간과 프로그레스바를 표시합니다.
        """
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
        dialog = QDialog(self)
        dialog.setWindowTitle("잠시 대기")
        layout = QVBoxLayout(dialog)

        label = QLabel(f"{message}", dialog)
        layout.addWidget(label)

        time_label = QLabel(f"남은 시간: {seconds}초", dialog)
        layout.addWidget(time_label)

        progress_bar = QProgressBar(dialog)
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(seconds)
        progress_bar.setValue(seconds)
        layout.addWidget(progress_bar)

        dialog.setModal(True)

        # 내부 상태
        self._wait_seconds_left = seconds

        def update_progress():
            self._wait_seconds_left -= 1
            progress_bar.setValue(self._wait_seconds_left)
            time_label.setText(f"남은 시간: {self._wait_seconds_left}초")
            if self._wait_seconds_left <= 0:
                timer.stop()
                dialog.accept()

        timer = QTimer(dialog)
        timer.timeout.connect(update_progress)
        timer.start(1000)

        dialog.exec_()
        timer.stop()

    def open_file(self, file_path):
        """
        파일을 열기 위한 메소드
        :param file_path: 열고자 하는 파일의 경로
        """
        try:
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                QMessageBox.critical(self, 'Error', 'File does not exist.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open file: {str(e)}')

    def get_values_from_json(self, file_path, key):
        """
        JSON 파일에서 지정한 하나의 키에 해당하는 모든 값들을 리스트로 반환

        Parameters:
            file_path (str): JSON 파일 경로
            key (str): 추출할 단일 키

        Returns:
            list: 해당 키의 모든 값 리스트
        """
        values = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def extract(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k == key:
                            # 값이 리스트면 extend, 아니면 append
                            if isinstance(v, list):
                                values.extend(v)
                            else:
                                values.append(v)
                        extract(v)
                elif isinstance(obj, list):
                    for item in obj:
                        extract(item)

            extract(data)
            return values

        except Exception as e:
            print(f"Error: {e}")
            return []
        
    def refresh_schedule_view(self):
        """스케줄 뷰 갱신 (리팩토링: ScheduleManager 사용)"""
        text = self.schedule_mgr.get_formatted_schedules()
        self.schedule_view.setPlainText(text)



    def add_new_schedule(self):
        """스케줄 추가 (리팩토링: ScheduleManager 사용)"""
        time_str = self.time_edit.time().toString('HH:mm')
        option = self.execute_option.currentText()
        buildname = self.combo_box_buildname.currentText()
        awsurl = self.lineedit_awsurl.text().strip()
        branch = self.lineedit_branch.text().strip()

        self.schedule_mgr.add_schedule(time_str, option, buildname, awsurl, branch)
        QMessageBox.information(self, "스케줄 등록", f"{time_str} 예약이 등록되었습니다.")
        self.refresh_schedule_view()
    
    def clear_all_schedules(self):
        """모든 스케줄 삭제"""
        schedules = self.schedule_mgr.load_schedules()
        if not schedules:
            QMessageBox.information(self, "스케줄 삭제", "삭제할 스케줄이 없습니다.")
            return
        
        # 확인 다이얼로그
        reply = QMessageBox.question(
            self, 
            "스케줄 전체 삭제", 
            f"총 {len(schedules)}개의 스케줄을 모두 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.schedule_mgr.save_schedules([])  # 빈 리스트로 저장
            QMessageBox.information(self, "스케줄 삭제", "모든 스케줄이 삭제되었습니다.")
            self.refresh_schedule_view()

if __name__ == '__main__':
    if os.path.exists("QuickBuild_updater.exe"):
        subprocess.call(["QuickBuild_updater.exe", "--silent"])
    else:
        subprocess.call([sys.executable, "updater.py", "--silent"])

    app = QApplication(sys.argv)
    ex = FolderCopyApp()
    sys.exit(app.exec_())