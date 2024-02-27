# -*- coding: utf-8 -*-
'''
# Created on Jan-02-20 09:41 
# tab_upgrade.py
# @author: 
'''

import sys, os, time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QFileDialog

sys.path.append(os.getcwd())
from lib.uploader import uploader_main

steup = '''
    Pull log use U disk
        1. push the "To USB store" buttom
        2. restart copter and connect the usb line
        3. wait a minute
    Push Friware
        1. load Frimware
        2. push 'Flash Firmware' button
        3. restart the copter and connect the usb line

    Note: when the begin, we shouldn't connect the usb line
    '''

# @msgs: send upgrade msg to copter
# @function: upgrade the copter's firmware
class tabUpgrade(QtWidgets.QTabBar):
    def __init__(self, *agrs, **kwargs):
        super(tabUpgrade, self).__init__(*agrs, **kwargs)
        self.tabNameStr = 'Upgrade'
        self.layout = QtWidgets.QVBoxLayout(self)
        self.icon = 'resource/icon_upgrade_64.svg'

        self.layout.setContentsMargins(20,20,10,0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        group = QtWidgets.QGroupBox()
        group.setObjectName('blackWgt_1pxBorder')
        group.setFixedHeight(250)
        groupLayout = QtWidgets.QVBoxLayout(group)
        groupLayout.setContentsMargins(0,0,0,0)
        groupLayout.setAlignment(QtCore.Qt.AlignTop)
        headerLabel = QtWidgets.QLabel()
        headerLabel.setFixedHeight(25)
        headerLabel.setText('Firmware Steup')
        headerLabel.setStyleSheet("QLabel { background:#2d3037;color:#c5cee1;}")
        headerLabel.setAlignment(QtCore.Qt.AlignCenter)

        steupLabel = QtWidgets.QLabel()
        steupLabel.setObjectName('nameLabel')
        steupLabel.setText(steup)
        groupLayout.addWidget(headerLabel)
        groupLayout.addWidget(steupLabel)
        self.layout.addWidget(group)

        self.msgWgt = QtWidgets.QTextEdit()
        self.msgWgt.setReadOnly(True)
        self.msgWgt.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.msgWgt.setObjectName('ConsoleWgt')
        self.msgWgt.append('Please load firmware...')
        self.layout.addWidget(self.msgWgt)

        frame = QtWidgets.QFrame()
        frameLayout = QtWidgets.QHBoxLayout(frame)
        self.loadFirmwareBtn = QtWidgets.QPushButton()
        self.loadFirmwareBtn.setObjectName('blackPushButton')
        self.loadFirmwareBtn.setText('Load Firmware [Local]')
        self.loadFirmwareBtn.setFixedSize(200, 25)
        self.loadFirmwareBtn.clicked.connect(self.loadBtnClicked)
        self.flashFirmwareBtn = QtWidgets.QPushButton()
        self.flashFirmwareBtn.setObjectName('blackPushButton')
        self.flashFirmwareBtn.setText('Flash Firmware')
        self.flashFirmwareBtn.setFixedSize(200, 25)
        self.flashFirmwareBtn.setCheckable(True)
        self.flashFirmwareBtn.clicked.connect(self.flashBtnClicked)
        self.flashFirmwareBtn.setDisabled(True)
        self.usbstore = QtWidgets.QPushButton()
        self.usbstore.setObjectName('blackPushButton')
        self.usbstore.setText('To USB store')
        self.usbstore.setFixedSize(200, 25)
        self.usbstore.setCheckable(True)
        self.usbstore.clicked.connect(self.usbBtnClicked)
        # self.usbstore.setDisabled(True)
        # self.serialclear = QtWidgets.QPushButton()
        # self.serialclear.setObjectName('blackPushButton')
        # self.serialclear.setText('Serial Clear')
        # self.serialclear.setFixedSize(200, 25)
        # self.serialclear.setCheckable(True)
        # self.serialclear.clicked.connect(self.serialclearClicked)
        # self.serialclear.setDisabled(True)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        frameLayout.addItem(spacerItem)
        frameLayout.addWidget(self.usbstore)
        frameLayout.addWidget(self.flashFirmwareBtn)
        frameLayout.addWidget(self.loadFirmwareBtn)
        # frameLayout.addWidget(self.serialclear)
        self.layout.addWidget(frame)

        self.filePath = ''
        self.upgrade_thread = upgrade_thread()
        self.upgrade_thread.uploader._msg_signal.connect(self.updateUploaderMsg)

    def loadBtnClicked(self):
        filePath = QFileDialog.getOpenFileName(self,'Select the log file..','')[0]
        if filePath == '':
            return
        self.filePath = filePath
        self.flashFirmwareBtn.setDisabled(False)
        # self.loadFile()
        self.flashFirmwareBtn.setChecked(True)
        self.flashBtnClicked()

    def flashBtnClicked(self):
        if self.flashFirmwareBtn.isChecked():
            self.loadFile()
            self.upgrade_thread.filePath = self.filePath
            self.upgrade_thread.flashflg = True
            self.upgrade_thread.start()
        else:
            self.upgrade_thread.flashflg = False
    def usbBtnClicked(self):
        print("click ok")
        if self.usbstore.isChecked():
            self.upgrade_thread.tousbflg = True
            self.upgrade_thread.start()
        else:
            self.upgrade_thread.clear_serial = True
    # def serialclearClicked(self):
    #     print("refush serial port")
    #     self.upgrade_thread.clear_serial = True

    def loadFile(self):
        """
        load a new frimware file
        """
        fileSize = round(os.path.getsize(self.filePath)/1024)
        fileTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(os.path.getctime(self.filePath)))
        self.msgWgt.setText('')
        self.msgWgt.append('\n-----------Load Firmware-----------')
        self.msgWgt.append(f'File  Path : {self.filePath}')
        self.msgWgt.append(f'Creat Time : {fileTime}')
        self.msgWgt.append(f'File  Size : {fileSize} KB')
        self.msgWgt.append('-----------------------------------\n')

    def updateUploaderMsg(self, msg):
        """
        update uploader msg in UI
        """
        if 'Erase' in msg or 'Program' in msg or 'Verify' in msg:
            cursor = self.msgWgt.textCursor()
            cursor.select(QtGui.QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
        self.msgWgt.append(msg)
        if 'Uploader Success' in msg:
            self.flashFirmwareBtn.setChecked(False)
            self.flashBtnClicked()
        if "send u_dri command" in msg:
            self.usbstore.setChecked(False)

class upgrade_thread(QThread):
    def __init__(self):
        super(upgrade_thread, self).__init__()
        self.flashflg = False
        self.uploader = uploader_main()
        self.filePath = ''
        self.tousbflg = False
        self.clear_serial = False

    def run(self):
        while(True):
            time.sleep(0.05)
            if self.clear_serial:
                self.clear_serial = False
                self.tousbflg = False
                self.tousbflg = False
                self.uploader.load_flg =False
                self.uploader.flg = True
                self.uploader.port_list.clear()
                self.uploader.port_find_list.clear()
                self.uploader.putload_port =''
            if self.flashflg or self.tousbflg:
                self.uploader.find_serial()
            if self.tousbflg and self.uploader.load_flg:
                self.uploader.to_usb()
                return
            if self.flashflg and self.uploader.load_flg:
                self.uploader.update(self.filePath)
                self.flashflg = self.uploader.load_flg = False
                self.uploader.flg = True
                self.uploader.port_find_list = []
                self.putload_port = ''



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabUpgrade()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    sys.exit(app.exec_())

