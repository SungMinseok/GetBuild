import sys
import os
import shutil
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QProgressDialog)
from PyQt5.QtCore import Qt  # Qt 모듈을 임포트

class FolderCopyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = 'settings.json'
        self.initUI()
        self.load_settings()

    def initUI(self):
        # Create layouts
        layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        h_layout2 = QHBoxLayout()
        h_layout2_1 = QHBoxLayout()
        h_layout3 = QHBoxLayout()

        # Create widgets for the first row
        self.input_box1 = QLineEdit(self)
        self.folder_button1 = QPushButton('Set Source', self)
        self.folder_button1.clicked.connect(lambda: self.choose_folder(self.input_box1))
        self.open_folder_button1 = QPushButton('Open', self)
        self.open_folder_button1.clicked.connect(self.open_folder1)

        # Add widgets to the first row layout
        h_layout1.addWidget(self.input_box1)
        h_layout1.addWidget(self.folder_button1)
        h_layout1.addWidget(self.open_folder_button1)

        # Create widgets for the second row
        self.input_box2 = QLineEdit(self)
        self.folder_button2 = QPushButton('Client Dir', self)
        self.folder_button2.clicked.connect(lambda: self.choose_folder(self.input_box2))

        # Add widgets to the second row layout
        h_layout2.addWidget(self.input_box2)
        h_layout2.addWidget(self.folder_button2)

        # Create widgets for the second row
        self.input_box2_1 = QLineEdit(self)
        self.folder_button2_1 = QPushButton('Server Dir', self)
        self.folder_button2_1.clicked.connect(lambda: self.choose_folder(self.input_box2_1))

        # Add widgets to the second row layout
        h_layout2_1.addWidget(self.input_box2_1)
        h_layout2_1.addWidget(self.folder_button2_1)

        # Create widgets for the third row
        self.combo_box = QComboBox(self)
        self.refresh_button = QPushButton('↺', self)
        self.refresh_button.setMaximumSize(35,500)
        self.refresh_button.clicked.connect(self.refresh_dropdown)
        self.copy_button = QPushButton('Copy Client', self)
        self.copy_button.clicked.connect(lambda : self.copy_folder(self.input_box2.text(),'WindowsClient'))
        self.copy_button1 = QPushButton('Copy Server', self)
        self.copy_button1.clicked.connect(lambda : self.copy_folder(self.input_box2_1.text(),'WindowsServer'))
        self.copy_button2 = QPushButton('Copy Both', self)
        #self.copy_button1.clicked.connect(self.copy_folder)

        # Add widgets to the third row layout
        h_layout3.addWidget(self.combo_box)
        h_layout3.addWidget(self.refresh_button)
        h_layout3.addWidget(self.copy_button)
        h_layout3.addWidget(self.copy_button1)
        h_layout3.addWidget(self.copy_button2)

        # Add row layouts to the main layout
        layout.addLayout(h_layout1)
        layout.addLayout(h_layout2)
        layout.addLayout(h_layout2_1)
        layout.addLayout(h_layout3)

        # Set the main layout
        self.setLayout(layout)

        # Set the window properties
        self.setWindowTitle('Folder Copy App')
        self.setGeometry(300, 300, 650, 100)
        self.show()

    def choose_folder(self, return_input_box):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_path:
            return_input_box.setText(folder_path)
            #self.refresh_dropdown()

    def choose_folder2(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_path:
            self.input_box2.setText(folder_path)

    def refresh_dropdown(self, ):
        self.combo_box.clear()
        folder_path = self.input_box1.text()
        if os.path.isdir(folder_path):
            folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
            folders.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
            self.combo_box.addItems(folders)

    def copy_folder(self, dest_folder, target_name):
        '''
        dest_folder = 'C:/mybuild'
        target_name = 'WindowsClient'
        '''
        src_folder = self.input_box1.text()
        #dest_folder = self.input_box2.text()
        clinet_folder = self.combo_box.currentText()
        folder_to_copy = os.path.join(src_folder, clinet_folder, target_name)

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
            dest_path = os.path.join(dest_folder, clinet_folder, target_name)
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

    def open_folder1(self):
        folder_path = self.input_box1.text()
        if os.path.isdir(folder_path):
            os.startfile(folder_path)
        else:
            QMessageBox.critical(self, 'Error', 'Invalid directory.')

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as file:
                settings = json.load(file)
                self.input_box1.setText(settings.get('input_box1', ''))
                self.input_box2.setText(settings.get('input_box2', ''))
                self.combo_box.addItems(settings.get('combo_box', []))

    def save_settings(self):
        settings = {
            'input_box1': self.input_box1.text(),
            'input_box2': self.input_box2.text(),
            'combo_box': [self.combo_box.itemText(i) for i in range(self.combo_box.count())]
        }
        with open(self.settings_file, 'w') as file:
            json.dump(settings, file)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FolderCopyApp()
    sys.exit(app.exec_())
