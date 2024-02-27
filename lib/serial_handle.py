# -*- coding: utf-8 -*-
'''
# Created on Jan-10-20 17:50 
# serial_handle.py
# @author: 
'''

import serial
import serial.tools.list_ports
import threading
import time
import sys, os
sys.path.append(os.getcwd())
from lib.delegate import Delegate

class SerialHandle:
    """
    处理串口数据
    """
    def __init__(self):
        self.com = serial.Serial()
        self.tx = b''
        self.tx_buffer = b''
        self.thd_flg = False
        self.thd = None

        # 代理逻辑
        Delegate.add_listener('ON_COM_TX', self.push_tx_rawdata)
        Delegate.add_listener('ON_COM_BIN_TX', self.force_write)

    def open(self, name, rate):
        print('try open')
        self.com.port = name
        self.com.baudrate = rate
        try:
            self.com.open()
        except Exception as e:
            print(e)
            # print('open port fail')
            return False
        else:
            print('open success')
            self.thd_flg = True  # 标志进程Enable
            self.start_com_thread()
            return True

    def close(self):
        print('try close')
        self.thd_flg = False
        time.sleep(0.1)  # 等待线程一个循环过去，防止出错
        self.com.close()
        print('close com')

    def print_data_hex(self, data):
        if(len(data) <= 0):
            return
        data_str = ''
        if isinstance(data[0], int):
            for x in data:
                data_str += '0x%02X,' % x
        elif isinstance(data[0], str):
            for y in data:
                x = ord(y)
                data_str += '0x%02X,' % x
        elif isinstance(data[0], bytes):
            for x in data:
                data_str += '0x%02X,' % x
        # print('hex:' + data_str)


    def push_tx_rawdata(self, barry):
        if self.com.isOpen():
            self.tx += barry
        else:
            print('串口未打开')
            Delegate.broadcast('CONSOLE_WRITE', '串口未打开')

    def force_write(self, barry):
        if self.com.isOpen():
            self.com.write(barry)

    def transfer_thread(self):
        while True:
            try:
                if self.thd_flg and self.com.isOpen():
                    n = self.com.inWaiting()
                    if n > 0:
                        data = self.com.read(n)
                        # print(data)
                        if data:
                            Delegate.call('ON_COM_RX', data)
                        else:
                            print('no data?')
                    # send data
                    if len(self.tx) > 0:
                        print('tx:')
                        self.print_data_hex(self.tx)
                        self.tx_buffer = self.tx
                        self.com.write(self.tx_buffer)
                        self.tx = b''

                    # time.sleep(0.005)
                else:
                    # print('not open set')
                    time.sleep(1)
            except Exception as e:
                self.close()
                print(e)

    def start_com_thread(self):
        if (self.thd):
            return
        thread = threading.Thread(target=self.transfer_thread)
        thread.setDaemon(True)
        thread.start()
        self.thd = thread

    def get_port_names(self):
        pts = serial.tools.list_ports.comports()
        self.ports = []
        for p in pts:
            self.ports.append(p[0])
        return self.ports


def _quit(root):
    print("quit app")
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent


if __name__ == '__main__':
    import tkinter as tk
    from tkinter import ttk
    print('module test')

    sh = SerialHandle()
    ports = sh.get_port_names()
    print(ports)
    # sh.open(ports[2], 115200)

    sh.start_com_thread()

    root = tk.Tk()
    btn_open = ttk.Button(
        root,
        text='打开串口',
        command=lambda: sh.open(ports[0], 115200))
    btn_open.pack()
    btn_close = ttk.Button(
        root,
        text='关闭串口',
        command=sh.close)
    btn_close.pack()
    root.protocol("WM_DELETE_WINDOW", lambda: _quit(root))
    root.mainloop()
