#!/usr/bin/env python

#
# Serial firmware uploader for the PX4FMU bootloader
#
# The PX4 firmware file is a JSON-encoded Python object, containing
# metadata fields and a zlib-compressed base64-encoded firmware image.
#
# The uploader uses the following fields from the firmware file:
#

# for python2.7 compatibility
from __future__ import print_function

import sys
import argparse
import binascii
import serial
import socket
import struct
import json
import zlib
import base64
import time
import array
import os
import struct
import serial.tools.list_ports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

from sys import platform as _platform

# Detect python version
if sys.version_info[0] < 3:
    runningPython3 = False
else:
    runningPython3 = True


class firmware(object):
    '''Loads a firmware file'''

    image = bytes()
    crctab = array.array('I', [
        0x00000000, 0x77073096, 0xee0e612c, 0x990951ba, 0x076dc419, 0x706af48f, 0xe963a535, 0x9e6495a3,
        0x0edb8832, 0x79dcb8a4, 0xe0d5e91e, 0x97d2d988, 0x09b64c2b, 0x7eb17cbd, 0xe7b82d07, 0x90bf1d91,
        0x1db71064, 0x6ab020f2, 0xf3b97148, 0x84be41de, 0x1adad47d, 0x6ddde4eb, 0xf4d4b551, 0x83d385c7,
        0x136c9856, 0x646ba8c0, 0xfd62f97a, 0x8a65c9ec, 0x14015c4f, 0x63066cd9, 0xfa0f3d63, 0x8d080df5,
        0x3b6e20c8, 0x4c69105e, 0xd56041e4, 0xa2677172, 0x3c03e4d1, 0x4b04d447, 0xd20d85fd, 0xa50ab56b,
        0x35b5a8fa, 0x42b2986c, 0xdbbbc9d6, 0xacbcf940, 0x32d86ce3, 0x45df5c75, 0xdcd60dcf, 0xabd13d59,
        0x26d930ac, 0x51de003a, 0xc8d75180, 0xbfd06116, 0x21b4f4b5, 0x56b3c423, 0xcfba9599, 0xb8bda50f,
        0x2802b89e, 0x5f058808, 0xc60cd9b2, 0xb10be924, 0x2f6f7c87, 0x58684c11, 0xc1611dab, 0xb6662d3d,
        0x76dc4190, 0x01db7106, 0x98d220bc, 0xefd5102a, 0x71b18589, 0x06b6b51f, 0x9fbfe4a5, 0xe8b8d433,
        0x7807c9a2, 0x0f00f934, 0x9609a88e, 0xe10e9818, 0x7f6a0dbb, 0x086d3d2d, 0x91646c97, 0xe6635c01,
        0x6b6b51f4, 0x1c6c6162, 0x856530d8, 0xf262004e, 0x6c0695ed, 0x1b01a57b, 0x8208f4c1, 0xf50fc457,
        0x65b0d9c6, 0x12b7e950, 0x8bbeb8ea, 0xfcb9887c, 0x62dd1ddf, 0x15da2d49, 0x8cd37cf3, 0xfbd44c65,
        0x4db26158, 0x3ab551ce, 0xa3bc0074, 0xd4bb30e2, 0x4adfa541, 0x3dd895d7, 0xa4d1c46d, 0xd3d6f4fb,
        0x4369e96a, 0x346ed9fc, 0xad678846, 0xda60b8d0, 0x44042d73, 0x33031de5, 0xaa0a4c5f, 0xdd0d7cc9,
        0x5005713c, 0x270241aa, 0xbe0b1010, 0xc90c2086, 0x5768b525, 0x206f85b3, 0xb966d409, 0xce61e49f,
        0x5edef90e, 0x29d9c998, 0xb0d09822, 0xc7d7a8b4, 0x59b33d17, 0x2eb40d81, 0xb7bd5c3b, 0xc0ba6cad,
        0xedb88320, 0x9abfb3b6, 0x03b6e20c, 0x74b1d29a, 0xead54739, 0x9dd277af, 0x04db2615, 0x73dc1683,
        0xe3630b12, 0x94643b84, 0x0d6d6a3e, 0x7a6a5aa8, 0xe40ecf0b, 0x9309ff9d, 0x0a00ae27, 0x7d079eb1,
        0xf00f9344, 0x8708a3d2, 0x1e01f268, 0x6906c2fe, 0xf762575d, 0x806567cb, 0x196c3671, 0x6e6b06e7,
        0xfed41b76, 0x89d32be0, 0x10da7a5a, 0x67dd4acc, 0xf9b9df6f, 0x8ebeeff9, 0x17b7be43, 0x60b08ed5,
        0xd6d6a3e8, 0xa1d1937e, 0x38d8c2c4, 0x4fdff252, 0xd1bb67f1, 0xa6bc5767, 0x3fb506dd, 0x48b2364b,
        0xd80d2bda, 0xaf0a1b4c, 0x36034af6, 0x41047a60, 0xdf60efc3, 0xa867df55, 0x316e8eef, 0x4669be79,
        0xcb61b38c, 0xbc66831a, 0x256fd2a0, 0x5268e236, 0xcc0c7795, 0xbb0b4703, 0x220216b9, 0x5505262f,
        0xc5ba3bbe, 0xb2bd0b28, 0x2bb45a92, 0x5cb36a04, 0xc2d7ffa7, 0xb5d0cf31, 0x2cd99e8b, 0x5bdeae1d,
        0x9b64c2b0, 0xec63f226, 0x756aa39c, 0x026d930a, 0x9c0906a9, 0xeb0e363f, 0x72076785, 0x05005713,
        0x95bf4a82, 0xe2b87a14, 0x7bb12bae, 0x0cb61b38, 0x92d28e9b, 0xe5d5be0d, 0x7cdcefb7, 0x0bdbdf21,
        0x86d3d2d4, 0xf1d4e242, 0x68ddb3f8, 0x1fda836e, 0x81be16cd, 0xf6b9265b, 0x6fb077e1, 0x18b74777,
        0x88085ae6, 0xff0f6a70, 0x66063bca, 0x11010b5c, 0x8f659eff, 0xf862ae69, 0x616bffd3, 0x166ccf45,
        0xa00ae278, 0xd70dd2ee, 0x4e048354, 0x3903b3c2, 0xa7672661, 0xd06016f7, 0x4969474d, 0x3e6e77db,
        0xaed16a4a, 0xd9d65adc, 0x40df0b66, 0x37d83bf0, 0xa9bcae53, 0xdebb9ec5, 0x47b2cf7f, 0x30b5ffe9,
        0xbdbdf21c, 0xcabac28a, 0x53b39330, 0x24b4a3a6, 0xbad03605, 0xcdd70693, 0x54de5729, 0x23d967bf,
        0xb3667a2e, 0xc4614ab8, 0x5d681b02, 0x2a6f2b94, 0xb40bbe37, 0xc30c8ea1, 0x5a05df1b, 0x2d02ef8d])
    crcpad = bytearray(b'\xff\xff\xff\xff')

    def __init__(self, path):

        # read the file
        f = open(path, "rb")
        s = f.read()
        f.close()
        self.image = bytearray(s)

        # pad image to 4-byte length
        while ((len(self.image) % 4) != 0):
            self.image.extend(b'\xff')

    def __crc32(self, bytes, state):
        for byte in bytes:
            index = (state ^ byte) & 0xff
            state = self.crctab[index] ^ (state >> 8)
        return state

    def crc(self, padlen):
        state = self.__crc32(self.image, int(0))
        for i in range(len(self.image), (padlen - 1), 4):
            state = self.__crc32(self.crcpad, state)
        return state


