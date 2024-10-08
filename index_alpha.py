import sys
import os
import shutil
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QProgressDialog, QTimeEdit, QCheckBox, QLabel, QMenuBar, QAction, QDialog)
from PyQt5.QtCore import (Qt, QTime, QTimer, QUrl)
from PyQt5.QtGui import QPixmap, QDesktopServices
import zipfile

class FolderCopyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = 'settings.json'
        self.initUI()
        self.load_settings()

    def initUI(self):
        # Apply the custom stylesheet
        self.setStyleSheet("""
    QWidget {
        background-color: #1a1a1a;
        color: #ffffff;
        border-radius: 10px;
        border: 1px solid #333333;
        font-family: 'Malgun Gothic', sans-serif;
        font-size: 11pt;
        font-weight: bold
    }

    QLineEdit {
        background-color: #333333;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 5px;
        font-family: 'Malgun Gothic', sans-serif;
    }

    QPushButton {
        background-color: #444444;
        border: 1px solid #666666;
        border-radius: 5px;
        padding: 5px;
        font-family: 'Malgun Gothic', sans-serif;
    }

    QPushButton:hover {
        background-color: #555555;
    }

    QPushButton:pressed {
        background-color: #666666;
    }

    QComboBox {
        background-color: #333333;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 5px;
        font-family: 'Malgun Gothic', sans-serif;
    }

    QCheckBox {
        background-color: transparent;
        border: none;
        font-family: 'Malgun Gothic', sans-serif;
    }

    QProgressDialog {
        background-color: #1a1a1a;
        color: #ffffff;
        border-radius: 10px;
        border: 1px solid #333333;
        font-family: 'Malgun Gothic', sans-serif;
    }

    QTimeEdit {
        background-color: #333333;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 5px;
        font-family: 'Malgun Gothic', sans-serif;
    }
""")

        # Create a menu bar
        menu_bar = QMenuBar(self)
        about_menu = menu_bar.addMenu("Menu")
        about_action = QAction("About", self)
        about_action1 = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addActions([about_action])

        layout = QVBoxLayout()
        layout.setMenuBar(menu_bar)
        # The rest of your UI initialization code remains the same
        #layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        h_layout2 = QHBoxLayout()
        h_layout2_1 = QHBoxLayout()
        h_layout3 = QHBoxLayout()
        h_layout4 = QHBoxLayout()

        # First row
        self.input_box1 = QLineEdit(self)
        self.folder_button1 = QPushButton('SET SOURCE', self)
        #self.folder_button1.setFixedWidth(120)
        self.folder_button1.setFixedWidth(186)
        self.folder_button1.clicked.connect(lambda: self.choose_folder(self.input_box1))
        # self.open_folder_button1 = QPushButton('OPEN', self)        
        # self.open_folder_button1.setFixedWidth(60)
        # self.open_folder_button1.clicked.connect(self.open_folder1)
        h_layout1.addWidget(self.input_box1)
        h_layout1.addWidget(self.folder_button1)
        #h_layout1.addWidget(self.open_folder_button1)

        # Second row
        self.input_box2 = QLineEdit(self)
        self.folder_button2 = QPushButton('SET CLIENT DIRECTORY', self)        
        self.folder_button2.setFixedWidth(186)
        self.folder_button2.clicked.connect(lambda: self.choose_folder(self.input_box2))
        h_layout2.addWidget(self.input_box2)
        h_layout2.addWidget(self.folder_button2)

        # Additional second row
        self.input_box2_1 = QLineEdit(self)
        self.folder_button2_1 = QPushButton('SET SERVER DIRECTORY', self)
        self.folder_button2_1.setFixedWidth(186)
        self.folder_button2_1.clicked.connect(lambda: self.choose_folder(self.input_box2_1))
        h_layout2_1.addWidget(self.input_box2_1)
        h_layout2_1.addWidget(self.folder_button2_1)

        # Third row
        self.combo_box = QComboBox(self)
        self.refresh_button = QPushButton('↺', self)
        self.refresh_button.setFixedWidth(35)
        self.refresh_button.clicked.connect(self.refresh_dropdown)
        
        self.combo_box2 = QComboBox(self)
        self.combo_box2.addItems(['Only Client','Only Server','All'])
        self.combo_box2.setFixedWidth(120)
        self.copy_button = QPushButton('COPY', self)
        self.copy_button.clicked.connect(self.execute_copy)
        self.copy_button.setFixedWidth(60)
        # self.copy_button = QPushButton('COPY CLIENT', self)
        # self.copy_button.setFixedWidth(120)
        # self.copy_button.clicked.connect(lambda : self.copy_folder(self.input_box2.text(),self.combo_box.currentText(),'WindowsClient'))
        # self.copy_button1 = QPushButton('COPY SERVER', self)
        # self.copy_button1.setFixedWidth(120)
        # self.copy_button1.clicked.connect(lambda : self.copy_folder(self.input_box2_1.text(),self.combo_box.currentText(),'WindowsServer'))
        # self.copy_button2 = QPushButton('COPY ALL', self)
        # self.copy_button2.setFixedWidth(120)
        # self.copy_button2.clicked.connect(lambda : self.copy_folder(self.input_box2.text(),self.combo_box.currentText(),''))
        h_layout3.addWidget(self.combo_box)
        h_layout3.addWidget(self.refresh_button)
        h_layout3.addWidget(self.combo_box2)
        h_layout3.addWidget(self.copy_button)
        # h_layout3.addWidget(self.copy_button1)
        # h_layout3.addWidget(self.copy_button2)

        # Time settings
        self.time_edit = QTimeEdit(self)
        self.time_edit.setDisplayFormat("HH:mm")
        self.input_box4 = QLineEdit(self)
        # self.combo_box1 = QComboBox(self)
        # self.combo_box1.addItems(['Only Client','Only Server','All'])
        # self.combo_box1.setFixedWidth(120)
        self.checkbox = QCheckBox('RESERVATION', self)
        h_layout4.addWidget(self.time_edit)
        h_layout4.addWidget(self.input_box4)
        #h_layout4.addWidget(self.combo_box1)
        h_layout4.addWidget(self.checkbox)

        # Set the layout
        layout.addLayout(h_layout1)
        layout.addLayout(h_layout2)
        layout.addLayout(h_layout2_1)
        layout.addLayout(h_layout3)
        layout.addLayout(h_layout4)
        self.setLayout(layout)



        self.setWindowTitle('BUILD ttalkkag2')
        self.setGeometry(300, 300, 650, 100)
        self.show()

        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_time)
        self.check_timer.start(1000)



    def choose_folder(self, return_input_box):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_path:
            return_input_box.setText(folder_path)
            #self.refresh_dropdown()

    def choose_folder2(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_path:
            self.input_box2.setText(folder_path)

    def refresh_dropdown(self):
        self.combo_box.clear()
        folder_path = self.input_box1.text()
        filter_texts = self.input_box4.text().split(';') if self.input_box4.text() else []

        if os.path.isdir(folder_path):
            folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
            folders.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)

            for folder in folders:
                if any(filter_text in folder for filter_text in filter_texts):
                    self.combo_box.addItem(folder)

    def copy_folder(self, dest_folder, target_folder, target_name):
        '''
        dest_folder:저장할 위치 'C:/mybuild'\n
        target_folder:저장할 빌드명 'self.combo_box.currentText()'\n
        target_name:저장할 폴더명 'WindowsClient'
        '''
        src_folder = self.input_box1.text()
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

        try:
            dest_path = os.path.join(dest_folder, target_folder, target_name)
            self.progress_dialog = QProgressDialog(f"Copying {target_name} files...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setValue(0)

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
            QMessageBox.information(self, 'Success', 'Folder copied successfully.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to copy folder: {str(e)}')

    def zip_folder(self, dest_folder,target_folder, target_name):
        src_folder = self.input_box1.text()
        #src_folder = 'c:/source'
        client_folder = self.combo_box.currentText()
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
            zip_file = os.path.join(dest_path, f"{target_name}.zip")

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
            QMessageBox.information(self, 'Success', 'Folder zipped successfully.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to zip folder: {str(e)}')

    def open_folder1(self):
        folder_path = self.input_box1.text()
        try:
            os.startfile(folder_path)
        except:
            QMessageBox.critical(self, 'Error', 'Invalid directory.')

    def check_time(self):
        if self.checkbox.isChecked():
            current_time = QTime.currentTime()
            set_time = self.time_edit.time()
            if current_time.hour() == set_time.hour() and current_time.minute() == set_time.minute():
                self.execute_copy(refresh=True)
                self.checkbox.setChecked(False)

    def execute_copy(self, refresh = False):
        reservation_option = self.combo_box2.currentText() #Only Client, Only Server, All
        #QMessageBox.information(self, 'Test', 'Timer executed.')
        #self.zip_folder(self.input_box2_1.text(),self.combo_box.currentText(),'WindowsServer')
        #self.zip_folder('c:/mybuild','tempbuild','WindowsServer')
        if refresh :
            self.refresh_dropdown()
        if reservation_option == "Only Client":
            self.copy_folder(self.input_box2.text(),self.combo_box.currentText(),'WindowsClient')
        elif reservation_option == "Only Server":
            self.copy_folder(self.input_box2_1.text(),self.combo_box.currentText(),'WindowsServer')
        elif reservation_option == "All":
            self.copy_folder(self.input_box2.text(),self.combo_box.currentText(),'')
        #self.copy_folder(self.input_box2.text(),self.combo_box.currentText(),'WindowsClient')
    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as file:
                settings = json.load(file)
                self.input_box1.setText(settings.get('input_box1', ''))
                self.input_box2.setText(settings.get('input_box2', ''))
                self.input_box2_1.setText(settings.get('input_box2_1', ''))
                self.combo_box.addItems(settings.get('combo_box', []))
                self.input_box4.setText(settings.get('input_box4', ''))
                time_value = settings.get('time_edit', '')
            if time_value:
                self.time_edit.setTime(QTime.fromString(time_value, 'HH:mm'))

    def save_settings(self):
        settings = {
            'input_box1': self.input_box1.text(),
            'input_box2': self.input_box2.text(),
            'input_box2_1': self.input_box2_1.text(),
            'combo_box': [self.combo_box.itemText(i) for i in range(self.combo_box.count())],
            'input_box4': self.input_box4.text(),
            'time_edit': self.time_edit.time().toString('HH:mm'),
        }
        with open(self.settings_file, 'w') as file:
            json.dump(settings, file)

    def show_about_dialog(self):
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About")
        about_dialog.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                font-family: 'NanumSquareEB', sans-serif;
                font-size: 12pt;
            }
        """)

        layout = QVBoxLayout()

        version_label = QLabel("Version: v1.0", about_dialog)
        last_update_label = QLabel("Last update date: 2024-08-13", about_dialog)
        created_by_label = QLabel("Created by: mssung@pubg.com", about_dialog)
        first_production_date_label = QLabel("First production date: 2024-07-01", about_dialog)

        #github_label = QLabel("GitHub link:", about_dialog)
        github_icon = QLabel("Issues", about_dialog)
        #pixmap = QPixmap("github_icon.png")  # Replace with the path to your GitHub icon
        #github_icon.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        github_icon.setCursor(Qt.PointingHandCursor)
        github_icon.mousePressEvent = lambda event: QDesktopServices.openUrl(QUrl("https://github.com/SungMinseok/GetBuild/issues"))

        layout.addWidget(version_label)
        layout.addWidget(last_update_label)
        layout.addWidget(created_by_label)
        layout.addWidget(first_production_date_label)

        h_layout = QHBoxLayout()
        #h_layout.addWidget(github_label)
        h_layout.addWidget(github_icon)
        layout.addLayout(h_layout)

        about_dialog.setLayout(layout)
        about_dialog.exec_()

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FolderCopyApp()
    sys.exit(app.exec_())
