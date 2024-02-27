# -*- coding: utf-8 -*-
'''
# Created on Feb-21-20 15:52 
# protocol_v1.py
# @author: 
'''

import sys, os
sys.path.append(os.getcwd())
from lib.delegate import *

# array被当做整形计算
def ss_crc_calculate(array, start, length):
    crc = 0xffff
    while length > 0:
        tmp = (array[start]) ^ (crc & 0xff)
        tmp ^= ((tmp << 4) & 0xff)
        crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        length -= 1
        start += 1
    return crc

class TelemK:
    ktelem_plot = 0x00

# v1.0 HEAD|ID|XData|LEN|CRC1|CRC2|END
class TelemParser:
    """
    包处理
    """
    PKG_HEAD = 0xFE
    PKG_END = 0xFD
    PKG_MIN_LEN = 6
    PKG_RX_MAX = 256
    DATA_INDEX = 2
    DATA_LEN_INDEX = -4
    rx_buffer = []

    # def __init__(self):
    #     # self.PKG_HEAD = 0xFD
    #     # self.PKG_END = 0xFE
    #     # self.PKG_RX_MAX = 128
    #     self.rx_buffer = []
    #     Delegate.add_listener('ON_COM_RX', self.parse)
    #     Delegate.add_listener('ON_MSG_TX', self.on_msg_send)

    @staticmethod
    def init():
        Delegate.add_listener('ON_COM_RX', TelemParser.parse)


    @staticmethod
    def msg_id(msg):
        return msg[1]

    # 返回数据部分的数组
    @staticmethod
    def msg_data(msg):
        return msg[TelemParser.DATA_INDEX: TelemParser.DATA_LEN_INDEX]

    # 传入的可以不是bytearray而是原始数组即可
    @staticmethod
    def pack_data(msg_id, raw):
        # print(raw)
        data_len = len(raw)
        packed_data = raw[:]  # cpy all
        packed_data.insert(0, TelemParser.PKG_HEAD)
        packed_data.insert(1, msg_id)
        packed_data.append(data_len)
        crc = ss_crc_calculate(packed_data, 0, len(packed_data))
        packed_data.append(crc >> 8)
        packed_data.append(crc & 0x00ff)
        packed_data.append(TelemParser.PKG_END)
        return packed_data

    @staticmethod
    def _get_pkg_len(data_len):
        return data_len + TelemParser.PKG_MIN_LEN


    '''
    包套包只会解出最内的包，因为每次解包后会清空接收缓冲
    '''
    @staticmethod
    def parse_char(hval):
        if(type(hval) is str):
            hval = ord(hval)
        # 如果缓冲过多，直接清空
        rx_len = len(TelemParser.rx_buffer)
        if rx_len > TelemParser.PKG_RX_MAX - 1:
            TelemParser.rx_buffer = []
            rx_len = 0
        # push value
        TelemParser.rx_buffer.append(hval)
        rx_len += 1

        # buffer is MAYBE enough for parsing
        if hval == TelemParser.PKG_END and rx_len >= TelemParser.PKG_MIN_LEN:
            # print(TelemParser.rx_buffer[-4])
            data_len = TelemParser.rx_buffer[TelemParser.DATA_LEN_INDEX]
            pkg_len = TelemParser._get_pkg_len(data_len)
            # print('data len rx is %d' % (TelemParser.rx_buffer[-4]))
            # buffer is sure enough for parsing
            if rx_len >= pkg_len:
                pkg_head = TelemParser.rx_buffer[-pkg_len]
                # head is match
                if pkg_head == TelemParser.PKG_HEAD:
                    rx_crc = (TelemParser.rx_buffer[-3]) << 8
                    rx_crc |= TelemParser.rx_buffer[-2]
                    ck_crc = ss_crc_calculate(
                        TelemParser.rx_buffer, rx_len - pkg_len, pkg_len - 3)
                    if ck_crc == rx_crc:
                        # cpy data out
                        msg = [0] * pkg_len
                        msg[0:] = TelemParser.rx_buffer[-pkg_len:]
                        # msg = [v for i in TelemParser.rx_buffer[-pkg_len:]]
                        # clear tmp buffer
                        TelemParser.rx_buffer = []
                        return msg
                    else:
                        # print 'rx crc is %d ck crc is %d' % (rx_crc, ck_crc)
                        print('crc check fail')
                else:
                    pass
                    # print('head err')  # 不打印，因为确实可能出现不匹配的特例
            else:
                pass
                # print 'rx len %d pkt len %d' % (rx_len, pkg_len)
                # print('length err')  # 不打印，确实可能出现不匹配的特例
        return []


    # 协议类只要实现这个函数就可以了，最后通过Delegate发布。
    @staticmethod
    def parse(data):
        if len(data) < 1:
            return
        # print('try to parse')
        for c in data:
            msg = TelemParser.parse_char(c)
            if msg and len(msg) > 0:
               	Delegate.broadcast(TelemParser.msg_id(msg), TelemParser.msg_data(msg))


    # 数据打包+发送，msg_data可以是list和bytearray
    @staticmethod
    def send(msg_id, msg_data):
        # print('消息数据类型', type(msg_data))
        pkt = TelemParser.pack_data(msg_id, msg_data)

        # 打印打包好的数据
        # pkt_text = '打包好的数据：'
        # for x in pkt:
        #     pkt_text += '0x%02X,' % x
        # print(pkt_text)

        if type(msg_data) is list:
            Delegate.broadcast('ON_COM_TX', bytearray(pkt))
        elif type(msg_data) is bytearray or type(msg_data) is bytes:
            Delegate.broadcast('ON_COM_TX', pkt)
        else:
            print('不支持打包格式')