class uploader(QObject):
    _msg_singal = pyqtSignal(str)
    '''Uploads a firmware file to the PX FMU bootloader'''

    # protocol bytes
    INSYNC          = b'\x12'
    EOC             = b'\x20'

    # reply bytes
    OK              = b'\x10'
    FAILED          = b'\x11'
    INVALID         = b'\x13'     # rev3+
    BAD_SILICON_REV = b'\x14'     # rev5+

    # command bytes
    NOP             = b'\x00'     # guaranteed to be discarded by the bootloader
    GET_SYNC        = b'\x21'
    GET_DEVICE      = b'\x22'
    CHIP_ERASE      = b'\x23'
    CHIP_VERIFY     = b'\x24'     # rev2 only
    PROG_MULTI      = b'\x27'
    READ_MULTI      = b'\x28'     # rev2 only
    GET_CRC         = b'\x29'     # rev3+
    GET_OTP         = b'\x2a'     # rev4+  , get a word from OTP area
    GET_SN          = b'\x2b'     # rev4+  , get a word from SN area
    GET_CHIP        = b'\x2c'     # rev5+  , get chip version
    SET_BOOT_DELAY  = b'\x2d'     # rev5+  , set boot delay
    GET_CHIP_DES    = b'\x2e'     # rev5+  , get chip description in ASCII

    USB_STORAGE_MODE = b'\x33'    # usb storage mode

    REBOOT          = b'\x30'

    DEBUG           = b'\x31'     # THIS COMMAND WILL HOLD BOOTLOADER IN DEAD LOOP, AND NOT JUMP TO APP

    INFO_BL_REV     = b'\x01'        # bootloader protocol revision
    INFO_BOARD_ID   = b'\x02'        # board type
    INFO_BOARD_REV  = b'\x03'        # board revision
    INFO_FLASH_SIZE = b'\x04'        # max firmware size in bytes

    PROG_MULTI_MAX  = 252            # protocol max is 255, must be multiple of 4
    READ_MULTI_MAX  = 252            # protocol max is 255

    MAVLINK_REBOOT_ID_G = bytearray(b'\xfe\x01\xaf\x75\x00\xc8\x19\x5b\x31')
    MAVLINK_REBOOT_ID_F = bytearray(b'\xfe\x01\xaf\x14\x00\x65\x20\xc1\x07')

    MAX_FLASH_PRGRAM_TIME  = 0.001  # Time on an F7 to send SYNC, RESULT from last data in multi RXed

    def __init__(self, portname, baudrate_bootloader, baudrate_flight):
        super().__init__()
        # Open the port, keep the default timeout short so we can poll quickly.
        # On some systems writes can suddenly get stuck without having a
        # write_timeout > 0 set.
        # chartime 8n1 * bit rate is us
        self.chartime = 10 * (1.0 / baudrate_bootloader)

        # we use a window approche to SYNC,<result> gathring
        self.port = serial.Serial(portname, baudrate_bootloader, timeout=0.5, write_timeout=0)
        self.baudrate_bootloader = baudrate_bootloader
        self.baudrate_flight = baudrate_flight

    def close(self):
        if self.port is not None:
            self.port.close()

    def open(self):
        # upload timeout
        timeout = time.time() + 0.2

        # attempt to open the port while it exists and until timeout occurs
        while self.port is not None:
            portopen = True
            try:
                portopen = self.port.is_open
            except AttributeError:
                portopen = self.port.isOpen()

            if not portopen and time.time() < timeout:
                try:
                    self.port.open()
                except OSError:
                    # wait for the port to be ready
                    time.sleep(0.04)
                except serial.SerialException:
                    # if open fails, try again later
                    time.sleep(0.04)
            else:
                break

    # debugging code

    def __send(self, c):
        self.port.write(c)

    def __recv(self, count=1):
        c = self.port.read(count)
        if len(c) < 1:
            raise RuntimeError("timeout waiting for data (%u bytes)" % count)
        # print("recv " + binascii.hexlify(c))
        return c

    def __recv_int(self):
        raw = self.__recv(4)
        val = struct.unpack("<I", raw)
        return val[0]

    def __getSync(self, doFlush=True):
        if (doFlush):
            self.port.flush()
        c = bytes(self.__recv())
        if c != self.INSYNC:
            raise RuntimeError("unexpected %s instead of INSYNC" % c)
        c = self.__recv()
        if c == self.INVALID:
            raise RuntimeError("bootloader reports INVALID OPERATION")
        if c == self.FAILED:
            raise RuntimeError("bootloader reports OPERATION FAILED")
        if c != self.OK:
            raise RuntimeError("unexpected response 0x%x instead of OK" % ord(c))

    # attempt to get back into sync with the bootloader
    def __sync(self):
        # send a stream of ignored bytes longer than the longest possible conversation
        # that we might still have in progress
        self.port.flushInput()
        self.__send(uploader.GET_SYNC +
                    uploader.EOC)
        self.__getSync()

    def __trySync(self):
        try:
            self.port.flush()
            if (self.__recv() != self.INSYNC):
                #  print("unexpected 0x%x instead of INSYNC" % ord(c))
                self._msg_singal.emit("Erase Failed! No Answer!")
                return False
            c = self.__recv()
            if (c != self.OK):
                # print("unexpected 0x%x instead of OK" % ord(c))
                self._msg_singal.emit("Erase Failed!")
                return False
            return True
        except RuntimeError:
            # timeout, no response yet
            return False

    # send the GET_DEVICE command and wait for an info parameter
    def __getInfo(self, param):
        self.__send(uploader.GET_DEVICE + param + uploader.EOC)
        value = self.__recv_int()
        self.__getSync()
        return value

    def __drawProgressBar(self, label, progress, maxVal):
        if maxVal < progress:
            progress = maxVal

        percent = (float(progress) / float(maxVal)) * 100.0

        sys.stdout.write("\r%s: [%-20s] %.1f%%" % (label, '='*int(percent/5.0), percent))
        sys.stdout.flush()
        msg = "%s: [%-20s] %.1f%%" % (label, '='*int(percent/5.0), percent)
        self._msg_singal.emit(msg)

    # send the CHIP_ERASE command and wait for the bootloader to become ready
    def __erase(self, label):
        print("\n", end='')
        # 发送擦除指令
        self.__send(uploader.CHIP_ERASE +
                    uploader.EOC)

        # erase is very slow, give it 30s
        #擦除超时时间
        deadline = time.time() + 30.0
        while time.time() < deadline:

            usualEraseDuration = 15.0
            estimatedTimeRemaining = deadline-time.time()
            if estimatedTimeRemaining >= usualEraseDuration:
                self.__drawProgressBar(label, 30.0-estimatedTimeRemaining, usualEraseDuration)
            else:
                self.__drawProgressBar(label, 10.0, 10.0)
                sys.stdout.write(" (timeout: %d seconds) " % int(deadline-time.time()))
                sys.stdout.flush()

            if self.__trySync(): #下位机应答  return 如何没有应答或者应答错误，等待超时
                self.__drawProgressBar(label, 10.0, 10.0)
                self._msg_singal.emit('  ')
                return

        raise RuntimeError("timed out waiting for erase")

    # send a PROG_MULTI command to write a collection of bytes
    def __program_multi(self, data):

        if runningPython3:
            length = len(data).to_bytes(1, byteorder='big')
        else:
            length = chr(len(data))

        self.__send(uploader.PROG_MULTI) #发送烧写命令
        self.__send(length) #发送烧写长度
        self.__send(data)   #发送烧录数据
        self.__send(uploader.EOC)   
        self.__getSync(False)   #等下位机回应

    # verify multiple bytes in flash

    # send the reboot command
    def __reboot(self):
        self.__send(uploader.REBOOT +
                    uploader.EOC)
        self.port.flush()
        self.__getSync()

    # split a sequence into a list of size-constrained pieces
    def __split_len(self, seq, length):
        return [seq[i:i+length] for i in range(0, len(seq), length)]

    # upload code
    def __program(self, label, fw):
        print("\n", end='')
        code = fw.image #传送bin文件
        groups = self.__split_len(code, uploader.PROG_MULTI_MAX)    #把code数组进行分割。
        # Give imedate feedback
        self.__drawProgressBar(label, 0, len(groups))
        for bytes in groups:
            self.__program_multi(bytes)
            self.__drawProgressBar(label, groups.index(bytes), len(groups))
        self.__drawProgressBar(label, 100, 100)
        self._msg_singal.emit('  ')

    # verify code
    def __verify(self, label, fw):
        print("\n", end='')
        self.__drawProgressBar(label, 1, 100)
        expect_crc = fw.crc(self.fw_maxsize)
        self.__send(uploader.GET_CRC + uploader.EOC)
        #下位机应答一定要快，如果上位机校验很慢，可以加大下面的延时
        time.sleep(0.5)
        report_crc = self.__recv_int()
        self.__getSync()
        if report_crc != expect_crc:
            # print("Expected 0x%x" % expect_crc)
            # print("Got      0x%x" % report_crc)
            # raise RuntimeError("Program CRC failed")
            msg = f"Expected 0x{expect_crc}"
            self._msg_singal.emit(msg)
            msg = f"Got      0x{report_crc}"
            self._msg_singal.emit(msg)
            msg = f"Program CRC failed"
            self._msg_singal.emit(msg)
        self.__drawProgressBar(label, 100, 100)

    # get basic data about the board
    def identify(self):
        self.port.baudrate = self.baudrate_bootloader
        # make sure we are in sync before starting
        self.__sync()

        # get the bootloader protocol ID first
        #！可能需要注释掉
        self.bl_rev = self.__getInfo(uploader.INFO_BL_REV)          # show user some infomation only
        self.board_type = self.__getInfo(uploader.INFO_BOARD_ID)    # show user some infomation only
        self.board_rev = self.__getInfo(uploader.INFO_BOARD_REV)    # show user some infomation only

        self.fw_maxsize = self.__getInfo(uploader.INFO_FLASH_SIZE)  # get chip flash size, we use this param to calculate crc32

    def to_usb(self):
        self.__send(uploader.USB_STORAGE_MODE)

    # upload the firmware
    def upload(self, fw):
        # Make sure we are doing the right thing
        start = time.time()

        self.__erase("Erase  ") #带下划线 是私有方法，不带下滑线 是共有函数
        self.__program("Program", fw)
        self.__verify("Verify ", fw)
        print("\nRebooting.", end='')
        self.__reboot()
        self.port.close()
        print(" Elapsed Time %3.3f\n" % (time.time() - start))
        msg = "\nRebooting. Elapsed Time %3.3f\n" % (time.time() - start)
        self._msg_singal.emit(msg)

    def send_reboot(self):
        print("Attempting reboot on %s with baudrate=%d..." % (self.port.port, self.port.baudrate), file=sys.stderr)
        if "ttyS" in self.port.port:
            print("If the board does not respond, check the connection to the Flight Controller")
        else:
            print("If the board does not respond, unplug and re-plug the connector.", file=sys.stderr)

        try:
            self.port.baudrate = self.baudrate_flight
            # try MAVLINK command first
            self.port.flush()
            self.__send(uploader.MAVLINK_REBOOT_ID_G)
            self.__send(uploader.MAVLINK_REBOOT_ID_F)
            self.port.flush()
            self.port.baudrate = self.baudrate_bootloader
        except Exception:
            try:
                self.port.flush()
                self.port.baudrate = self.baudrate_bootloader
            except Exception:
                pass

        return True

