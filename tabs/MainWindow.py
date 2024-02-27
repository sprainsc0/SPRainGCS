# -*- coding: utf-8 -*-
'''
# Created on Dec-31-19 19:25 
# MainWindow.py
# @author: 
'''

import sys
from PyQt5 import QtCore, QtGui, QtWidgets

buadRateList = [
    '57600',
    '115200',
]

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        """
        Frame of GUI
        =========================
        |____________header___________|
        |                             |
        -------------------------------
        |tablist|                     |
        |tablist|                     |
        |tablist|    tab              |
        |tablist|                     |
        |tablist|                     |
        =========================
        """

        super().__init__()
        self.setObjectName("MainWindow")

        # self.setWindowTitle('xGroundStation')
        self.setWindowTitle(' ')

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        self.sensorWgt = {
            'gyro' : {
                'iconOn': 'resource/sensor_gyro_on.png',
                'iconOff': 'resource/sensor_gyro_off.png',
                'name': 'GYRO',
            },
            'accel' : {
                'iconOn': 'resource/sensor_acc_on.png',
                'iconOff': 'resource/sensor_acc_off.png',
                'name': 'ACCEL',
            },
            'mag' : {
                'iconOn': 'resource/sensor_mag_on.png',
                'iconOff': 'resource/sensor_mag_off.png',
                'name': 'MAG',
            },
            'baro' : {
                'iconOn': 'resource/sensor_baro_on.png',
                'iconOff': 'resource/sensor_baro_off.png',
                'name': 'BARO',
            },
            'vision' : {
                'iconOn': 'resource/sensor_gyro_on.png',
                'iconOff': 'resource/sensor_gyro_off.png',
                'name': 'VISION',
            },
            'lidar' : {
                'iconOn': 'resource/sensor_gyro_on.png',
                'iconOff': 'resource/sensor_gyro_off.png',
                'name': 'LIDAR',
            },
        }

        # add header
        self.addHeader()

        self.addNavigationWgt()

        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setFixedHeight(22)
        self.statusbar.setContentsMargins(0,0,0,0)
        self.statusbar.setObjectName('statusbar')
        self.statusbar.setSizeGripEnabled(False)
        # self.setStatusBar(self.statusbar)
        self.layout.addWidget(self.statusbar)

    def addNavigationWgt(self):
        frameTab = QtWidgets.QFrame()
        horizontalLayout = QtWidgets.QHBoxLayout(frameTab)
        horizontalLayout.setContentsMargins(0, 0, 0, 0)
        horizontalLayout.setSpacing(0)

        scrollArea = QtWidgets.QScrollArea(frameTab)
        scrollArea.setFixedWidth(180)
        scrollArea.setWidgetResizable(True)
        scrollArea.setObjectName('Navigation')
        scrollAreaWidgetContents = QtWidgets.QWidget()
        scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 194, 522))
        scrollLayout = QtWidgets.QVBoxLayout(scrollAreaWidgetContents)
        scrollLayout.setContentsMargins(0, 0, 0, 0)
        scrollLayout.setSpacing(0)

        scrollFrame = QtWidgets.QFrame(scrollAreaWidgetContents)
        scrollFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        scrollFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        frameLayout = QtWidgets.QVBoxLayout(scrollFrame)
        frameLayout.setContentsMargins(0, 0, 0, 0)
        frameLayout.setSpacing(0)

        self.navigationList = QtWidgets.QListWidget()
        self.navigationList.setObjectName('navigationList')
        self.navigationList.setIconSize(QtCore.QSize(20, 20))

        frameLayout.addWidget(self.navigationList)
        scrollLayout.addWidget(scrollFrame)
        scrollArea.setWidget(scrollAreaWidgetContents)

        horizontalLayout.addWidget(scrollArea)

        self.mainTab = QtWidgets.QTabWidget()
        self.mainTab.setObjectName('mainTab')

        horizontalLayout.addWidget(self.mainTab)

        self.layout.addWidget(frameTab)

    def addNavigationItem(self, itemName, iconPath):
        item = QtWidgets.QListWidgetItem()
        item.setText(itemName)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(iconPath), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        item.setIcon(icon)
        self.navigationList.addItem(item)
        self.navigationList.setCurrentRow(0)

    def addHeader(self):
        header = QtWidgets.QFrame()
        header.setObjectName('blackFrame')
        header.setFixedHeight(110)
        header.setFrameShape(QtWidgets.QFrame.StyledPanel)
        header.setFrameShadow(QtWidgets.QFrame.Raised)
        self.headerLayout = QtWidgets.QHBoxLayout(header)
        self.headerLayout.setContentsMargins(0, 0, 15, 0)
        logoLabel = QtWidgets.QLabel(header)
        logoLabel.setObjectName('logoLabel')
        self.headerLayout.addWidget(logoLabel)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.headerLayout.addItem(spacerItem)
        self.layout.addWidget(header)

        self.addSensorswgt(self.sensorWgt)
        self.addComportWgt()

    def addComportWgt(self):
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.setContentsMargins(1, 14, 10, 14)
        gridLayout.setHorizontalSpacing(5)
        gridLayout.setVerticalSpacing(1)
        # gridLayout.setAlignment(QtCore.Qt.AlignLeft)

        gridLayout2 = QtWidgets.QGridLayout()
        gridLayout2.setContentsMargins(1, 14, 10, 14)
        gridLayout2.setHorizontalSpacing(5)
        gridLayout2.setVerticalSpacing(1)
        # gridLayout2.setAlignment(QtCore.Qt.AlignLeft)

        label = QtWidgets.QLabel()
        label.setText("Serial")
        gridLayout.addWidget(label, 0, 0, 1, 1, QtCore.Qt.AlignLeft)

        self.serial_select = QtWidgets.QRadioButton()
        self.serial_select.setChecked(False)
        gridLayout.addWidget(self.serial_select, 0, 1, 1, 1, QtCore.Qt.AlignLeft)
        
        label = QtWidgets.QLabel()
        label.setText("PORT:")
        gridLayout.addWidget(label, 1, 0, 1, 1, QtCore.Qt.AlignLeft)

        self.portComboBox = QtWidgets.QComboBox()
        self.portComboBox.setFixedSize(120, 20)
        gridLayout.addWidget(self.portComboBox, 1, 1, 1, 1, QtCore.Qt.AlignLeft)

        label = QtWidgets.QLabel()
        label.setText("BAUD:")
        gridLayout.addWidget(label, 2, 0, 1, 1, QtCore.Qt.AlignLeft)

        self.buadrateComboBox = QtWidgets.QComboBox()
        self.buadrateComboBox.setFixedSize(120, 20)
        self.buadrateComboBox.addItems(buadRateList)
        gridLayout.addWidget(self.buadrateComboBox, 2, 1, 1, 1, QtCore.Qt.AlignLeft)

        label = QtWidgets.QLabel()
        label.setText("UDP")
        gridLayout2.addWidget(label, 0, 0, 1, 1, QtCore.Qt.AlignLeft)

        self.udp_select = QtWidgets.QRadioButton()
        self.udp_select.setChecked(True)
        gridLayout2.addWidget(self.udp_select, 0, 1, 1, 1, QtCore.Qt.AlignLeft)

        label = QtWidgets.QLabel()
        label.setText("ADDR:")
        gridLayout2.addWidget(label, 1, 0, 1, 1, QtCore.Qt.AlignLeft)

        self.udpaddress = QtWidgets.QLineEdit()
        self.udpaddress.setFixedSize(120, 20)
        # self.udpaddress.setPlaceholderText("127.0.0.1")
        self.udpaddress.setText("127.0.0.1")
        gridLayout2.addWidget(self.udpaddress, 1, 1, 1, 1, QtCore.Qt.AlignLeft)

        label = QtWidgets.QLabel()
        label.setText("PORT:")
        gridLayout2.addWidget(label, 2, 0, 1, 1, QtCore.Qt.AlignLeft)

        self.udpport = QtWidgets.QLineEdit()
        self.udpport.setFixedSize(120, 20)
        # self.udpport.setPlaceholderText("14445")
        self.udpport.setText("14445")
        gridLayout2.addWidget(self.udpport, 2, 1, 1, 1, QtCore.Qt.AlignLeft)

        self.headerLayout.addLayout(gridLayout2)
        self.headerLayout.addLayout(gridLayout)

        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.setContentsMargins(-1, 19, -1, 9)
        ConnectBtnLyt = QtWidgets.QHBoxLayout()
        self.connectBtn = QtWidgets.QToolButton()
        self.connectBtn.setFixedWidth(50)
        self.connectBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.connectBtn.setObjectName('connectBtn')
        self.connectBtn.setCheckable(True)
        self.connectBtn.setIconSize(QtCore.QSize(50, 50))
        ConnectBtnLyt.addWidget(self.connectBtn)
        verticalLayout.addLayout(ConnectBtnLyt)
        self.connectLabel = QtWidgets.QLabel()
        self.connectLabel.setFixedWidth(100)
        self.connectLabel.setObjectName('connectLabel')
        self.connectLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.connectLabel.setText("Connect")
        verticalLayout.addWidget(self.connectLabel)

        self.headerLayout.addLayout(verticalLayout)

    def addSensorswgt(self, sensor_dict):
        self.frameSensors = QtWidgets.QFrame()
        self.headerLayout.addWidget(self.frameSensors)
        self.frameSensors.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frameSensors.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frameSensors.setObjectName('frameSensors')

        frameLayout = QtWidgets.QHBoxLayout(self.frameSensors)
        frameLayout.setContentsMargins(20, 0, 20, 0)
        frameLayout.setSpacing(0)

        for key in sensor_dict:
            btn = QtWidgets.QToolButton(self.frameSensors)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(sensor_dict[key]['iconOff']), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            btn.setIcon(icon)
            btn.setIconSize(QtCore.QSize(40, 40))
            btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            btn.setText(QtCore.QCoreApplication.translate("MainWindow", sensor_dict[key]['name']))
            btn.setEnabled(False)
            sensor_dict[key].setdefault('btn', btn)

            frameLayout.addWidget(btn)

        self.frameSensors.setHidden(True)


