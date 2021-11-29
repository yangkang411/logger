# coding: utf-8
"""
三一重工的数据解析。
解析CANTest log的含中文字符的数据。

Created on 2021-8-11
@author: Ocean

序号,系统时间,时间标识,CAN通道,传输方向,ID号,帧类型,帧格式,长度,数据
00000,="12:04:59.533",0x592897,ch1,接收,0x0009001C,数据帧,扩展帧,0x08,x| 05 C3 8A 43 00 02 EE 00 
00001,="12:04:59.533",0x59289C,ch1,接收,0x00F02A81,数据帧,扩展帧,0x08,x| 03 7D FD 7C FB 7C 40 04 
00002,="12:04:59.533",0x5928A2,ch1,接收,0x08F02D83,数据帧,扩展帧,0x08,x| 50 79 F1 7C 07 7E 80 04 
"""

import os
import sys
import datetime
import string
import numpy as np
import scipy.io as io
from numpy.core.numeric import roll
from can_parser import PGNType, CANParser

class CANTestLogReader():
    '''
    '''
    def __init__(self, file_name):
        self.file = file_name
        self.log_file_all = None
        self.log_file_gyro = None
        self.log_file_accel = None
        self.log_file_tilt = None

        if file_name is not None:
            self.create_log_files()
        pass

    def create_log_files (self):
        '''
        create log files.
        '''
        if not os.path.exists('data/'):
            os.mkdir('data/')
        start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        (filepath, tempfilename) = os.path.split(self.file)
        (shotname, extension) = os.path.splitext(tempfilename)

        file_dir        = os.path.join('data', '{0}_[{1}].csv'.format(start_time, shotname))
        file_dir_gyro   = os.path.join('data', '{0}_[{1}]_gyro.csv'.format(start_time, shotname))
        file_dir_accel  = os.path.join('data', '{0}_[{1}]_accel.csv'.format(start_time, shotname))
        file_dir_tilt   = os.path.join('data', '{0}_[{1}]_tilt.csv'.format(start_time, shotname))

        self.log_file_all   = open(file_dir, 'w')
        self.log_file_gyro  = open(file_dir_gyro, 'w')
        self.log_file_accel = open(file_dir_accel, 'w')
        self.log_file_tilt  = open(file_dir_tilt, 'w')

        print('Start logging: {0}'.format(file_dir))
        header = 'time(ms), ID, PGN, payload'.replace(' ', '')
        self.log_file_all.write(header + '\n')
        self.log_file_all.flush()
        pass

    def close_log_files (self):
        self.log_file_all.close()
        self.log_file_gyro.close()
        self.log_file_accel.close()
        self.log_file_tilt.close()
        pass

    def read(self,):
        gyro  = []
        accel = []
        tilt  = []
        can_parser = CANParser()
        # 注意，因为log中有中文，所以指定 gbk.
        with open(self.file, 'r', encoding='gbk') as f:
            idx = 0
            line = f.readline()
            while line:
                try:
                    idx += 1
                    if line.startswith('序号'): #跳过第1行，及文件中出现表头的行。
                        line = f.readline()
                        continue

                    item = line.split(',')

                    # get system time.
                    sys_time = item[1]
                    sys_time = sys_time.replace('"', '').replace('=', '')

                    # get frame id
                    id = item[5]
                    id = int(id, 16)

                    # get msg
                    msg = item[9].split(' ')[1:-1] # eg: ['x|', '3B', 'E8', '7D', 'F5', 'BF', '7C', '00', '06'],所以删除第一个元素。
                    msg = [ int(p, 16) for p in msg]

                    (_Priority, _PGN, _PF, _PS, _SA) = can_parser.parse_PDU(id)
                    data = None
                    str = '{0},{1},{2},'.format(sys_time, hex(id), _PGN)

                    if _PGN == PGNType.SSI2.value:    # Slope Sensor Information 2
                        data = can_parser.parse_tilt(msg)
                        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
                        self.log_file_tilt.write(str )
                        self.log_file_tilt.flush()
                    elif _PGN == PGNType.ARI.value:   # Angular Rate
                        data = can_parser.parse_gyro(msg)
                        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
                        self.log_file_gyro.write(str )
                        self.log_file_gyro.flush()
                    elif _PGN == PGNType.ACCS.value:  # Acceleration Sensor
                        data = can_parser.parse_accel(msg)
                        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
                        self.log_file_accel.write(str )
                        self.log_file_accel.flush()
                    else: # unknown PGN msg
                        pass

                    if data is not None:
                        self.log_file_all.write(str)
                        self.log_file_all.flush()
                    pass

                    line = f.readline()

                except Exception as e:
                    print('Error at line {0} :{1}'.format(idx,e))
                    return


def read_from_trc_logfile(file_name):
    '''
    '''
    can_reader = CANTestLogReader(file_name)
    can_reader.read()
    can_reader.close_log_files()

if __name__ == '__main__':
    file_name = '/Users/songyang/project/analyze/drive_test/SANY/2021-9-17/data/RawData/Test1/MTLT305D_Teset1.csv'
    read_from_trc_logfile(file_name)
