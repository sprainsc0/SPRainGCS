# -*- coding: utf-8 -*-
'''
# Created on Jan-01-20 18:43 
# tab_params.py
# @author: 
'''
import sys, os, time, re
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from functools import partial
from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtGui import QIntValidator
import struct
from ctypes import *

sys.path.append(os.getcwd())
from lib.mavlink_handle import Mav_Handle

class param_value(Union):
    _fields_=[
       ("int",c_int),
       ("float",c_float),
       ("array",c_char * 4), ]
# @msgs: parameters
# @function: all of the parameters in copter, load and save
class tabParameters(QtWidgets.QTabBar):
    def __init__(self, *args, **kwargs):
        super(tabParameters, self).__init__(*args, **kwargs)
        self.tabNameStr = 'Parameters'
        self.icon = 'resource/icon_params_64.svg'

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 15, 0, 0,)
        self.layout.setSpacing(5)

        searchFrame = QtWidgets.QFrame()
        searchFrameLayout = QtWidgets.QHBoxLayout(searchFrame)
        searchFrameLayout.setContentsMargins(80,0,0,0)
        self.searchLine = QtWidgets.QLineEdit()
        self.searchLine.setFixedWidth(200)
        self.searchLine.editingFinished.connect(self.searchParams)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        searchFrameLayout.addWidget(self.searchLine)
        searchFrameLayout.addItem(spacerItem)
        self.layout.addWidget(searchFrame)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setObjectName('blackWgt_noBorder')
        scrollAreaWidgetContents = QtWidgets.QWidget()
        scrollAreaWidgetContents.setObjectName('blackWgt_noBorder')
        scrollArea.setWidget(scrollAreaWidgetContents)
        self.gridLayout = QtWidgets.QGridLayout(scrollAreaWidgetContents)
        # 器件之间横向间距
        self.gridLayout.setVerticalSpacing(0)
        self.layout.addWidget(scrollArea)

        # 保存frame，重新拉取时删除
        self.params_frame_dict = {}
        # 保存参数输入框，全部保存时读取输入数值
        self.params_wgt_dict = {}

        frame = QtWidgets.QFrame()
        frameLayout = QtWidgets.QHBoxLayout(frame)
        self.loadAllBtn = QtWidgets.QPushButton()
        self.loadAllBtn.setText('Load All ...')
        self.loadAllBtn.setFixedSize(150, 20)
        self.loadAllBtn.setObjectName('blackPushButton')
        self.loadAllBtn.clicked.connect(self.loadAllBtnClick)

        self.targetcomponent = QtWidgets.QLineEdit()
        self.targetcomponent.setFixedWidth(60)
        self.targetcomponent.setPlaceholderText('CAN设备ID')
        intValidator = QIntValidator(self)
        intValidator.setRange(0,127)

        self.targetcomponent.setValidator(intValidator)

        self.saveAllBtn = QtWidgets.QPushButton()
        self.saveAllBtn.setText('Save All ...')
        self.saveAllBtn.setFixedSize(150, 20)
        self.saveAllBtn.setObjectName('blackPushButton')
        self.saveAllBtn.clicked.connect(self.saveAllBtnClick)
        exportBtn = QtWidgets.QPushButton()
        exportBtn.setText('Export')
        exportBtn.setFixedSize(150, 20)
        exportBtn.setObjectName('blackPushButton')
        exportBtn.clicked.connect(self.exportBtnClicked)
        importBtn = QtWidgets.QPushButton()
        importBtn.setText('Import')
        importBtn.setFixedSize(150, 20)
        importBtn.setObjectName('blackPushButton')
        importBtn.clicked.connect(self.importBtnClicked)
        frameLayout.addWidget(self.loadAllBtn)
        frameLayout.addWidget(self.targetcomponent)
        frameLayout.addWidget(self.saveAllBtn)
        frameLayout.addWidget(exportBtn)
        frameLayout.addWidget(importBtn)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        frameLayout.addItem(spacerItem)
        self.layout.addWidget(frame)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setFixedHeight(1)
        self.progress.setTextVisible(False)
        self.layout.addWidget(self.progress)

        Mav_Handle._msg_singal.connect(self.updateMsg)

        self.saveparams_thd = saveparams_thread()
        self.saveparams_thd._count_singal.connect(self.setProgressValue)
        self.saveparams_thd.start()

        self.last_msg_param_index = 0

    def setProgressValue(self, value):
        self.progress.setValue((value/520)*100)

    # 添加一组参数控件，包含参数名，数值输入框，拉取和保存按钮
    def addGroup(self, name, fvalue, position):
        """
        add a group wgt of parameter
        Args:
            name: name of the parameter name
            fvalue: value of the parameter
            position: position of the frame wgt in gridLayout
        """
        frame = QtWidgets.QFrame()
        frame.setFixedWidth(500)
        frameLayout = QtWidgets.QHBoxLayout(frame)
        frameLayout.setSpacing(0)
        label = QtWidgets.QLabel()
        label.setText(f'[{position}] {name}')
        label.setObjectName('nameLabel')
        label.setFixedSize(200, 25)

        spinbox = QtWidgets.QLineEdit()
        spinbox.setObjectName('paramLineEdit')
        # revalue = fvalue
        # if ftype == 6:
        #     bs = struct.pack("f",fvalue)
        #     data_temp = struct.unpack('<i', struct.pack('4b', *bs))[0]
        #     revalue = float(data_temp)

        spinbox.setValidator(QtGui.QDoubleValidator(-99999, 99999, 7))
        spinbox.setText(str(round(fvalue, 7)))

        spinbox.setFixedSize(150, 25)
        spinbox.setAlignment(QtCore.Qt.AlignCenter)
        spinbox.textChanged.connect(partial(self.spinboxChanged, name, spinbox))

        loadbtn = QtWidgets.QPushButton()
        loadbtn.setFixedSize(50, 25)
        loadbtn.setText('Load')
        loadbtn.setObjectName('blackPushButton')
        loadbtn.clicked.connect(partial(self.loadbtnClick, name, position))
        
        savebtn = QtWidgets.QPushButton()
        savebtn.setText('Save')
        savebtn.setObjectName('blackPushButton')
        savebtn.setFixedSize(50, 25)
        savebtn.clicked.connect(partial(self.savebtnClick, name, spinbox))

        frameLayout.addWidget(label)
        frameLayout.addWidget(spinbox)
        frameLayout.addWidget(loadbtn)
        frameLayout.addWidget(savebtn)
        self.params_frame_dict.setdefault(name, frame)
        self.params_wgt_dict.setdefault(name, spinbox)
        pos = [position / 2, position % 2]
        self.gridLayout.addWidget(frame, *pos)

    def savebtnClick(self, name, input_line):
        value = float(input_line.text())
        component = self.targetcomponent.text()
        component_id = 1
        if len(component) != 0:
            component_id = int(component)
        Mav_Handle.set_param(name, value, component_id)

    def loadbtnClick(self, name, index):
        component = self.targetcomponent.text()
        component_id = 1
        if len(component) != 0:
            component_id = int(component)
        Mav_Handle.load_param(name, index, component_id)

    def spinboxChanged(self, name, spinbox):
        spinbox.setStyleSheet('border-color: hotpink;color:hotpink;')

    # 清除， 重新拉取时操作
    def deleteAll(self):
        for key in self.params_frame_dict:
            self.params_frame_dict[key].deleteLater()
        self.params_frame_dict.clear()
        self.params_wgt_dict.clear()

    def loadAllBtnClick(self):
        self.deleteAll()
        self.progress.setValue(0)
        component = self.targetcomponent.text()
        component_id = 1
        if len(component) != 0:
            component_id = int(component)

        Mav_Handle.param_request_list(component_id)

    def saveAllBtnClick(self):
        """
        save all the parameters in saveparams_thread
        """
        for key in self.params_wgt_dict:
            self.saveparams_thd.params_dict.setdefault(key, self.params_wgt_dict[key].text())
        self.saveparams_thd.flg = True

    def updateMsg(self, msg):
        """
        singal of rcv msg. 'param_index' is 65535 when the msg is a reply of save cmd.
        """
        if msg.get_type() == 'PARAM_VALUE':
            # if msg.param_id in self.params_wgt_dict and msg.param_index == 65535:
            if msg.param_id in self.params_wgt_dict:
                print(f'get param: {msg.param_id}, value: {round(msg.param_value, 7)}')
                self.params_wgt_dict[msg.param_id].setText(f'{str(round(msg.param_value, 7))}')
                if self.saveparams_thd.flg == False:
                    return
                if msg.param_id == self.saveparams_thd.save_param_id:
                    # 保存下一个参数
                    self.saveparams_thd.save_next_flg = True
                else:
                    print(f'save param err, save {self.saveparams_thd.save_param_id}, get {msg.param_id}')
                return

            # '_hash_check' in f7 
            if msg.param_index == 65535:
                return

            revalue = msg.param_value
            if msg.param_type == 6:
                bs = struct.pack("f",msg.param_value)
                data_temp = struct.unpack('<i', struct.pack('4b', *bs))[0]
                revalue = float(data_temp)

            self.addGroup(msg.param_id, revalue, msg.param_index)

            # lost params
            if msg.param_index - self.last_msg_param_index > 1:
                for i in range(1,msg.param_index - self.last_msg_param_index):
                    print(f'lost param: {self.last_msg_param_index + i}')
            self.last_msg_param_index = msg.param_index

            if msg.param_index <= msg.param_count:
                self.progress.setValue((msg.param_index / msg.param_count) * 100)
    
            if msg.param_index == msg.param_count - 1:
                print(f"pull count: {len(self.params_wgt_dict)}  param_count:{msg.param_count}")
                self.progress.setValue(0)
                self.last_msg_param_index = 0

    def searchParams(self):
        keywords = self.searchLine.text().upper()
        for key in self.params_frame_dict:
            if keywords in key:
                self.params_frame_dict[key].setHidden(False)
            else:
                self.params_frame_dict[key].setHidden(True)

    def exportBtnClicked(self):
        """
        save all the params in PARAMS.md
        """
        path = QtWidgets.QFileDialog.getExistingDirectory(self,'Select the path','/')
        if path == '':
            return
        if len(self.params_wgt_dict) == 0:
            return
        name = path + '/' + 'PARAMS' + '.md'
        paramsFile = open(name, 'wt', encoding='UTF-8')
        paramsFile.write('> Attention: copter firmware version should be consistent!')
        # paramsFile.write('\n---\n')
        paramsFile.write('\n\n')
        paramsFile.write('| NAME | VALUE |\n')
        paramsFile.write('| :---: | :--: |\n')
        for key in self.params_wgt_dict:
            name = key
            value = float(self.params_wgt_dict[key].text())
            paramsFile.write(f'| {name} | {value} |\n')

    def importBtnClicked(self):
        """
        import params from a markdown file
        """
        path = QFileDialog.getOpenFileName(self,'Select the params file..','','(*.md)')
        if path[0] == '':
            return
        self.deleteAll()
        file = open(path[0], 'r')
        content = file.read()
        result = re.findall('\|\s+(\w+)\s+\|\s+(\-?\d+e?\-?\.?\d+)\s+\|', content)
        for i in range(len(result)):
            name  = result[i][0]
            value = float(result[i][1])
            self.addGroup(name, value, i)
        print(f'params_count: {len(result)}')

