# -*- coding: utf-8 -*-
'''
# Created on Mar-02-20 15:37 
# tab_log2.py
# @author: 
'''

import sys, os, time, copy
import code
import re
from os import path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QFileDialog
from functools import partial
from PyQt5.QtGui import QDoubleValidator

sys.path.append(os.getcwd())
import numpy as np
import scipy.io as scio
from lib.plot import graphStatic
from lib.log_parser import log_parser
from lib.mavlink_handle import Mav_Handle
import matplotlib.pyplot as plt

timeStampLabel = 'TimeUS'

def on_press(event):
    print("you pressed" ,event.button, event.xdata, event.ydata)

def samplemat(dims):
    """Make a matrix with all zeros and increasing elements on the diagonal"""
    aa = np.zeros(dims)
    for i in range(min(dims)):
        aa[i, i] = i
    return aa

class tabLog(QtWidgets.QWidget):
    _update_progress_singal = QtCore.pyqtSignal(float)
    def __init__(self, *args, **kwargs):

        super(tabLog, self).__init__(*args, **kwargs)
        self.tabNameStr = 'LogAnalysis'
        self.setObjectName(self.tabNameStr)
        self.icon = 'resource/icon_log_64.svg'

        # * --------- start UI layout
        self.layout = QtWidgets.QHBoxLayout(self) # 水平布局
        self.layout.setContentsMargins(0,0,0,0) # 设置边距 左上右下

        frame =  QtWidgets.QFrame() #基本控件
        frameLayout = QtWidgets.QVBoxLayout(frame) # 垂直布局
        frameLayout.setContentsMargins(0,0,0,0)
        frameLayout.setSpacing(0) # 各个控件间的上下边距

        # 添加绘图 TAB
        self.tab = QtWidgets.QTabWidget() # 添加TAB窗体
        self.tab.setStyleSheet('''
        QTabWidget::pane {
        border: none;
        background: rgb(57, 58, 60);
        }
        QTabWidget::tab-bar {
                border: none;
        }
        QTabWidget QTabBar::tab {
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
                color: rgb(175, 175, 175);
                background: rgba(255, 255, 255, 30);
                height: 22px;
                min-width: 145px;
                margin-right: 0px;
                margin-left: 20px;
                padding-left: 5px;
                padding-right: 5px;
        }
        QTabWidget QTabBar::tab:hover {
                background: rgba(255, 255, 255, 40);
        }
        QTabWidget QTabBar::tab:selected {
                color: white;
                background: #181616;
        }
        ''')
        graphTab = QtWidgets.QTabBar(self.tab) # 生成绘图标签
        self.tab.addTab(graphTab, 'PLOT')
        graphTabLaytout = QtWidgets.QHBoxLayout(graphTab) # 水平布局
        graphTabLaytout.setContentsMargins(0,0,0,0)
        graphTabLaytout.setSpacing(0)

        graphFrame = QtWidgets.QFrame() # 绘图控件
        graphFrame.setObjectName('blackWgt_noBorder')
        graphFrameLayout = QtWidgets.QVBoxLayout(graphFrame)
        graphFrameLayout.setSpacing(0)
        graphFrameLayout.setContentsMargins(0,0,0,0)

        frameBtn = QtWidgets.QFrame()
        btnLayout = QtWidgets.QHBoxLayout(frameBtn)

        selectBtn = QtWidgets.QPushButton()
        selectBtn.setText('LOAD')
        selectBtn.setObjectName('blackPushButton')
        selectBtn.setFixedSize(80, 20)
        selectBtn.clicked.connect(self.selectBtnClicked)

        exportBtn = QtWidgets.QPushButton()
        exportBtn.setObjectName('blackPushButton')
        exportBtn.setText('EXPORT')
        exportBtn.setFixedSize(80, 20)
        exportBtn.clicked.connect(self.exportBtnClicked)

        clearBtn = QtWidgets.QPushButton()
        clearBtn.setObjectName('blackPushButton')
        clearBtn.setText('CLEAR')
        clearBtn.setFixedSize(80, 20)
        clearBtn.clicked.connect(self.clearCheckBtnClicked)

        btnLayout.addWidget(selectBtn)
        btnLayout.addWidget(clearBtn)
        btnLayout.addWidget(exportBtn)
        btnLayout.setSpacing(5)
        btnLayout.setContentsMargins(20,8,0,2)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum) # 空白区域
        btnLayout.addItem(spacerItem)
        graphFrameLayout.addWidget(frameBtn)

        self.graph = graphStatic()
        self.graph.p.plotItem.showGrid(True, True, 0.5)
        graphFrameLayout.addWidget(self.graph.p)
        graphTabLaytout.addWidget(graphFrame) # 添加绘图

        # 绘图TAB 添加TreeWidget
        treeframe = QtWidgets.QFrame()
        treeframeLayout = QtWidgets.QVBoxLayout(treeframe)
        treeframeLayout.setContentsMargins(0,0,0,0)
        treeframeLayout.setSpacing(0)
        treeframe.setMaximumWidth(280)
        self.treewgt = QtWidgets.QTreeWidget()
        self.treewgt.setHeaderHidden(True)
        self.treewgt.setObjectName('blackFrame')
        treeframeLayout.addWidget(self.treewgt)
        graphTabLaytout.addWidget(treeframe) # 添加树目录

        # 添加 参数 Tab
        paramsTab = QtWidgets.QTabBar(self.tab) # 生成参数标签
        self.tab.addTab(paramsTab, 'PARAMS')
        paramsTabLayout = QtWidgets.QVBoxLayout(paramsTab)
        paramsTabLayout.setSpacing(0)
        paramsTabLayout.setContentsMargins(0,0,0,0)
        # 参数TAB 添加搜索框
        searchLineFrame = QtWidgets.QFrame()
        searchLineFrame.setObjectName('blackWgt_noBorder')
        searchLineFrameLayout = QtWidgets.QHBoxLayout(searchLineFrame)
        exportParamsBtn = QtWidgets.QPushButton()
        exportParamsBtn.setFixedSize(180, 20)
        exportParamsBtn.setObjectName('blackPushButton')
        exportParamsBtn.setText('Export Parameters')
        exportParamsBtn.clicked.connect(self.exportParamsBtnClicked)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.searchLine = QtWidgets.QLineEdit()
        self.searchLine.setFixedWidth(200)
        self.searchLine.editingFinished.connect(self.searchParams)
        searchLineFrameLayout.addWidget(self.searchLine)
        searchLineFrameLayout.addWidget(exportParamsBtn)
        searchLineFrameLayout.addItem(spacerItem)
        paramsTabLayout.addWidget(searchLineFrame)

        # label 显示该LOG所用飞控版本等信息
        self.logTextLabel = QtWidgets.QLabel()
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setFixedHeight(50)
        scrollArea.setWidgetResizable(True)
        scrollArea.setObjectName('blackWgt_noBorder')
        scrollAreaWidgetContents = QtWidgets.QWidget()
        scrollAreaWidgetContents.setObjectName('blackWgt_noBorder')
        scrollArea.setWidget(scrollAreaWidgetContents)
        scrollAreaLayout = QtWidgets.QGridLayout(scrollAreaWidgetContents)
        scrollAreaLayout.addWidget(self.logTextLabel)
        paramsTabLayout.addWidget(scrollArea)

        # 添加wgt显示参数
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setObjectName('blackWgt_noBorder')
        scrollAreaWidgetContents = QtWidgets.QWidget()
        scrollAreaWidgetContents.setObjectName('blackWgt_noBorder')
        scrollArea.setWidget(scrollAreaWidgetContents)
        self.frameDetailLayout = QtWidgets.QGridLayout(scrollAreaWidgetContents)
        self.frameDetailLayout.setVerticalSpacing(0)
        self.frameDetailLayout.setHorizontalSpacing(50)
        self.frameDetailLayout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        paramsTabLayout.addWidget(scrollArea)
        
        frameLayout.addWidget(self.tab)
        self.layout.addWidget(frame)

        # * --------- end UI layout
        # 导出窗口
        self.exportWindow = exportWindow()

        # 解析log时的进度条窗口
        self.waitWindow = QtWidgets.QWidget()
        self.waitWindow.resize(240, 180)
        waitWindowLayout = QtWidgets.QVBoxLayout(self.waitWindow)
        waitWindowLayout.setContentsMargins(0,0,0,0)
        waitWindowFrame = QtWidgets.QFrame()
        waitWindowFrame.setObjectName('blackFrame')
        waitWindowFrameLayout = QtWidgets.QVBoxLayout(waitWindowFrame)
        waitWindowFrameLayout.setContentsMargins(10,80,10,80)
        label = QtWidgets.QLabel()
        label.setText('Please wait ... It need a little time to process data')
        label.setFixedHeight(30)
        waitWindowFrameLayout.addWidget(label)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        waitWindowFrameLayout.addWidget(self.progress)
        waitWindowLayout.addWidget(waitWindowFrame)
        self.waitWindow.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        # self.waitWindow.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.waitWindow.setWindowModality(QtCore.Qt.ApplicationModal)

        # log 解析线程
        self.log_thd = LogAnalysisThd()
        self.log_thd._update_treelist_singal.connect(self.addTreeList)
        self.log_thd.log_parser._progress_update_signal.connect(self.updateProgress)
        self.log_thd._closeWindow_singal.connect(self.closWindow)
        self.log_thd._updateParams_singal.connect(self.updateParams)

        self.paramsFrameDict = {}
        self.checkBoxCheckList = []
        self.fileName = ''

    def closWindow(self):
        self.waitWindow.close()
        self.progress.setValue(0)
        self.graph.p.setTitle(self.fileName)

    def updateProgress(self, value):
        self.progress.setValue(value)

    def searchParams(self):
        keywords = self.searchLine.text().upper()
        for key in self.paramsFrameDict:
            if keywords in key:
                self.paramsFrameDict[key].setHidden(False)
            else:
                self.paramsFrameDict[key].setHidden(True)

    def deleteAllPrams(self):
        for key in self.paramsFrameDict:
            self.paramsFrameDict[key].deleteLater()
        self.paramsFrameDict.clear()
        item_list = list(range(self.frameDetailLayout.count()))
        item_list.reverse()
        for i in item_list:
            item = self.frameDetailLayout.itemAt(i)
            self.frameDetailLayout.removeItem(item)
            if item.widget() :
                item.widget().deleteLater()

    def checkboxChanged(self, data_dict, name, key, checkbox):
        label = str(name) + ' -> ' + str(key)
        mark_mode = 0
        if name == 'ERR' and key == 'Err':
            mark_mode = 1
        elif name == 'MODE' and key == 'Mode':
            mark_mode = 2
        elif name == 'EV' and key == 'id':
            mark_mode = 3
        else:
            mark_mode = 0

        try:
            if checkbox.checkState():
                if mark_mode == 0:
                    self.graph.addLine(label, data_dict[timeStampLabel], data_dict[key])
                else:
                    self.graph.addMark(mark_mode, data_dict[timeStampLabel], data_dict[key])
                self.checkBoxCheckList.append(checkbox)
            else:
                if mark_mode == 0:
                    self.graph.removeLine(label)
                else:
                    self.graph.removeMark(mark_mode)
        except Exception as e:
            checkbox.setCheckState(False)
            print(f'Add Line Err: {e}')

    def caclFormula(self, name, label, pathLine):
        formula = pathLine.text()
        if formula is '':
            if label in self.log_thd.log_parser.msg_dict_backup[name]:
                self.log_thd.logData[name][label] = copy.deepcopy(self.log_thd.log_parser.msg_dict_backup[name][label])
        else:
            for i in range(len(self.log_thd.log_parser.msg_dict_backup[name][label])):
                data = self.log_thd.log_parser.msg_dict_backup[name][label][i]
                try:
                    formula_result = eval('data' + formula)
                    self.log_thd.logData[name][label][i] = formula_result
                except Exception as e:
                    print(f'Cacl Err: {e}')
                    break

    def clearCheckBtnClicked(self):
        for checkbox in self.checkBoxCheckList:
            checkbox.setCheckState(False)

    def exportBtnClicked(self):
        self.exportWindow.deleteAll()
        self.exportWindow.addCheckbox(self.log_thd.logData, self.fileName)
        self.exportWindow.show()

    def selectBtnClicked(self):
        logfile = QFileDialog.getOpenFileName(self,'Select the log file..','','(*.LOG , *.log, *.BIN, *.bin)')
        if logfile[0] is not '':
            self.fileName = logfile[0]
            self.treewgt.clear()
            self.graph.remove_all_line()
            self.deleteAllPrams()
            self.graph.p.setTitle('')

            self.waitWindow.show()
            self.log_thd.file = logfile[0]
            self.log_thd.flg = True
            self.log_thd.start()

    def exportParamsBtnClicked(self):
        path = QFileDialog.getExistingDirectory(self,'Select the path','/')
        if path == '':
            return
        if 'PARM' not in self.log_thd.log_parser.msg_dict_backup:
            return
        name = path + '/' + 'params' + '.md'
        paramsFile = open(name, 'wt', encoding='UTF-8')
        paramsFile.write('>' + self.logTextLabel.text())
        paramsFile.write('\n---\n')
        paramsFile.write('| NAME | VALUE |\n')
        paramsFile.write('| :---: | :--: |\n')
        for i in range(len(self.log_thd.log_parser.msg_dict_backup['PARM']['Name'])):
            name = self.log_thd.log_parser.msg_dict_backup['PARM']['Name'][i].decode()
            result = re.findall('(\w+)(\\x00*)', name)
            value = self.log_thd.log_parser.msg_dict_backup['PARM']['Value'][i]
            paramsFile.write(f'| {result[0][0]} | {round(value, 7)} |\n')

    def updateParams(self, name, value, idx):
        frame = QtWidgets.QFrame()
        frameLayout = QtWidgets.QHBoxLayout(frame)
        frameLayout.setSpacing(0)
        label = QtWidgets.QLabel()
        label.setText(name)
        label.setFixedSize(150, 20)
        pathLine = QtWidgets.QLineEdit()
        pathLine.setText(str(round(value, 7)))
        pathLine.setFixedSize(120,20)
        pathLine.setReadOnly(True)
        pathLine.setAlignment(QtCore.Qt.AlignHCenter)
        frameLayout.addWidget(label)
        frameLayout.addWidget(pathLine)
        pos = [idx / 3, idx % 3]
        self.frameDetailLayout.addWidget(frame, *pos)
        self.paramsFrameDict.setdefault(name, frame)

        if 'MSG' in self.log_thd.log_parser.msg_dict_backup:
            msg = ''
            for text in self.log_thd.log_parser.msg_dict_backup['MSG']['Message']:
                msg = msg + text.decode() + '\n'
            self.logTextLabel.setText(msg)

    def addTreeList(self, data_dict, tree_name):
        one_treelist = QtWidgets.QTreeWidgetItem(self.treewgt)
        one_treelist.setText(0, tree_name)

        for key in data_dict:
            frame = QtWidgets.QFrame()
            frameLayout = QtWidgets.QHBoxLayout(frame)
            frameLayout.setSpacing(0)
            frameLayout.setContentsMargins(0,0,0,0)
            checkbox = QtWidgets.QCheckBox()
            checkbox.setText(key)
            checkbox.setFixedWidth(125)
            frameLayout.addWidget(checkbox)
            checkbox.stateChanged.connect(partial(self.checkboxChanged, data_dict, tree_name, key, checkbox))
            # * cacl the log frquency
            if key == timeStampLabel and len(data_dict[timeStampLabel]) > 1:
                runningTime = (data_dict[timeStampLabel][-1] - data_dict[timeStampLabel][0])
                frq = 0
                if runningTime != 0:
                    frq = round(len(data_dict[timeStampLabel]) / runningTime, 0)
                label = QtWidgets.QLabel()
                frameLayout.addWidget(label)
                label.setText(str(frq) + ' Hz')
            else:
                pathline = QtWidgets.QLineEdit()
                frameLayout.addWidget(pathline)
                # pathline.setClearButtonEnabled(True)
                pathline.editingFinished.connect(partial(self.caclFormula, tree_name, key, pathline))
            self.treewgt.setItemWidget(QtWidgets.QTreeWidgetItem(one_treelist), 0, frame)


