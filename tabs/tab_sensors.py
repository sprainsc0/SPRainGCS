# -*- coding: utf-8 -*-
'''
# Created on Jan-04-20 00:53 
# tab_sensors.py
# @author: 
'''

import sys, os
import random
from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

sys.path.append(os.getcwd())
from lib.plot import graph

plot_axis_buf = {}

notifiy_str = '''
Please note: setting the refresh rate too high will increase the communication burden.
It is recommended that you only turn on the graphics display and reasonable refresh rate of the sensor you are interested in.
'''

background_list = [
    'background:#00abee;',
    'background:#bed805;',
    'background:#cf484c;',
    'background:#c82a77',
    'background:#ffbf2d',
    'background:#169582',
]

sensor_dict = {
    'GYRO' : {
        'TMP':[],
        'X:':[],
        'Y:':[],
        'Z:':[],
    },
    'ACCEL' : {
        'TMP':[],
        'X:':[],
        'Y:':[],
        'Z:':[],
    },
    'MAG' : {
        'X:':[],
        'Y:':[],
        'Z:':[],
    },
    'BARO' : {
        'ALT:':[],
        'TMP:':[],
    },
    'LIDAR' : {
        'DST:':[],
        'QUL:':[],
    },
    'FLOW' : {
        'QUL':[],
        'X:':[],
        'Y:':[],
    },
}

# @msg: Gyro, Accel, Mag, Baro, LiDAR, Flow (or Vision)
# @function: show the curve of every sensros
class tabSensors(QtWidgets.QTabBar):
    def __init__(self, *agrs, **kwargs):
        super(tabSensors, self).__init__(*agrs, **kwargs)
        self.tabNameStr = 'Sensors'
        self.layout = QtWidgets.QVBoxLayout(self)
        self.icon = 'resource/icon_sensors_64.svg'

        self.setObjectName('widget_sensors')

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollAreaWidgetContents = QtWidgets.QWidget()
        scrollArea.setObjectName('blackWgt_noBorder')
        scrollAreaWidgetContents.setObjectName('blackWgt_noBorder')
        scrollArea.setWidget(scrollAreaWidgetContents)
        self.scrollAreaLayout = QtWidgets.QVBoxLayout(scrollAreaWidgetContents)
        self.scrollAreaLayout.setSpacing(15)
        self.scrollAreaLayout.setContentsMargins(10,0,10,0)
        self.layout.addWidget(scrollArea)

        notifyLabel = QtWidgets.QLabel()
        notifyLabel.setText(notifiy_str)
        notifyLabel.setObjectName('notifyLabel')
        self.scrollAreaLayout.addWidget(notifyLabel)

        self.addSensorBtn()

        self.graphList = []
        self.groupDict = {}
        for key in sensor_dict:
            self.addGroup(sensor_dict[key], key)

        spacer_sensors = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.scrollAreaLayout.addItem(spacer_sensors)

    def addSensorBtn(self):

        group = QtWidgets.QGroupBox(self)
        group.setFixedHeight(40)
        group.setTitle('')

        groupLayout = QtWidgets.QHBoxLayout(group)
        groupLayout.setSpacing(30)
        groupLayout.setContentsMargins(10,0,10,0)
        for key in sensor_dict:
            checkBox = QtWidgets.QCheckBox()
            checkBox.setObjectName('checkBoxSwitch')
            checkBox.setText(key)
            checkBox.stateChanged.connect(partial(self.checkBoxchecked, key, checkBox))
            groupLayout.addWidget(checkBox)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        groupLayout.addItem(spacerItem)
        self.scrollAreaLayout.addWidget(group)

    def checkBoxchecked(self, key, checkBox):
        if checkBox.checkState():
            self.groupDict[key].setHidden(False)
        else:
            self.groupDict[key].setHidden(True)

    def addGroup(self, sensorSet, sensorName):

        group = QtWidgets.QGroupBox(self)
        self.groupDict.setdefault(sensorName, group)
        group.setHidden(False)
        group.setTitle("")
        group.setFixedHeight(220)
        groupLayout = QtWidgets.QHBoxLayout(group)
        groupLayout.setContentsMargins(0, 0, 0, 0)
        groupLayout.setSpacing(0)
        
        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.setContentsMargins(12, 12, 18, 12)
        verticalLayout.setSpacing(0)
        groupLayout.addLayout(verticalLayout)
        graph_debugplot = graph(plot_axis_buf)
        graph_debugplot.p.setRange(QtCore.QRectF(0, -1000, 5000, 2000))
        graph_debugplot.p.plotItem.showGrid(True, True, 0.3)
        verticalLayout.addWidget(graph_debugplot.p)
        self.graphList.append(graph_debugplot)
        # self.thread_debugplot = graphThread(self.graph_debugplot)
        # self.thread_debugplot.start()

        frameSensor = QtWidgets.QFrame(group)
        frameSensor.setObjectName('tabSensorFrame')
        frameSensor.setFrameShape(QtWidgets.QFrame.StyledPanel)
        frameSensor.setFrameShadow(QtWidgets.QFrame.Raised)
        frameSensorLayout = QtWidgets.QVBoxLayout(frameSensor)
        frameSensorLayout.setAlignment(QtCore.Qt.AlignTop)
    
        sensorLabel=QtWidgets.QLabel(frameSensor)
        sensorLabel.setMaximumSize(QtCore.QSize(16777215,20))
        sensorLabel.setStyleSheet("QLabel{font-weight:bold;}")
        # sensorLabel.setText('GYRO - deg/s')
        sensorLabel.setText(sensorName)
        frameSensorLayout.addWidget(sensorLabel)

        frqLayout=QtWidgets.QHBoxLayout()
        fraLabel = QtWidgets.QLabel(frameSensor)
        fraLabel.setText('FRESH:')
        frqLayout.addWidget(fraLabel)
        frqComboBox = QtWidgets.QComboBox(frameSensor)
        frqLayout.addWidget(frqComboBox)
        frameSensorLayout.addLayout(frqLayout)

        valueLayout=QtWidgets.QGridLayout()
        valueLayout.setContentsMargins(0, 10,0, 10)

        _cnt = 0
        for key in sensorSet:
            checkbox = QtWidgets.QCheckBox(frameSensor)
            checkbox.setText(key)
            checkbox.setFixedWidth(80)
            valueLayout.addWidget(checkbox, _cnt, 0, 1, 1)
            line = QtWidgets.QLineEdit(frameSensor)
            line.setText('0')
            line.setAlignment(QtCore.Qt.AlignCenter)
            line.setStyleSheet(background_list[_cnt])
            valueLayout.addWidget(line, _cnt, 1, 1, 1)
            _cnt = _cnt + 1

        frameSensorLayout.addLayout(valueLayout)

        saveBtn = QtWidgets.QPushButton(frameSensor)
        saveBtn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        saveBtn.setText("SAVE")
        saveBtn.setFixedHeight(20)
        frameSensorLayout.addWidget(saveBtn)

        groupLayout.addWidget(frameSensor)
        self.scrollAreaLayout.addWidget(group)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabSensors()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())

