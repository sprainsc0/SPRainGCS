# -*- coding: utf-8 -*-
'''
# Created on Jan-15-20 14:20
# mavlink_handle.py
# @author: 
'''

import sys, os, time
import threading
import serial
import socket
from multiprocessing import Process, Queue, Value, Array

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
sys.path.append(os.getcwd())

from lib import H7 as custom_protocal
target_system       = 1
target_component    = 1


# ! Python 的线程受限于GIL，并不是真正的并行
class serialThread(QtCore.QThread):
    _rcv_msg_singal = pyqtSignal()
    def __init__(self, rcv_queue, send_queue):
        super(serialThread, self).__init__()
        self.daemon = True

        self.com = 0
        self.baud = 0
        self.Bps = 0
        self.alive = True
        self.rcv_queue = rcv_queue
        self.send_queue = send_queue
        self.open_or_close_flg = 'NONE'
        
        self.port = serial.Serial(timeout=0, writeTimeout=0)
        self.rcv_flg = False

        self.rcv_conut = 0
        self.last_rcv_time = 0

    def run(self):
        while self.alive:
            # # try open
            # if self.open_or_close_flg == 'OPEN':
            #     self.open()
            # # try close
            # if self.open_or_close_flg == 'CLOSE':
            #     self.close()

            if not self.send_queue.empty() and self.rcv_flg:
                self.write(self.send_queue.get())

            if self.rcv_flg:
                self.recv()
                time.sleep(0.005)
            else:
                time.sleep(0.1)

    def open(self):
        try:
            self.port.port = self.com
            self.port.open()
            self.port.baudrate = self.baud
            self.alive = True
        except Exception as e:
            print(e)
            self.open_or_close_flg = 'ERR'
            return False
        else:
            self.rcv_flg = True
            self.open_or_close_flg = 'OPENED'
            print(f'{self.com} Open  Success')
            return True

    def close(self):
        try:
            self.rcv_flg = False
            self.port.close()
            self.open_or_close_flg = 'CLOSED'
            print(f'{self.com} Close Success')
        except Exception as e:
            self.open_or_close_flg = 'ERR'
            print(e)

    def recv(self):
        try:
            waiting = self.port.inWaiting()
            ret = self.port.read(waiting)
            self.cal_bps(waiting)
            self.rcv_queue.put_nowait(ret)
            self._rcv_msg_singal.emit()
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
            self.Bps = self.rcv_conut
            self.rcv_conut = 0
            self.last_rcv_time = time.time()

class udpThread(QtCore.QThread):
    _rcv_msg_singal = pyqtSignal()
    def __init__(self, rcv_queue, send_queue):
        super(udpThread, self).__init__()
        self.daemon = True

        self.address = '127.0.0.1'
        self.port = 14445
        self.Bps = 0
        self.alive = True
        self.rcv_queue = rcv_queue
        self.send_queue = send_queue
        self.open_or_close_flg = 'NONE'
        
        self.rcv_flg = False

        self.rcv_conut = 0
        self.last_rcv_time = 0

        self.client_add = ('127.0.0.1', 14550)

    def run(self):
        while self.alive:
            # # try open
            # if self.open_or_close_flg == 'OPEN':
            #     self.open()
            # # try close
            # if self.open_or_close_flg == 'CLOSE':
            #     self.close()

            if not self.send_queue.empty() and self.rcv_flg:
                self.write(self.send_queue.get())

            if self.rcv_flg:
                self.recv()
                time.sleep(0.005)
            else:
                time.sleep(0.1)

    def open(self):
        try:
            self.socket_fd = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            local_addr = (self.address, self.port)
            self.socket_fd.bind(local_addr)
            self.socket_fd.setblocking(0)
            self.alive = True
        except Exception as e:
            print(e)
            self.open_or_close_flg = 'ERR'
            return False
        else:
            self.rcv_flg = True
            self.open_or_close_flg = 'OPENED'
            print(f'udp Open Success')
            return True

    def close(self):
        try:
            self.rcv_flg = False
            self.socket_fd.close()
            self.open_or_close_flg = 'CLOSED'
            print(f'udp Close Success')
        except Exception as e:
            self.open_or_close_flg = 'ERR'
            print(e)

    def recv(self):
        try:
            data,addr=self.socket_fd.recvfrom(2048)
            self.client_add = addr
            self.cal_bps(len(bytes(data)))
            self.rcv_queue.put_nowait(bytes(data))
            self._rcv_msg_singal.emit()
        except Exception:
            return

    def write(self, buf):
        try:
            return self.self.socket_fd.sendto(bytes(buf), self.client_add)
        except Exception:
            return -1

    def cal_bps(self, count):
        self.rcv_conut += count
        if time.time() - self.last_rcv_time > 1:
            self.Bps = self.rcv_conut
            self.rcv_conut = 0
            self.last_rcv_time = time.time()