class item:
    def __init__(self):
        self.port = ''
        self.firmware = ''
        self.baud_bootloader = 115200
        self.baud_flight = 115200

class uploader_main(QObject):
    _msg_signal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.flg = True
        self.load_flg =False
        self.port_find_list=[]
        self.putload_port = ''
        self.port_list=[]
        
    def updateMsg(self, msg):
        self._msg_signal.emit(msg)

    def find_serial(self):
        # 查询串口列表，并尝试握手，优先握手新添加串口
        if self.flg is True:
            # 建立初始串口列表
            _t = time.time()
            self.port_list = list(serial.tools.list_ports.comports())
            print( list(serial.tools.list_ports.comports()) )
            if len(self.port_list) == 0:
                self._msg_signal.emit("No Serial Port.\r")
            else:
                for i in range(0,len(self.port_list)):
                    self.port_find_list.append(self.port_list[i].device)
                    print(f'Find Serial Port: {self.port_list[i].device}')
                    self._msg_signal.emit(f'Find Serial Port: {self.port_list[i].device}')
            self._msg_signal.emit('Please restart the drone.\r')
            self.flg = False
        else:
            self.port_list = list(serial.tools.list_ports.comports())
            for i in range(0,len(self.port_list)):
                if self.port_list[i].device not in self.port_find_list:
                    self.port_find_list.append(self.port_list[i].device)
                    # args.port = port_list[i].device
                    self.putload_port = self.port_list[i].device
                    self._msg_signal.emit(f'Find New Serial Port: {self.putload_port}.\r')
                    self.load_flg = True
                    print(f'Find New Serial Port: {self.putload_port}.\r')

    def to_usb(self):
 
        args = item()
        msg = f"search the serial port!"
        self._msg_signal.emit(msg)        
        args.port = self.putload_port 
        try:
            while True:
                portlist = []
                patterns = args.port.split(",")
                # on unix-like platforms use glob to support wildcard ports. This allows
                # the use of /dev/serial/by-id/usb-3D_Robotics on Linux, which prevents the upload from
                # causing modem hangups etc
                if "linux" in _platform or "darwin" in _platform or "cygwin" in _platform:
                    import glob
                    for pattern in patterns:
                        portlist += glob.glob(pattern)
                else:
                    portlist = patterns

                successful = False
                for port in portlist:
                    # create an uploader attached to the port
                    try:
                        if "linux" in _platform:
                            # Linux, don't open Mac OS and Win ports
                            if "COM" not in port and "tty.usb" not in port:
                                up = uploader(port, args.baud_bootloader, args.baud_flight)
                        elif "darwin" in _platform:
                            # OS X, don't open Windows and Linux ports
                            if "COM" not in port and "ACM" not in port:
                                up = uploader(port, args.baud_bootloader, args.baud_flight)
                        elif "cygwin" in _platform:
                            # Cygwin, don't open native Windows COM and Linux ports
                            if "COM" not in port and "ACM" not in port:
                                up = uploader(port, args.baud_bootloader, args.baud_flight)
                        elif "win" in _platform:
                            # Windows, don't open POSIX ports
                            if "/" not in port:
                                up = uploader(port, args.baud_bootloader, args.baud_flight)
                        up._msg_singal.connect(self.updateMsg)

                    except Exception as e:
                        # open failed, rate-limit our attempts
                        self._msg_signal.emit(str(e))
                        print(e)
                        time.sleep(0.05)

                        # and loop to the next port
                        # continue
                        return

                    found_bootloader = False
                    while (True):
                        up.open()
                        try:
                            up.to_usb()
                        except Exception:
                            # print("send to usb command !")
                            msg = f"send u_dri command"
                            self._msg_signal.emit(msg)
                            return
        except Exception:
            print("to usb end")


    def update(self, firm_dir):

        args = item()
        msg = f"search the serial port!"
        self._msg_signal.emit(msg)        
        args.port = self.putload_port
        args.firmware = firm_dir

        # warn people about ModemManager which interferes badly with Pixhawk
        if os.path.exists("/usr/sbin/ModemManager"):
            print("==========================================================================================================")
            print("WARNING: You should uninstall ModemManager as it conflicts with any non-modem serial device (like Pixhawk)")
            print("==========================================================================================================")

        # We need to check for pyserial because the import itself doesn't
        # seem to fail, at least not on macOS.
        pyserial_installed = False
        try:
            if serial.__version__:
                pyserial_installed = True
        except:
            pass

        try:
            if serial.VERSION:
                pyserial_installed = True
        except:
            pass

        if not pyserial_installed:
            print("Error: pyserial not installed!")
            print("(Install using: sudo pip install pyserial)")
            # sys.exit(1)
            msg = f"Error: pyserial not installed!"
            self._msg_signal.emit(msg)
            return

        # Load the firmware file
        fw = firmware(args.firmware)
        # Spin waiting for a device to show up
        try:
            while True:
                portlist = []
                patterns = args.port.split(",")
                # on unix-like platforms use glob to support wildcard ports. This allows
                # the use of /dev/serial/by-id/usb-3D_Robotics on Linux, which prevents the upload from
                # causing modem hangups etc
                if "linux" in _platform or "darwin" in _platform or "cygwin" in _platform:
                    import glob
                    for pattern in patterns:
                        portlist += glob.glob(pattern)
                else:
                    portlist = patterns

                successful = False
                for port in portlist:
                    # create an uploader attached to the port
                    try:
                        if "linux" in _platform:
                            # Linux, don't open Mac OS and Win ports
                            if "COM" not in port and "tty.usb" not in port:
                                up = uploader(port, args.baud_bootloader, args.baud_flight)
                        elif "darwin" in _platform:
                            # OS X, don't open Windows and Linux ports
                            if "COM" not in port and "ACM" not in port:
                                up = uploader(port, args.baud_bootloader, args.baud_flight)
                        elif "cygwin" in _platform:
                            # Cygwin, don't open native Windows COM and Linux ports
                            if "COM" not in port and "ACM" not in port:
                                up = uploader(port, args.baud_bootloader, args.baud_flight)
                        elif "win" in _platform:
                            # Windows, don't open POSIX ports
                            if "/" not in port:
                                up = uploader(port, args.baud_bootloader, args.baud_flight)
                        up._msg_singal.connect(self.updateMsg)

                    except Exception as e:
                        # open failed, rate-limit our attempts
                        self._msg_signal.emit(str(e))
                        print(e)
                        time.sleep(0.05)

                        # and loop to the next port
                        # continue
                        return

                    found_bootloader = False
                    while (True):
                        up.open()

                        # port is open, try talking to it
                        try:
                            # identify the bootloader 
                            up.identify()
                            found_bootloader = True                            
                            print("Found board id: %s,%s bootloader version: %s on %s" % (up.board_type, up.board_rev, up.bl_rev, port))
                            msg = "Found board id: %s,%s bootloader version: %s on %s\n" % (up.board_type, up.board_rev, up.bl_rev, port)
                            self._msg_signal.emit(msg)
                            break

                        except Exception:
                            msg = f"identify fail, try reboot."
                            self._msg_signal.emit(msg)
                            if not up.send_reboot():#握手失败，尝试让飞控重启
                                break

                            # wait for the reboot, without we might run into Serial I/O Error 5
                            time.sleep(0.25)

                            # always close the port
                            up.close() 

                            # wait for the close, without we might run into Serial I/O Error 6
                            time.sleep(0.3)

                    if not found_bootloader:
                        # Go to the next port
                        continue

                    try:
                        # ok, we have a bootloader, try flashing it
                        #开始烧写固件
                        up.upload(fw)

                        # if we made this far without raising exceptions, the upload was successful
                        successful = True

                    except RuntimeError as ex:
                        # print the error
                        # print("\nERROR: %s" % ex.args)
                        msg = f"ERROR {ex.args}"
                        self._msg_signal.emit(msg)

                    except IOError:
                        up.close()
                        continue

                    finally:
                        # always close the port
                        up.close()

                    # we could loop here if we wanted to wait for more boards...
                    if successful:
                        self._msg_signal.emit('Uploader Success\r')
                        return
                    else:
                        self._msg_signal.emit('Uploader Failed\r')
                        return

                # Delay retries to < 20 Hz to prevent spin-lock from hogging the CPU
                time.sleep(0.05)

        # CTRL+C aborts the upload/spin-lock by interrupt mechanics
        except KeyboardInterrupt:
            # print("\n Upload aborted by user.")
            # sys.exit(0)
            self._msg_signal.emit(' Upload aborted by user.\r')
            return



if __name__ == '__main__':

    class update_serial_thread(QThread):
        _signal = pyqtSignal(object)
        def __init__(self):
            super(update_serial_thread,self).__init__()
            self.flg = True
            self.uploader_main = uploader_main()
            self.firm_dir = "Evolve~1"

        def run(self):
            while True:
                time.sleep(0.05)
                if self.flg:
                    self.uploader_main.find_serial()
                    if self.uploader_main.load_flg :
                        print(self.uploader_main.putload_port)
                        print(self.firm_dir)
                        self.uploader_main.update(self.firm_dir)
                        self.flg = False
                        self.uploader_main.load_flg =False

    def test(object):
        print(object)

    app = QtWidgets.QApplication(sys.argv)
    seir_name = "com12"
    firm_dir = "Evolve~1"
    
    app_up = update_serial_thread()
    app_up.uploader_main._msg_signal.connect(test)
    app_up.start()
    sys.exit(app.exec_())