import struct
class B2V:  # bytes to value
    unpacker = None

    @staticmethod
    def unpack_to_i16(list_data):
        bydata = bytearray(list_data)
        # 收到的数据不是2的倍数不合法
        num = len(bydata)
        if num % 2 != 0 or num == 0:
            return []
        num /= 2;  # 获取实际数据个数
        # # 初始化解释器
        # if B2V.unpacker is None:
        #     # print('首次初始化解释器')
        #     B2V.unpacker = struct.Struct('%dh' % num)
        # elif B2V.unpacker.size != len(bydata):
        #     # print('切换解释器长度')
        #     B2V.unpacker = struct.Struct('%dh' % num)
        # # 获取实际的int16数据
        # values = B2V.unpacker.unpack_from(bydata)
        # print('values len ' + str(num))
        fmt = ('%dh' % num)
        values = struct.unpack(fmt, bydata)
        return values

    @staticmethod
    def unpack_to_str(list_data):
        return bytearray(list_data).decode()


    @staticmethod
    def unpack_to_float(list_data):
        bydata = bytearray(list_data)
        num = len(bydata)
        if num == 4: # 单独一个float独自处理一下子
            return struct.unpack('f', bydata)[0]
        if num % 2 != 0 or num == 0:
            return []
        fmt = '%df' % (num / 4)
        return struct.unpack(fmt, bydata)

    @staticmethod
    def pack(fmt, list_data):
        return bytearray(struct.pack(fmt, *list_data))


def __print_hex(data):
    text = ''
    for x in data:
        text += '0x%02X,' % x
    print(text)

# 联合串口工具测试协议栈
if __name__ == '__main__':
    # from lib.data_cmd import *
    import struct


    # bydata = bytearray([1, 2, 3, 4, 5])
    # bydata = [1, 2, 3, 4, 5]
    bydata = [0xcd, 0xcc, 0x2c, 0x40, 0xcd, 0xcc, 0x2c, 0x40,]
    output = TelemParser.pack_data(0x00, bydata)
    # [254, 37, 1, 2, 3, 4, 5, 5, 225, 32, 253]
    output = struct.pack('=BBBBB', *bydata)
    
    list_data = [8, *(ord(x) for x in 'shit')]
    output = struct.pack('=B%ds' % len('shit'), 8, ('shit').encode())



    if type(output) is bytearray:
        print('hello')
    else:
        print('not bytearry', type(output))
    if type(output) is list:
        print('hello list')

    print(output)