class MavLinkHandle(QtCore.QObject):
    _msg_singal = QtCore.pyqtSignal(object)
    def __init__(self):
        super(MavLinkHandle, self).__init__()

        # 数据队列
        self.rcv_queue = Queue()
        self.send_queue = Queue()

        self.serialThread = serialThread(self.rcv_queue, self.send_queue)
        self.udpThread = udpThread(self.rcv_queue, self.send_queue)

        self.mav = custom_protocal.MAVLink(self, srcSystem=255, srcComponent=0, use_native=False)
        
        self.port_type = 'serial'

        self.serialThread._rcv_msg_singal.connect(self.rcv_thread)
        self.udpThread._rcv_msg_singal.connect(self.rcv_thread)

    def start(self):
        print('Started')

    def exit(self):
        self.serialThread.alive = False
        self.udpThread.alive = False

    def open(self, port_type, com, baud):
        self.port_type = port_type
        if port_type == 'serial' :
            self.serialThread.baud = baud
            self.serialThread.com = com
            self.Bps = self.serialThread.Bps
            self.serialThread.open()
            self.serialThread.start()
        else :
            self.udpThread.address = com
            self.udpThread.port = baud
            self.Bps = self.udpThread.Bps
            self.udpThread.open()
            self.udpThread.start()
        pass

    def close(self):
        if self.port_type == 'serial' :
            self.serialThread.alive = False
            self.serialThread.close()
        else :
            self.udpThread.alive = False
            self.udpThread.close()

    def is_open(self):
        if self.serialThread.open_or_close_flg == 'OPENED' or self.udpThread.open_or_close_flg == 'OPENED':
            return True
        else:
            return False

    def rcv_thread(self):
        while not self.rcv_queue.empty():
            s = self.rcv_queue.get()
            try:
                msg = self.mav.parse_char(s)
                if msg != None:
                    self._msg_singal.emit(msg)
            except Exception as e:
                print(e)

    def write(self, buf):
        self.send_queue.put(buf)

    def param_request_list(self, component):
        try:
            self.mav.param_request_list_send(target_system, component)
        except:
            pass

    def set_param(self, name, value, component):
        try:
            self.mav.param_set_send(target_system, component,\
                bytes(name,'utf-8'), value, custom_protocal.MAVLINK_TYPE_FLOAT)
        except Exception as e:
            pass

    def load_param(self, name, index, component):
        try:
            self.mav.param_request_read_send(target_system, component,\
                bytes(name,'utf-8'), index, custom_protocal.MAVLINK_TYPE_FLOAT)
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

    socket_fd = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    local_addr = ('', 14555)
    socket_fd.bind(local_addr)

    socket_fd.setblocking(0)

    while 1 :
        try:
            data,addr=socket_fd.recvfrom(2048)
            print(addr)
            print(data)

            socket_fd.sendto(bytes(data), addr)

            time.sleep(0.005)
        except Exception as e:
            time.sleep(0.005)

    socket_fd.close()

    sys.exit(app.exec_())