class saveparams_thread(QThread):
    """
    Save all the params.Save next only when a reply is received.
    set the save_next_flg True when rcv the reply.
    """
    _count_singal = pyqtSignal(int)
    def __init__(self):
        super(saveparams_thread, self).__init__()
        self.flg = False
        self.params_dict    = {}
        self.save_count     = 0
        self.save_next_flg  = False
        self.save_param_id  = ''

    def run(self):
        while(True):
            time.sleep(0.05)
            if self.flg:
                for key in self.params_dict:
                    if 'CAL_GYRO' in key or 'CAL_ACC' in key or 'CAL_MAG' in key:
                        print(f'save params except: {key}')
                        continue
                    self.save_param_id = key
                    self.save_next_flg = False
                    _time = time.time()
                    Mav_Handle.set_param(key, float(self.params_dict[key]), 1)
                    while self.save_next_flg is False:
                        time.sleep(0.01)
                        if time.time() - _time > 3:
                            print('save all params fail:time out')
                            break
                    time.sleep(0.01)
                    self._count_singal.emit(self.save_count)
                    self.save_count = self.save_count + 1
                print('SAVE ALL PARAMS FINISH!!!')
                self.flg = False
                self.save_count = 0
                self._count_singal.emit(self.save_count)
                self.params_dict.clear()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabParameters()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())


