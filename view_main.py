# -*- coding: utf-8 -*-
'''
# Created on Dec-31-19 09:07 
# view_main.py
# @author: 
'''

import sys, time, os
import importlib
import signal
import serial.tools.list_ports
from PyQt5 import QtCore, QtGui, QtWidgets

from lib.mavlink_handle import Mav_Handle
from tabs.MainWindow import MainWindow

tab_views = [
    'tab_summary.tabSummary',
    # 'tab_sensors.tabSensors',
    'tab_calibrate.tabCalibrate',
    'tab_plot.tabPlot',
    'tab_params.tabParameters',
    'tab_log.tabLog',
    'tab_simulator.tabSimulator',
    'tab_console.tabConsole',
    # 'tab_upgrade.tabUpgrade',
    # 'tab_custom.tabCustom',
]

class _thread(QtCore.QThread):
    _scanport_singal = QtCore.pyqtSignal(list)
    _timeout_singal = QtCore.pyqtSignal()
    _set_connectBtn_singal = QtCore.pyqtSignal(bool)
    def __init__(self):
        super(_thread, self).__init__()
        self.last_list = []
        self.last_rcv_msg = 0

    def run(self):
        while True:
            time.sleep(0.3)
            port_list = list(serial.tools.list_ports.comports())
            if sorted(port_list) != sorted(self.last_list):
                self._scanport_singal.emit(port_list)
            self.last_list = port_list

            if time.time() - self.last_rcv_msg > 2:
                self._timeout_singal.emit()

            self._set_connectBtn_singal.emit(Mav_Handle.is_open())

class view_main(MainWindow):
    def __init__(self):
        super().__init__()
        self.connectBtn.clicked.connect(self.connectBtnClick)

        self.navigationList.currentRowChanged['int'].connect(self.mainTab.setCurrentIndex)
        self.resize(1600, 900)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("resource/icon_airplane_nor.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        copyrightLabel = QtWidgets.QLabel()
        copyrightLabel.setText('Copyright (C) 2019-2023 FC Department V1.0.16')
        self.statusbar.addPermanentWidget(copyrightLabel)

        self.heartLabel = QtWidgets.QLabel()
        self.heartLabel.setText('HeartBeat')
        self.statusbar.addWidget(self.heartLabel)

        self.BpsLabel = QtWidgets.QLabel()
        self.BpsLabel.setText('- KBps')
        self.statusbar.addWidget(self.BpsLabel)

        Mav_Handle._msg_singal.connect(self.updateMsg)
        self.thd = _thread()
        self.thd._scanport_singal.connect(self.updateComport)
        self.thd._timeout_singal.connect(self.MavlinkTimeout)
        self.thd._set_connectBtn_singal.connect(self.setConnectBtn)
        self.thd.start()
        self.port_list = []

        # * 捕获主进程结束信号，以便结束子进程
        signal.signal(signal.SIGTERM, self.closeEvent)

    def setConnectBtn(self, isOpen):
        if isOpen:
            # self.BpsLabel.setText(f'{round((Mav_Handle.Bps/1000), 3)} KBps')
            if self.connectBtn.isChecked():
                return
            self.connectBtn.setChecked(True)
            self.connectBtn.setStyleSheet('#connectBtn{background:red;}')
            self.connectLabel.setText('DisConnect')
        else:
            self.connectBtn.setChecked(False)
            self.connectLabel.setText('Connect')
            self.connectBtn.setStyleSheet('#connectBtn{background:rgb(0, 156, 255);}')
            self.BpsLabel.setText('- KBps')

    def MavlinkTimeout(self):
        self.heartLabel.setStyleSheet('QLabel{color:red;}')
        self.heartLabel.setText('HeartBeat')

    def updateMsg(self, msg):
        if msg.get_type() != 'BAD_DATA':
            self.thd.last_rcv_msg = time.time()

        if msg.get_type() == 'HEARTBEAT':
            Mav_Handle.send_heartbeat()
            self.heartLabel.setStyleSheet('QLabel{color:rgb(0, 156, 255);}')

    def addTab(self, tab, tabName):
        index = self.mainTab.addTab(tab, tabName)

    def connectBtnClick(self):
        if self.connectBtn.isChecked() and Mav_Handle.is_open() == False:
            if self.serial_select.isChecked() :
                if len(self.port_list) == 0:
                    return
                idx = self.portComboBox.currentIndex()
                Mav_Handle.open('serial', self.port_list[idx].device, int(self.buadrateComboBox.currentText()))
            else :
                Mav_Handle.open('udp', self.udpaddress.text(), int(self.udpport.text()))
            self.connectBtn.setChecked(False)
        else:
            Mav_Handle.close()
            self.connectLabel.setText('Connect')
            self.connectBtn.setStyleSheet('#connectBtn{background:rgb(0, 156, 255);}')
            self.frameSensors.setHidden(True)

    def updateComport(self, port_list):
        self.portComboBox.clear()
        self.port_list = port_list
        for i in self.port_list:
            self.portComboBox.addItem(str(i))

    # * 退出子进程
    def closeEvent(self, event):
        Mav_Handle.exit()
        os._exit(0)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    realse_path = sys.argv[0] 
    split_path = realse_path.split('\\')
    del split_path[-1]
    use_path = '\\'.join(split_path)
    # app.setStyleSheet(open(use_path + "/dark_style.css").read())
    app.setStyleSheet(open("dark_style.css").read())

    view = view_main()
    for path in tab_views:
        print(path)
        model_path, class_name = path.rsplit(".", 1)
        model = importlib.import_module('tabs.' + model_path)
        obj = getattr(model, class_name)()
        view.addTab(obj, obj.tabNameStr)
        view.addNavigationItem(obj.tabNameStr, obj.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())
