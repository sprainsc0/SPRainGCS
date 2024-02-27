# -*- coding: utf-8 -*-
'''
# Created on Dec-31-19 19:41 
# tab_plot.py
# @author: 
'''

import sys, os, time
from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

sys.path.append(os.getcwd())
from lib.plot import graph, graphThread
from lib.mavlink_handle import Mav_Handle

class tabPlot(QtWidgets.QTabBar):
    def __init__(self, *agrs, **kwargs):
        super(tabPlot, self).__init__(*agrs, **kwargs)
        self.tabNameStr = 'Plot'
        self.layout = QtWidgets.QVBoxLayout(self)
        self.icon = 'resource/icon_plot_64.svg'
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        self.x_axis_dict = {}
        self.y_axis_dict = {}
        # * 记录label更新时间
        self.update_label_time = {}
        # * 记录msg接收时间，计算接收频率
        self.last_rcv_time = {}

        frame = QtWidgets.QFrame()
        frameLayout = QtWidgets.QHBoxLayout(frame)
        frameLayout.setContentsMargins(20,2,0,2)
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

        self.graph = graph(self.y_axis_dict, self.x_axis_dict)
        self.graph.p.setRange(QtCore.QRectF(0, -400, 1000, 800))
        self.graph_thread = graphThread(self.graph)
        self.graph_thread.start()
        self.graph.p.resize(QtCore.QSize(1500,16777215))
        self.graph.p.plotItem.showGrid(True, True, 0.25)
        self.graph.addMouseLine()
        frameLayout.addWidget(self.graph.p)
        frameLayout.addWidget(self.treewgt)
        self.layout.addWidget(frame)

        Mav_Handle._msg_singal.connect(self.updateMsg)
    
        self.rcvMsgLen = 0

        self.tree_list_wgt = {}

    def clearBtnClicked(self):
        for key in self.y_axis_dict:
            self.y_axis_dict[key] = []
            self.x_axis_dict[key] = []
        self.rcvMsgLen = 0

    def stopBtnClicked(self):
        if self.graph_thread.pause == False:
            self.graph_thread.pause = True
        else:
            self.graph_thread.pause = False

    def addPlotList(self, name, child_name_list, fmt_list):
        if name not in self.tree_list_wgt:
            tree_list = add_plot_tree_list(self.treewgt, self.graph)
            tree_list.addList(name, child_name_list, fmt_list)
            self.tree_list_wgt.setdefault(name, tree_list)

    def updateLabel(self, tree_name, label, value):
        """
        update the label value
        """
        if type(value) != float and type(value) !=int:
            return
        try:
            if tree_name in self.tree_list_wgt:
                self.tree_list_wgt[tree_name].label_dict[label].setText(str(round(value, 3)))
        except Exception as e:
            pass

    def updateMsg(self, msg):
        """
        singal of rcv msg
        """
        if msg.get_type() == 'BAD_DATA':
            return
        self.addPlotList(msg.get_type(), msg.fieldnames, msg.fieldtypes)
        msg_dict = msg.to_dict()

        # * 记录label更新时间
        self.update_label = False
        self.update_label_time.setdefault(msg_dict['mavpackettype'], 0)
        if time.time() - self.update_label_time[msg_dict['mavpackettype']] > 0.2:
            self.update_label = True
            self.update_label_time[msg_dict['mavpackettype']] = time.time()

        # * 记录消息接收频率
        self.last_rcv_time.setdefault(msg_dict['mavpackettype'], [time.time(), 0])
        dt = time.time() - self.last_rcv_time[msg_dict['mavpackettype']][0]
        self.last_rcv_time[msg_dict['mavpackettype']][0] = time.time()
        if dt > 0:
            self.last_rcv_time[msg_dict['mavpackettype']][1] = int(round((self.last_rcv_time[msg_dict['mavpackettype']][1] + 1/dt) / 2 , 0))
        if msg_dict['mavpackettype'] + ' -> ' + 'time_boot_ms' in self.y_axis_dict and 'time_boot_ms' in msg_dict \
            and len(self.y_axis_dict[msg_dict['mavpackettype'] + ' -> ' + 'time_boot_ms']) > 0:
            dt = msg_dict['time_boot_ms'] - self.y_axis_dict[msg_dict['mavpackettype'] + ' -> ' + 'time_boot_ms'][-1]
            if dt != 0:
                self.last_rcv_time[msg_dict['mavpackettype']][1] = int(round(1000/dt , 0))

        # * 更新label，保存数据
        self.rcvMsgLen += 1
        for key in msg_dict:
            if key == 'mavpackettype':
                continue
            time_stamp = self.rcvMsgLen
            self.x_axis_dict.setdefault(msg_dict['mavpackettype']+' -> '+ key, []).append(time_stamp)
            self.y_axis_dict.setdefault(msg_dict['mavpackettype'] + ' -> ' + key, []).append(msg_dict[key])
            if self.update_label:
                self.updateLabel(msg_dict['mavpackettype'], key, msg_dict[key])
                name = msg_dict['mavpackettype'] + '  (' + str(self.last_rcv_time[msg_dict['mavpackettype']][1]) + ' Hz)'
                self.tree_list_wgt[msg_dict['mavpackettype']].treeWgtItem.setText(0, name)


class add_plot_tree_list:
    """
    add a QTreeWidgetItem in QTreeWidget, every QTreeWidgetItem contain a checkbox and label to show the value ...
    """
    def __init__(self, QTreeWidget, graph):
        """
        Args: 
                QTreeWidget: add QTreeWidgetItem in QTreeWidget
                graph: add or remove a plot in graph
        """
        self.treewgt = QTreeWidget
        self.graph = graph
        self.label_dict = {}

    def addList(self, tree_name, child_name_list, fmt_list=None):
        """
        Args: 
            tree_name: name of the QTreeWidgetItem
            child_name_list: list of the checkbox name
            fmt_list: list of the value fmt
        """
        self.treeWgtItem = QtWidgets.QTreeWidgetItem(self.treewgt)
        self.treeWgtItem.setText(0, tree_name)

        for i in range(len(child_name_list)):
            frame = QtWidgets.QFrame()
            frameLayout = QtWidgets.QHBoxLayout(frame)
            frameLayout.setContentsMargins(0,0,10,0)
            frameLayout.setSpacing(0)
            checkbox = QtWidgets.QCheckBox()
            checkbox.setText(child_name_list[i])
            checkbox.setFixedWidth(180)
            frameLayout.addWidget(checkbox)
            label = QtWidgets.QLabel()
            label.setText('-')
            label.setAlignment(QtCore.Qt.AlignRight)
            self.label_dict.setdefault(child_name_list[i], label)
            frameLayout.addWidget(label)
            checkbox.stateChanged.connect(partial(self.checkboxChanged, tree_name, checkbox))
            self.treewgt.setItemWidget(QtWidgets.QTreeWidgetItem(self.treeWgtItem), 0, frame)

    def checkboxChanged(self, tree_name, checkbox):
        """
        checkbox click singal, add or remove a plot
        """
        label = f'{tree_name} -> {checkbox.text()}'
        try:
            if checkbox.checkState():
                self.graph.addLine(label)
            else:
                self.graph.removeLine(label)
        except Exception as e:
            checkbox.setCheckState(QtCore.Qt.Unchecked)
            print(e)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabPlot()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())


