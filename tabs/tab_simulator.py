# -*- coding: utf-8 -*-
'''
# Created on Jan-03-20 08:39 
# tab_calibrate.py
# @author: 
'''
import sys, os, time, numpy, re, math
from PyQt5 import QtCore, QtGui, QtWidgets

# import pybullet for physics simulation
import pybullet as p

sys.path.append(os.getcwd())
from lib.mavlink_handle import custom_protocal, Mav_Handle
from lib.plot import graph_sim

# @msgs: 
# @function: copter calibrate 
class tabSimulator(QtWidgets.QTabBar):
    def __init__(self, *agrs, **kwargs):
        super(tabSimulator, self).__init__(*agrs, **kwargs)
        self.tabNameStr = 'Simulator'
        frameTab = QtWidgets.QFrame()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout_status = QtWidgets.QHBoxLayout(frameTab)
        self.layout_status.setAlignment(QtCore.Qt.AlignLeft)
        
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        # 设置边距
        self.layout.setContentsMargins(15, 15, 15, 15)
        # 设置控件上下距
        self.layout.setSpacing(2)
        self.icon = 'resource/icon_quadcopter_64.svg'

        self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.layout.addWidget(self.mainSplitter)

        self.graph = graph_sim()
        self.mainSplitter.addWidget(self.graph.window)

        self.simBtn = QtWidgets.QPushButton()
        self.simBtn.setText("Simulation Start")
        self.simBtn.setFixedWidth(200)
        self.simBtn.setFixedHeight(30)
        self.simBtn.setObjectName('simButton')
        self.simBtn.setStyleSheet("color:black;background-color: CornflowerBlue")
        
        self.simBtn.clicked.connect(self.simBtnClick)

        self.modeLabel = QtWidgets.QLabel()
        self.modeLabel.setFixedWidth(100)
        self.modeLabel.setFixedHeight(30)
        self.modeLabel.setObjectName('modeLabel')
        self.modeLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.modeLabel.setStyleSheet("color:black;background-color: CornflowerBlue")
        self.modeLabel.setText("Att")

        self.armedLabel = QtWidgets.QLabel()
        self.armedLabel.setFixedWidth(100)
        self.armedLabel.setFixedHeight(30)
        self.armedLabel.setObjectName('armedLabel')
        self.armedLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.armedLabel.setStyleSheet("color:black;background-color: CornflowerBlue")
        self.armedLabel.setText("Disarm")

        self.layout_status.addWidget(self.armedLabel)
        self.layout_status.addWidget(self.modeLabel)
        self.layout_status.addWidget(self.simBtn)

        self.layout.addWidget(frameTab)

        Mav_Handle._msg_singal.connect(self.updateMsg)

        self.attitude = [0,0,0,1]
        self.position = [0,0,0]

        self.graph.update(self.position,self.attitude)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.sim_started = False

    def update(self):
        self.graph.update(self.position,self.attitude)
        pass
    
    def simBtnClick(self):
        if self.sim_started == False:
            self.timer.start(60)
            self.sim_started = True
            self.simBtn.setText("Simulation Stop")
            self.simBtn.setStyleSheet("color: black; background-color: Red")
        else:
            self.timer.stop()
            self.sim_started = False
            self.simBtn.setText("Simulation Start")
            self.simBtn.setStyleSheet("color: black; background-color: CornflowerBlue")

    def updateMsg(self, msg):
        if msg.get_srcSystem() != 1:
            return
        # * get compass data and plot in graph
        if msg.get_type() == 'ATTITUDE':
            self.attitude = p.getQuaternionFromEuler([msg.roll,-msg.pitch,-msg.yaw])
            
        if msg.get_type() == 'LOCAL_POSITION_NED':
            self.position = (msg.x,-msg.y, -msg.z)
        
        if msg.get_type() == 'HEARTBEAT':
            armed = msg.base_mode & (1<<7)
            # main_mode = (msg.custom_mode>>8) & 0xFF
            main_mode = msg.custom_mode & 0xFF
            sub_mode = (msg.custom_mode>>8) & 0xFF
            # print('base_mode' + str(msg.base_mode))
            # print('armed' + str(armed))
            # print('custom_mode' + str(msg.custom_mode))
            # print('main_mode' + str(main_mode))
            if armed > 0:
                self.armedLabel.setText("Armed")
                self.armedLabel.setStyleSheet("color: red; background-color: CornflowerBlue")
            else:
                self.armedLabel.setText("Disarm")
                self.armedLabel.setStyleSheet("color: black; background-color: CornflowerBlue")
            
            if main_mode == 7:
                self.modeLabel.setText("ATT")
            elif main_mode == 2:
                self.modeLabel.setText("ALT")
            elif main_mode == 3:
                self.modeLabel.setText("POS")
            elif main_mode == 4:
                if sub_mode == 2:
                    self.modeLabel.setText("AUTO-Takeoff")
                elif sub_mode == 4:
                    self.modeLabel.setText("AUTO-Mission")
                elif sub_mode == 5:
                    self.modeLabel.setText("AUTO-RTL")
                elif sub_mode == 6:
                    self.modeLabel.setText("AUTO-Land")
                else:
                    self.modeLabel.setText("AUTO-None")
                
            else:
                self.modeLabel.setText("None")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabSimulator()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())




