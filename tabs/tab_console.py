# -*- coding: utf-8 -*-
'''
# Created on Jan-02-20 08:59 
# tab_console.py
# @author: 
'''

import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

sys.path.append(os.getcwd())
from lib.mavlink_handle import Mav_Handle

# @msgs: 
# @function: mavlink console
class tabConsole(QtWidgets.QTabBar):
    def __init__(self, *agrs, **kwargs):
        super(tabConsole, self).__init__(*agrs, **kwargs)
        self.tabNameStr = 'Console'
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(50,50,10,10)
        self.icon = 'resource/icon_console_64.svg'

        self.ConsoleWgt = QtWidgets.QPlainTextEdit()
        self.layout.addWidget(self.ConsoleWgt)
        self.ConsoleWgt.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.ConsoleWgt.setObjectName('ConsoleWgt')
        # self.showMessage(' Hello, This is a MavLink Console, You can use some commands to communicate with copter through mavlink.\n')
        # self.showMessage(' Please connect the mavlink')

        self.ConsoleWgt.setReadOnly(True)

        Mav_Handle._msg_singal.connect(self.updateMsg)

        self.inputWgt = QtWidgets.QLineEdit()
        self.inputWgt.setFixedHeight(20)
        self.inputWgt.setClearButtonEnabled(True)
        self.inputWgt.editingFinished.connect(self.sendMsg)
        self.layout.addWidget(self.inputWgt)

    def showMessage(self, msg):
        # deal the appendPlaintext add one more '\n'
        self.ConsoleWgt.moveCursor(QtGui.QTextCursor.End)
        # get a cursor
        precursor = self.ConsoleWgt.textCursor()
        # record last pos
        pos = precursor.position()
        # append txt
        self.ConsoleWgt.appendPlainText(msg)
        if pos == 0:
            return
        # cursor jump to last position
        precursor.setPosition(pos)
        self.ConsoleWgt.setTextCursor(precursor)
        # delet '\n'
        self.ConsoleWgt.textCursor().deleteChar()

    def updateMsg(self, msg):
        if msg.get_type() == 'STATUSTEXT':
            self.showMessage('\n')
            self.showMessage(f'STATUSTEXT: {msg.text}')

        if msg.get_type() == 'SERIAL_CONTROL':
            data = msg.data[:msg.count]
            buf = ''
            for i in data:
                buf += str(chr(i))

            # 部分乱码去掉
            if ' \x1b[K' in buf:
                buf = buf.replace(' \x1b[K', ' ')

            self.showMessage(buf)

    def sendMsg(self, msg = None):
        if msg == None:
            msg = self.inputWgt.text()
            self.inputWgt.clear()
        if msg == '':
            Mav_Handle.send_text('\n')
        else:
            Mav_Handle.send_text(msg + '\n')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open(os.getcwd() + "/dark_style.css").read())

    from view_main import view_main
    view = view_main()

    tab = tabConsole()

    view.addTab(tab, tab.tabNameStr)
    view.addNavigationItem(tab.tabNameStr, tab.icon)

    view.show()

    Mav_Handle.start()

    sys.exit(app.exec_())





   