class LogAnalysisThd(QThread):
    _update_treelist_singal = pyqtSignal(dict, str)
    _closeWindow_singal = pyqtSignal()
    _updateParams_singal = pyqtSignal(str, float, int)
    def __init__(self):
        super(LogAnalysisThd, self).__init__()
        self.flg = False
        self.file = ''
        self.log_parser = log_parser()
        self.logData = {}

    def run(self):
        while True:
            time.sleep(0.1)
            if self.flg:
                self.logData = self.log_parser.analysis_log(self.file)
                self.updateTreeList()
                self.updateParams()
                self.flg = False
                self._closeWindow_singal.emit()

    def updateTreeList(self):
        # do not add list if the len of the data is 0
        for tree_name in self.logData:
            for label in self.logData[tree_name]:
                if len(self.logData[tree_name][label]) > 0:
                    self._update_treelist_singal.emit(self.logData[tree_name], tree_name)
                    break

    def updateParams(self):
        # update the key if 'PARM' changed in protocal
        if 'PARM' not in self.log_parser.msg_dict_backup:
            return
        for i in range(len(self.log_parser.msg_dict_backup['PARM']['Name'])):
            name = self.log_parser.msg_dict_backup['PARM']['Name'][i].decode()
            value = self.log_parser.msg_dict_backup['PARM']['Value'][i]
            self._updateParams_singal.emit(name, value, i)

