# -*- coding: utf-8 -*-
'''
# Created on Jan-03-20 08:39 
# tab_calibrate.py
# @author: 
'''
import sys, os, time, numpy, re, math
from PyQt5 import QtCore, QtGui, QtWidgets

sys.path.append(os.getcwd())
from lib.mavlink_handle import custom_protocal, Mav_Handle
from lib.plot import graph_3d

# @msgs: 
# @function: copter calibrate 
class tabCalibrate(QtWidgets.QTabBar):
    def __init__(self, *agrs, **kwargs):
        super(tabCalibrate, self).__init__(*agrs, **kwargs)
        self.tabNameStr = 'Calibrate'
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setContentsMargins(50, 25, 50, 100)
        self.layout.setSpacing(15)
        self.icon = 'resource/icon_calibrate_64.svg'

        self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.layout.addWidget(self.mainSplitter)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.textWgt = QtWidgets.QPlainTextEdit()
        self.textWgt.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.textWgt.setObjectName('ConsoleWgt')
        self.textWgt.setReadOnly(True)
        splitter.addWidget(self.textWgt)

        self.graph = graph_3d()
        splitter.addWidget(self.graph.w)
        self.mainSplitter.addWidget(splitter)

        self.accCalProgress = 0
        self.accProgressBar = QtWidgets.QProgressBar()
        self.addCalWgt('Accelerometer Calibrate', self.accProgressBar, self.accCalBtnClick)

        self.compass_data_buf = []
        self.compassCalProgress = 0
        self.compassProgressBar = QtWidgets.QProgressBar()
        self.addCalWgt('Compass Calibrate', self.compassProgressBar, self.compassCalBtnClick)

        # self.rcProgressBar = QtWidgets.QProgressBar()
        # self.addCalWgt('RC Calibrate', self.rcProgressBar, self.rcCalBtnClick)

        # self.escProgressBar = QtWidgets.QProgressBar()
        # self.addCalWgt('ESC Calibrate', self.escProgressBar, self.escCalBtnClick)

        Mav_Handle._msg_singal.connect(self.updateMsg)

        self.compass_cal_flg = False

        # * 校准之后的参数，key值和参数名保持一致
        self.compass_cal_result = {
            'CAL_MAG0_XOFF'     :None,
            'CAL_MAG0_YOFF'     :None,
            'CAL_MAG0_ZOFF'     :None,
            'CAL_MAG0_XDIAG'    :None,
            'CAL_MAG0_YDIAG'    :None,
            'CAL_MAG0_ZDIAG'    :None,
            'CAL_MAG0_XOFFDIA'  :None,
            'CAL_MAG0_YOFFDIA'  :None,
            'CAL_MAG0_ZOFFDIA'  :None,
        }
        self.transform_mat = numpy.empty((3,3),dtype = float)
        self.translate_mat = numpy.empty((3,1),dtype = float)

    def updateMsg(self, msg):
        if msg.get_type() == 'COMMAND_ACK':
            command = custom_protocal.enums['MAV_CMD'][msg.command]
            result = custom_protocal.enums['MAV_RESULT'][msg.result]
            self.textWgt.appendPlainText(command.description)
            self.textWgt.appendPlainText(result.description)

        if msg.get_type() == 'CALIBRATE_STATUS':
            cal_type = custom_protocal.enums['MAV_CALIBRATE_TYPE'][msg.type]

            # * deal acc calibration
            if cal_type.name == 'MAV_ACCL_CALIBRATE':
                cal_status = custom_protocal.enums['MAV_ACCL_CALIBRATION'][msg.status]
                # * set progressbar value
                if msg.status == 3 or msg.status == 4 or msg.status == 5 or msg.status == 6\
                    or msg.status == 7 or msg.status == 8:
                    self.accCalProgress += 100/6
                # * calibration failed
                if msg.status == 2:
                    self.accCalProgress = 0
                self.accProgressBar.setValue(self.accCalProgress)
            
            # * deal compass calibration
            if cal_type.name == 'MAV_MAG_CALIBRATE':
                cal_status = custom_protocal.enums['MAV_MAG_CALIBRATION'][msg.status]
                # * set progressbar value
                if msg.status == 3:
                    self.compass_cal_flg = True
                    self.graph.addItem('RawMag', self.graph.pinkcolor)
                if msg.status == 4 or msg.status == 5:
                    self.compassCalProgress += 100/3
                # * calibration failed
                elif msg.status == 2:
                    self.compass_cal_flg = False
                    self.compassCalProgress = 0
                # * calibration success
                elif msg.status == 1:
                    self.compass_cal_flg = False
                    self.compassCalProgress = 100
                    Mav_Handle.param_request_list()
                self.compassProgressBar.setValue(self.compassCalProgress)

            self.textWgt.appendPlainText(f'{cal_type.description}: {cal_status.description}\n')

        # * get compass data and plot in graph
        if self.compass_cal_flg and msg.get_type() == 'SCALED_IMU':
            data = (msg.xmag/100, msg.ymag/100, msg.zmag/100)
            self.compass_data_buf.append(data)
            data = (msg.xmag/100-4, msg.ymag/100, msg.zmag/100+2)
            self.graph.setItemData('RawMag', data)

        # * get compass calibration result
        if msg.get_type() == 'PARAM_VALUE' and self.compassCalProgress == 100:
            if msg.param_id in self.compass_cal_result:
                print(f'get param: {msg.param_id}, value: {round(msg.param_value, 7)}')
                self.compass_cal_result[msg.param_id] = msg.param_value
                self.calResult()

    def calResult(self):
        for key in self.compass_cal_result:
            if self.compass_cal_result[key] == None:
                return
        self.graph.addItem('CalMag', self.graph.greencolor)
        offsets_x = self.compass_cal_result['CAL_MAG0_XOFF']
        offsets_y = self.compass_cal_result['CAL_MAG0_YOFF']
        offsets_z = self.compass_cal_result['CAL_MAG0_ZOFF']
        diagonals_x = self.compass_cal_result['CAL_MAG0_XDIAG']
        diagonals_y = self.compass_cal_result['CAL_MAG0_YDIAG']
        diagonals_z = self.compass_cal_result['CAL_MAG0_ZDIAG']
        offdiagonals_x = self.compass_cal_result['CAL_MAG0_XOFFDIA']
        offdiagonals_y = self.compass_cal_result['CAL_MAG0_YOFFDIA']
        offdiagonals_z = self.compass_cal_result['CAL_MAG0_ZOFFDIA']
        mat = numpy.array([
            [diagonals_x,    offdiagonals_x, offdiagonals_y],
            [offdiagonals_x, diagonals_y,    offdiagonals_z],
            [offdiagonals_y, offdiagonals_z, diagonals_z]
        ])    
        offsets = numpy.array([
            [offsets_x],
            [offsets_y],
            [offsets_z],
        ])
        self.transform_mat = numpy.linalg.inv(mat)
        self.translate_mat = offsets/100
        self.translate_mat[0,0] = self.translate_mat[0,0]+4
        self.translate_mat[2,0] = self.translate_mat[2,0]-2
        radius = 0
        for mag in self.compass_data_buf:
            data = numpy.array([
                [mag[0]],
                [mag[1]],
                [mag[2]],
            ])
            result = data*100 + offsets
            CalMag = numpy.dot(mat, result)
            self.graph.setItemData('CalMag', (CalMag[0][0]/100+4, CalMag[1][0]/100, CalMag[2][0]/100))        
            radius = radius + math.sqrt(pow(CalMag[0][0]/100,2)+pow(CalMag[1][0]/100,2)+pow(CalMag[2][0]/100,2))
        radius = radius/(self.compass_data_buf.__len__())
        self.graph.plotSphere(transform_mat=self.transform_mat,translate_mat=self.translate_mat,radius=radius-0.1) #radius= 3.2
        self.graph.plotSphere(radius=radius-0.1) #radius= 3.2
        

    def addCalWgt(self, name, progressBar, clickCallBack):
        frame = QtWidgets.QFrame()
        frame.setFixedHeight(30)
        frameLayout = QtWidgets.QHBoxLayout(frame)
        frameLayout.setContentsMargins(0,0,0,10)
        frameLayout.setSpacing(5)
        accCalBtn = QtWidgets.QPushButton()
        accCalBtn.setText(name)
        accCalBtn.setFixedSize(200, 20)
        accCalBtn.setObjectName('blackPushButton')
        accCalBtn.clicked.connect(clickCallBack)
        progressBar.setTextVisible(False)
        progressBar.setFixedHeight(20)
        frameLayout.addWidget(accCalBtn)
        frameLayout.addWidget(progressBar)
        self.mainSplitter.addWidget(frame)

    def accCalBtnClick(self):
        self.accCalProgress = 0
        self.accProgressBar.setValue(self.accCalProgress)
        Mav_Handle.acc_calibration_start()

    def compassCalBtnClick(self):
        self.compassCalProgress = 0
        self.compass_data_buf.clear()
        self.compassProgressBar.setValue(self.compassCalProgress)
        self.graph.removeAllItem()
        Mav_Handle.compass_calibration_start()

    def rcCalBtnClick(self):
        pass

    def escCalBtnClick(self):
        pass

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabCalibrate()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())




