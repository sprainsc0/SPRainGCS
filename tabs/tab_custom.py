# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
'''
# Created on Feb-21-20 15:09 
# tab_custom.py
# @author: 
'''

import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

from tabs.tab_plot import add_plot_tree_list

sys.path.append(os.getcwd())
from lib.plot import graph, graphThread
from lib.serial_handle import SerialHandle
from lib.protocol_v1 import TelemParser, TelemK, B2V
from lib.delegate import Delegate

Msg = TelemParser

name_list = [
    'rol    ',
    'pch    ',
    'yaw    ',
    'v4     ',
    'v5     ',
    'v6     ',
    'v7     ',
    'v8     ',
    'v9     ',
    'v10    ',
    'v11    ',
    'v12    ',
    'v13    ',
]

# 调试用重写下拉复选框
class MyComboBox(QtWidgets.QComboBox):
    clicked = QtCore.pyqtSignal()  #创建一个信号
    def showPopup(self):  #重写showPopup函数
        self.clicked.emit()  #发送信号
        QtWidgets.QComboBox.showPopup(self)

class tabCustom(QtWidgets.QTabBar):
    def __init__(self, *agrs, **kwargs):
        super(tabCustom, self).__init__(*agrs, **kwargs)
        self.tabNameStr = 'Custom'
        self.layout = QtWidgets.QVBoxLayout(self)
        self.icon = 'resource/icon_plot_64.svg'
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        Msg.init()
        Delegate.add_listener(TelemK.ktelem_plot, self.rcvPlotData)

        self.y_axis_dict = {}
        self.plot_list_wgt = {}

        frame = QtWidgets.QFrame()
        frameLayout = QtWidgets.QHBoxLayout(frame)
        frameLayout.setContentsMargins(20,2,20,2)
        self.clearBtn = QtWidgets.QPushButton()
        self.clearBtn.setText('CLEAR')
        self.clearBtn.setObjectName('blackPushButton')
        self.clearBtn.setFixedSize(80, 20)
        self.clearBtn.clicked.connect(self.clearBtnClicked)
        self.stopBtn = QtWidgets.QPushButton()
        self.stopBtn.setObjectName('blackPushButton')
        self.stopBtn.setText('STOP')
        self.stopBtn.setFixedSize(80, 20)
        self.stopBtn.setCheckable(True)
        self.stopBtn.clicked.connect(self.stopBtnClicked)
        frameLayout.addWidget(self.clearBtn)
        frameLayout.addWidget(self.stopBtn)

        # 串口名称下拉框
        self.combo = MyComboBox()
        self.combo.setFixedSize(100, 20)
        self.combo.clicked.connect(self.onPullComList)
        # 连接或断开串口按钮
        self.btn_connect = QtWidgets.QPushButton('Connect')
        self.btn_connect.setFixedSize(100, 20)
        self.btn_connect.setCheckable(True)
        self.btn_connect.clicked.connect(self.comConnectOrNot)
        self.btn_connect.setObjectName('blackPushButton')
        self.btn_connect.setStyleSheet('#blackPushButton{background-color:rgb(24, 152, 63); color:white}')
        frameLayout.addWidget(self.btn_connect)
        frameLayout.addWidget(self.combo)

        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        frameLayout.addItem(spacerItem)
        self.layout.addWidget(frame)


        frame = QtWidgets.QFrame()
        frameLayout = QtWidgets.QHBoxLayout(frame)
        frameLayout.setContentsMargins(0,0,0,0)
        frameLayout.setSpacing(0)

        # 添加TreeWidget
        self.treewgt = QtWidgets.QTreeWidget()
        self.treewgt.setHeaderHidden(True)
        self.treewgt.setMaximumWidth(300)
        self.treewgt.setObjectName('blackFrame')
        self.treewgt.setIndentation(0)

        self.graph = graph(self.y_axis_dict)
        self.graph.p.setRange(QtCore.QRectF(0, -400, 1000, 800))
        self.graph_thread = graphThread(self.graph)
        self.graph_thread.start()
        self.graph.p.resize(QtCore.QSize(1500,16777215))
        self.graph.p.plotItem.showGrid(True, True, 0.25)
        self.graph.addMouseLine()
        frameLayout.addWidget(self.graph.p)
        frameLayout.addWidget(self.treewgt)

        self.layout.addWidget(frame)

        self.com = SerialHandle()
        self.addPlotList('All', name_list)
        self.treewgt.expandAll()

    def rcvPlotData(self, msg_data):
        values = B2V.unpack_to_float(msg_data)
        if type(values) is float:
            self.y_axis_dict.setdefault(f'All -> {name_list[0]}', []).append(values[i])

        for i in range(len(values)):
            self.y_axis_dict.setdefault(f'All -> {name_list[i]}', []).append(values[i])
            self.updateValue('All', name_list[i], values[i])        

    # 拉取串口回调
    def onPullComList(self):
        self.combo.clear()
        names = self.com.get_port_names()
        for n in names:
            self.combo.addItem(n)
    
    def comConnectOrNot(self):
        if self.btn_connect.isChecked():
            if self.com.open(self.combo.currentText(), 115200):
                self.btn_connect.setText('DisConnect')
                self.btn_connect.setStyleSheet('#blackPushButton{background-color:rgb(174, 102, 4); color:white}')
            else:
                self.btn_connect.setChecked(False)
        else:
            self.com.close()
            self.btn_connect.setText('Connect')
            self.btn_connect.setStyleSheet('#blackPushButton{background-color:rgb(24, 152, 63); color:white}')

    def clearBtnClicked(self):
        for key in self.y_axis_dict:
            self.y_axis_dict[key] = []

    def stopBtnClicked(self):
        if self.graph_thread.pause == False:
            self.graph_thread.pause = True
        else:
            self.graph_thread.pause = False

    def addPlotList(self, name, child_name_list):
        if name not in self.plot_list_wgt:
            tree_list = add_plot_tree_list(self.treewgt, self.graph)
            tree_list.addList(name, child_name_list)
            self.plot_list_wgt.setdefault(name, tree_list)

    def updateValue(self, list_name, label, value):
        try:
            if list_name in self.plot_list_wgt:
                self.plot_list_wgt[list_name].label_dict[label].setText(str(round(value, 3)))
        except Exception as e:
            pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabCustom()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())