# 导出log窗口
# class exportWindow(QtWidgets.QDialog):
class exportWindow(QtWidgets.QWidget):
    def __init__(self):
        super(exportWindow, self).__init__()
        self.setFixedSize(480, 320)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap('resource/icon_export.svg'), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
        self.setWindowIcon(icon)
        self.setWindowTitle('Export Setting')
        self.setObjectName('blackFrame')
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignBottom)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # * button
        expframeBtn = QtWidgets.QFrame()
        expbtnLayout = QtWidgets.QHBoxLayout(expframeBtn)

        self.exporttxtBtn = QtWidgets.QPushButton()
        self.exporttxtBtn.setObjectName('blackPushButton')
        self.exporttxtBtn.setText('Export .txt')
        self.exporttxtBtn.clicked.connect(self.exportTxtBtnClick)

        self.exportmatBtn = QtWidgets.QPushButton()
        self.exportmatBtn.setObjectName('blackPushButton')
        self.exportmatBtn.setText('Export .mat')
        self.exportmatBtn.clicked.connect(self.exportMatBtnClick)

        expbtnLayout.addWidget(self.exporttxtBtn)
        expbtnLayout.addWidget(self.exportmatBtn)
        expbtnLayout.setSpacing(5)

        # * scrollarea to add checkbox
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName('blackWgt_noBorder')
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setObjectName('blackWgt_noBorder')
        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.layout.addWidget(self.scrollArea)

        self.layout.addWidget(expframeBtn)

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.checkboxList = []
        self.logData = {}
        self.fileName = ''

    def addCheckbox(self, logData, fileName):
        self.fileName = fileName
        self.logData = logData
        if len(logData) is 0:
            return
        else:
            for key in logData:
                self.checkboxList.append(QtWidgets.QCheckBox())
                self.checkboxList[-1].setFixedSize(100, 15)
                self.checkboxList[-1].setText(key)
                self.gridLayout.addWidget(self.checkboxList[-1], (len(self.checkboxList)-1)/3, (len(self.checkboxList)-1)%3)

    def exportTxtBtnClick(self):
        self.path = QFileDialog.getExistingDirectory(self,'Select the path','/')
        if self.path == '':
            return
        if len(self.checkboxList) is 0:
            return
        for i in range(len(self.checkboxList)):
            if self.checkboxList[i].checkState():
                Name = self.path + '/' + self.checkboxList[i].text() + '_' + re.findall("\d+",self.fileName)[0] + '.txt'
                writeFile = open(Name, 'w', encoding='UTF-8')
                dateLen = len(self.logData[self.checkboxList[i].text()][timeStampLabel])
                for cnt in range(dateLen):
                    key_num = 0
                    for key in self.logData[self.checkboxList[i].text()]:
                        try:
                            writeFile.write('%-10s'%(str(self.logData[self.checkboxList[i].text()][key][cnt])))
                        except:
                            writeFile.write('0')
                        key_num = key_num + 1
                        if key_num < len(self.logData[self.checkboxList[i].text()]):
                            writeFile.write(',')
                    writeFile.write('\r\n')
                writeFile.close()
                self.close()

    def exportMatBtnClick(self):
        self.path = QFileDialog.getExistingDirectory(self,'Select the path','/')
        if self.path == '':
            return
        if len(self.checkboxList) == 0:
            return
        for i in range(len(self.checkboxList)):
            if self.checkboxList[i].checkState():
                Name = self.path + '/' + self.checkboxList[i].text() + '_' + re.findall("\d+",self.fileName)[0] + '.mat'

                scio.savemat(Name, self.logData[self.checkboxList[i].text()])
                
                self.close()
    
    def deleteAll(self):
        try:
            for i in range(len(self.checkboxList)):
                self.layout.removeWidget(self.checkboxList[i])
                self.checkboxList[i].deleteLater()
            self.checkboxList.clear()
        except:
            pass

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabLog()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())