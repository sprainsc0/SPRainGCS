# -*- coding: utf-8 -*-
'''
# Created on Dec-31-19 20:05 
# tab_summary.py
# @author: 
'''

import sys, os, time
from PyQt5 import QtCore, QtGui, QtWidgets

sys.path.append(os.getcwd())
from lib.mavlink_handle import Mav_Handle, custom_protocal

summary_dict = {}
summary_list = [
    custom_protocal.MAVLink_attitude_message,
    custom_protocal.MAVLink_local_position_ned_message,
    custom_protocal.MAVLink_scaled_imu_message,
    custom_protocal.MAVLink_scaled_imu2_message,
    custom_protocal.MAVLink_scaled_pressure_message,
    custom_protocal.MAVLink_gps_raw_int_message,
    custom_protocal.MAVLink_optical_flow_message,
    custom_protocal.MAVLink_distance_sensor_message,
    custom_protocal.MAVLink_battery_status_message,
    custom_protocal.MAVLink_rc_channels_message,
]

for msg in summary_list:
    summary_dict.setdefault(msg.name, {})
    summary_dict[msg.name].setdefault('fieldnames', msg.fieldnames)
    summary_dict[msg.name].setdefault('fielddisplays_by_name', msg.fieldunits_by_name)

# @msg: Atitude, Position, Gyro, Accel, Mag, Baro, LiDAR, Flow (or Vision), Bat, RCIN, RCOUT
# @function: show the statues of the copter
class tabSummary(QtWidgets.QTabBar):
    def __init__(self, *agrs, **kwargs):
        super(tabSummary, self).__init__(*agrs, **kwargs)
        self.tabNameStr = 'Summary'
        self.layout = QtWidgets.QVBoxLayout(self)
        self.icon = 'resource/icon_summary_64.svg'

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setObjectName('blackWgt_noBorder')
        scrollAreaWidgetContents = QtWidgets.QWidget()
        scrollAreaWidgetContents.setObjectName('blackWgt_noBorder')
        scrollArea.setWidget(scrollAreaWidgetContents)
        self.scrollAreaLayout = QtWidgets.QGridLayout(scrollAreaWidgetContents)
        self.scrollAreaLayout.setSpacing(20)
        # self.scrollAreaLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self.scrollAreaLayout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.addWidget(scrollArea)

        # save the label wgt
        self.label_dict = {}
        self.update_label_time = {}

        _cnt = 0
        for key in summary_dict:
            pos = [_cnt / 4, _cnt % 4]
            self.addGroup(summary_dict[key], key, pos)
            _cnt = _cnt + 1

        Mav_Handle._msg_singal.connect(self.updateMsg)        

    def addGroup(self, sum_dict, name, pos):
        """
        add a group wgt to show a msg.
        Args: 
            sum_dict: dict of a msg
            name: name of the group
            pos: position of the wgt in gridLayout 
        """
        group = QtWidgets.QGroupBox()
        group.setObjectName('blackWgt_1pxBorder')
        # group.setFixedSize(250, 320)
        group.setFixedSize(320, 320)
        groupLayout = QtWidgets.QVBoxLayout(group)
        groupLayout.setContentsMargins(0,0,0,0)
        groupLayout.setAlignment(QtCore.Qt.AlignTop)

        headerLabel = QtWidgets.QLabel()
        headerLabel.setFixedHeight(25)
        headerLabel.setText(name)
        headerLabel.setObjectName('headerLabel')
        headerLabel.setAlignment(QtCore.Qt.AlignCenter)
        groupLayout.addWidget(headerLabel)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setObjectName('summaryScl')
        scrollAreaWidgetContents = QtWidgets.QWidget()
        scrollAreaWidgetContents.setObjectName('summaryScl')
        scrollArea.setWidget(scrollAreaWidgetContents)
        scrollAreaLayout = QtWidgets.QVBoxLayout(scrollAreaWidgetContents)
        scrollAreaLayout.setContentsMargins(0,0,0,0)
        scrollAreaLayout.setAlignment(QtCore.Qt.AlignTop)
        groupLayout.addWidget(scrollArea)

        formLayout = QtWidgets.QFormLayout()
        formLayout.setContentsMargins(10, 0, 10, 0)
        self.label_dict.setdefault(name, {})
        self.update_label_time.setdefault(name, 0)
        _cnt = 0
        for key in sum_dict['fieldnames']:
            nameLabel = QtWidgets.QLabel()
            nameLabel.setText(key)
            nameLabel.setObjectName('nameLabel')
            formLayout.setWidget(_cnt, QtWidgets.QFormLayout.LabelRole, nameLabel)
            frame = QtWidgets.QFrame()
            frameLayout = QtWidgets.QHBoxLayout(frame)
            frameLayout.setAlignment(QtCore.Qt.AlignRight)
            frameLayout.setContentsMargins(0,0,0,0)
            frameLayout.setSpacing(5)
            valueLabel = QtWidgets.QLabel()
            valueLabel.setText('-')
            valueLabel.setObjectName('valueLabel')
            self.label_dict[name].setdefault(key, valueLabel)
            uintLabel = QtWidgets.QLabel()
            if key in sum_dict['fielddisplays_by_name']:
                uintLabel.setText(sum_dict['fielddisplays_by_name'][key])
            else:
                uintLabel.setText('')
            uintLabel.setObjectName('uintLabel')
            uintLabel.setFixedWidth(50)
            uintLabel.setAlignment(QtCore.Qt.AlignHCenter)
            frameLayout.addWidget(valueLabel)
            frameLayout.addWidget(uintLabel)
            valueLabel.setAlignment(QtCore.Qt.AlignRight)
            formLayout.setWidget(_cnt, QtWidgets.QFormLayout.FieldRole, frame)
            _cnt = _cnt + 1
        scrollAreaLayout.addLayout(formLayout)

        self.scrollAreaLayout.addWidget(group, *pos)

    def updateMsg(self, msg):
        msg_dict = msg.to_dict()
        if msg_dict['mavpackettype'] in summary_dict:
            # * set the ui fresh frequency in 10hz
            if time.time() - self.update_label_time[msg.name] < 0.2:
                return

            for key in summary_dict[msg.name]['fieldnames']:
                try:
                    self.label_dict[msg.name][key].setText(str(round(msg_dict[key], 3)))
                except:
                    pass
            self.update_label_time[msg.name] = time.time()
   


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabSummary()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())


