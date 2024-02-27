# -*- coding: utf-8 -*-
'''
# Created on Jan-15-20 14:20
# mavlink_handle.py
# @author: 
'''

import sys, os, time
import threading
import serial
from multiprocessing import Process, Queue, Value, Array

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
sys.path.append(os.getcwd())

from lib import H7 as custom_protocal
target_system       = 1
target_component    = 1


# ! Python 的线程受限于GIL，并不是真正的并行，所以采用进程处理串口。共享内存和Queue进行数据交换
# TODO：主进程非正常退出时，子进程会变成僵尸进程无法退出
class serialProcess(Process):
    def __init__(self, alive, rcv_queue, send_queue, open_or_close_flg, com, baud, Bps):
        super(serialProcess, self).__init__()
        self.daemon = True

        self.com = com
        self.baud = baud
        self.alive = alive
        self.rcv_queue = rcv_queue
        self.send_queue = send_queue
        self.open_or_close_flg = open_or_close_flg
        self.Bps = Bps
        self.port = serial.Serial(timeout=0, writeTimeout=0)
        self.rcv_flg = False

        self.rcv_conut = 0
        self.last_rcv_time = 0

    def run(self):
        while self.alive.value:
            # try open
            if self.open_or_close_flg.value == b'OPEN':
                if self.open():
                    self.open_or_close_flg.value = b'OPENED'
                else:
                    self.open_or_close_flg.value = b'NONE'
            # try close
            if self.open_or_close_flg.value == b'CLOSE':
                if self.close():
                    self.open_or_close_flg.value = b'CLOSED'
                else:
                    self.open_or_close_flg.value = b'NONE'

            if not self.send_queue.empty():
                self.write(self.send_queue.get())

            if self.rcv_flg:
                self.recv()
                time.sleep(0.0005)
            else:
                time.sleep(0.1)

    def open(self):
        try:
            self.port.port = bytes.decode(self.com.value)
            self.port.open()
            self.port.baudrate = self.baud.value
        except Exception as e:
            print(e)
            return False
        else:
            self.rcv_flg = True
            print(f'{bytes.decode(self.com.value)} Open  Success')
            return True

    def close(self):
        try:
            self.rcv_flg = False
            self.port.close()
            self.open_or_close_flg.value = b'CLOSED'
            print(f'{bytes.decode(self.com.value)} Close Success')
        except Exception as e:
            print(e)

    def recv(self):
        try:
            waiting = self.port.inWaiting()
            ret = self.port.read(waiting)
            self.cal_bps(waiting)
            self.rcv_queue.put_nowait(ret)
        except Exception as e:
            print(e)
            self.close()

    def write(self, buf):
        try:
            return self.port.write(bytes(buf))
        except Exception:
            return -1

    def cal_bps(self, count):
        self.rcv_conut += count
        if time.time() - self.last_rcv_time > 1:
            self.Bps.value = self.rcv_conut
            self.rcv_conut = 0
            self.last_rcv_time = time.time()


class MavLinkHandle(QtCore.QObject):
    _msg_singal = QtCore.pyqtSignal(object)
    def __init__(self):
        super(MavLinkHandle, self).__init__()
        # 共享内存
        self.open_or_close_flg = Array('c', b'NONE  ')
        self.com = Array('c', b'NONE  ')
        self.alive = Value('b', True)
        self.Bps = Value('f', 0)
        self.baud = Value('i', 57600)
        # 数据队列
        self.rcv_queue = Queue()
        self.send_queue = Queue()
        self.serialProcess = serialProcess(self.alive, self.rcv_queue, self.send_queue, self.open_or_close_flg, self.com, self.baud, self.Bps)

        self.mav = custom_protocal.MAVLink(self, srcSystem=255, srcComponent=0, use_native=False)

        thread = threading.Thread(target=self.rcv_thread)
        thread.setDaemon(True)
        self.thd_flg = False
        thread.start()

    def start(self):
        self.serialProcess.start()

    def exit(self):
        self.alive.value = False
        Mav_Handle.serialProcess.join()
        try:
            Mav_Handle.serialProcess.terminate()
        except Exception as e:
            print(e)

    def open(self, com, baud):
        self.baud.value = baud
        self.com.value = str.encode(com)
        self.open_or_close_flg.value = b'OPEN'
        self.thd_flg = True

    def close(self):
        self.open_or_close_flg.value = b'CLOSE'
        self.thd_flg = False

    def is_open(self):
        if self.open_or_close_flg.value == b'OPENED':
            return True
        else:
            return False

    def rcv_thread(self):
        while True:
            if self.thd_flg:
                if self.rcv_queue.empty():
                    time.sleep(0.01)
                    continue
                s = self.rcv_queue.get()
                try:
                    msg = self.mav.parse_char(s)
                    if msg != None:
                        self._msg_singal.emit(msg)
                except Exception as e:
                    print(e)
            else:
                time.sleep(0.1)

    def write(self, buf):
        self.send_queue.put(buf)

    def param_request_list(self):
        try:
            self.mav.param_request_list_send(target_system, target_component)
        except:
            pass

    def set_param(self, name, value):
        try:
            self.mav.param_set_send(target_system, target_component,\
                bytes(name,'utf-8'), value, custom_protocal.MAVLINK_TYPE_FLOAT)
        except Exception as e:
            pass

    def load_param(self, name):
        try:
            self.mav.param_request_read_send(target_system, target_component,\
                bytes(name,'utf-8'), -1, custom_protocal.MAVLINK_TYPE_FLOAT)
        except Exception as e:
            pass

    def send_text(self, text):
        try:
            device = 10
            flags = custom_protocal.SERIAL_CONTROL_FLAG_EXCLUSIVE \
                | custom_protocal.SERIAL_CONTROL_FLAG_RESPOND \
                | custom_protocal.SERIAL_CONTROL_FLAG_MULTI
            timeout = 0
            baudrate = 0
            count = len(text)
            buf = [ord(x) for x in text[:count]]
            buf.extend([0]*(70-len(buf)))
            self.mav.serial_control_send(device, flags, 0, 0, count, buf)
        except Exception as e:
            print(e)

    def send_heartbeat(self):
        try:
            self.mav.heartbeat_send(6, 0, 81, 7, 0, 2)
        except:
            pass

    def acc_calibration_start(self):
        try:
            self.mav.command_long_send(target_system, target_component, custom_protocal.MAV_CMD_PREFLIGHT_CALIBRATION, 0, \
                0, 0, 0, 0, 0, 0, 0)
        except:
            pass

    def compass_calibration_start(self):
        try:
            self.mav.command_long_send(target_system, target_component, custom_protocal.MAV_CMD_PREFLIGHT_CALIBRATION, 0, \
                2, 0, 0, 0, 0, 0, 0)
        except:
            pass



Mav_Handle = MavLinkHandle()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    sys.exit(app.exec_())
