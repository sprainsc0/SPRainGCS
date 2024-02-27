# -*- coding: utf-8 -*-
'''
# Created on Jan-03-20 16:42 
# log.py
# @author: 
'''

import sys
import sip
import struct
import time

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

type_replace = [
    '4s',
    '16s',
    '64s',
    'h',
    'H',
    'i',
    'I',
    'B',
]

type_user_define = [
    'n', # char[4]
    'N', # char[16]
    'Z', # char[64]
    'c', # int16_t * 100
    'C', # uint16_t * 100
    'e', # int32_t * 100
    'E', # uint32_t * 100
    'M', # uint8_t flight mode
]

class log_parser(QtCore.QObject):
    _progress_update_signal = QtCore.pyqtSignal(float)
    def __init__(self):
        super(log_parser, self).__init__()

        self.head        = b'\xae\x86'
        self.fmt_head    = b'\xae\x86\x80'

        self.fmt_content_dict = {}   # 解析后存放在字典中
        self.msg_dict = {}
        self.msg_dict_backup = {}   # 用来进行计算，避免深拷贝耗时

        self.analysis_progress = 0


    def fmt_analysis(self, all_content):
        self.fmt_content_dict = {}
        self.msg_dict = {}
        self.msg_dict_backup = {}

        beg_idx = all_content.find(self.fmt_head)
        while beg_idx >= 0:
            # 一帧结束位置
            end_index = all_content.find(self.head, beg_idx + len(self.fmt_head))

            # 取出内容
            content = all_content[beg_idx:end_index]
            try:
                fmt_id = content[3]
                fmt_length = content[4] | (content[5] << 8)
                fmt_name = content[6:10].decode().replace("\x00","")
                fmt_type = content[10:26].decode().replace("\x00","")
                fmt_labels = content[26:89].decode().replace("\x00","").split(',')

                # 将内容解析出
                self.fmt_content_dict.setdefault(str(fmt_id), {})
                self.fmt_content_dict[str(fmt_id)].setdefault('fmt_name', fmt_name)
                self.fmt_content_dict[str(fmt_id)].setdefault('fmt_length', fmt_length)
                self.fmt_content_dict[str(fmt_id)].setdefault('fmt_type', fmt_type)
                self.fmt_content_dict[str(fmt_id)].setdefault('fmt_labels', fmt_labels)
                self.fmt_content_dict[str(fmt_id)].setdefault('size', 0)

                self.msg_dict.setdefault(fmt_name, {})
                self.msg_dict_backup.setdefault(fmt_name, {})
                for i in range(len(fmt_labels)):
                    self.msg_dict[fmt_name].setdefault(fmt_labels[i], [])
                    self.msg_dict_backup[fmt_name].setdefault(fmt_labels[i], [])
            except:
                print('data err')

            # 找出下一帧起始位置 无则返回-1 退出循环
            beg_idx = all_content.find(self.fmt_head, beg_idx + len(self.fmt_head))

        for key in self.fmt_content_dict:
            for i in range(len(type_user_define)):
                if type_user_define[i] in self.fmt_content_dict[key]['fmt_type']:
                    self.fmt_content_dict[key]['fmt_type'] = self.fmt_content_dict[key]['fmt_type'].replace(type_user_define[i], type_replace[i])

    def msg_analysis(self, all_content):
        beg_idx = all_content.find(self.head)
        while beg_idx >= 0:
            if (beg_idx + len(self.head)) >= len(all_content):
                break
            msg_id = str(all_content[beg_idx + len(self.head)])
            next_beg_idx = all_content.find(self.head, beg_idx + len(self.head))
            try:
                if msg_id in self.fmt_content_dict \
                and (next_beg_idx - beg_idx) == self.fmt_content_dict[msg_id]['fmt_length'] \
                and next_beg_idx != -1:
                    # t v1 v2 v3 ...
                    fmt = '='+self.fmt_content_dict[msg_id]['fmt_type']
                    data_list = struct.unpack(fmt, all_content[beg_idx + len(self.head) + 1:next_beg_idx])
                    for i in range(len(self.fmt_content_dict[msg_id]['fmt_labels'])):
                        tree_name = self.fmt_content_dict[msg_id]['fmt_name']
                        label = self.fmt_content_dict[msg_id]['fmt_labels'][i]
                        if label == 'TimeUS':
                            timeStamp_s = (data_list[i]) / 1000000
                            self.msg_dict[tree_name][label].append(timeStamp_s)
                            self.msg_dict_backup[tree_name][label].append(timeStamp_s)
                        else:
                            self.msg_dict[tree_name][label].append(data_list[i])
                            self.msg_dict_backup[tree_name][label].append(data_list[i])
            except Exception as e:
                print(e)
            beg_idx = next_beg_idx
            
            if beg_idx/len(all_content) - self.analysis_progress > 0.01:
                self.analysis_progress = beg_idx/len(all_content)
                # print(self.analysis_progress)
                self._progress_update_signal.emit(self.analysis_progress * 100)

        self.analysis_progress = 0

    def analysis_log(self, path):  #解析全部数据
        file = open(path, 'rb') #绝对路径
        all_content = file.read()
        
        print(path)
        self.fmt_analysis(all_content)

        self.msg_analysis(all_content)

        return self.msg_dict


if __name__ == '__main__':
    # _parser = log_parser()
    # _parser.analysis_log('C:/Users/Qu/Desktop/datafile_00000056.log')

    print("sd log analysis test...")
    pass


