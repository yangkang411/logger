# coding: utf-8
"""
三一重工的数据解析。

Created on 2021-8-11
@author: Ocean
"""

import os
import sys
import datetime
import string
import numpy as np
import scipy.io as io
from numpy.core.numeric import roll
from can_parser import PGNType, CANParser

class TrcReader():
    '''
    '''
    def __init__(self, file_name):
        self.file = file_name
        self.log_file_gps = None

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

        file_dir_gps    = os.path.join('data', '{0}_[{1}]_gps.csv'.format(start_time, shotname))
        self.log_file_gps   = open(file_dir_gps, 'w')
        header = 'time, ID, PGN, lat, lon, alt, yaw, slop'.replace(' ', '')
        self.log_file_gps.write(header)
        self.log_file_gps.flush()
        pass

    def close_log_files (self):
        self.log_file_gps.close()
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
                    if id == '0x018A':
                        a = 1123
                    id = int(id, 16)

                    # get msg
                    msg = item[9].split(' ')[1:-1] # eg: ['x|', '3B', 'E8', '7D', 'F5', 'BF', '7C', '00', '06'],所以删除第一个元素。
                    msg = [ int(p, 16) for p in msg]

                    (_Priority, _PGN, _PF, _PS, _SA) = can_parser.parse_PDU(id)
                    data = None
                    str = '{0},{1},{2},'.format(sys_time, hex(id), _PGN)

                    if _SA == 0X8A:  # GPS latitude
                        data = can_parser.parse_GPS_LLA(msg)
                        str = '\n' + str + ','.join('{0:f}'.format(i) for i in data) + ','
                        self.log_file_gps.write(str )
                        self.log_file_gps.flush()
                    elif _SA == 0X8B:  # GPS longitude
                        data = can_parser.parse_GPS_LLA(msg)
                        str = ','.join('{0:f}'.format(i) for i in data) + ','
                        self.log_file_gps.write(str )
                        self.log_file_gps.flush()
                    elif _SA == 0X8C:  # GPS altitude
                        data = can_parser.parse_GPS_LLA(msg)
                        str = ','.join('{0:f}'.format(i) for i in data) + ','
                        self.log_file_gps.write(str )
                        self.log_file_gps.flush()
                    elif _SA == 0X8F:  # GPS yaw and slop. 
                        data = can_parser.parse_GPS_angle(msg)
                        str = ','.join('{0:f}'.format(i) for i in data) + ','
                        self.log_file_gps.write(str )
                        self.log_file_gps.flush()
                    else: # unknown PGN msg
                        pass

                    line = f.readline()

                except Exception as e:
                    print('Error at line {0} :{1}'.format(idx,e))
                    return


def read_from_trc_logfile(file_name):
    '''
    '''
    trc_reader = TrcReader(file_name)
    trc_reader.read()
    trc_reader.close_log_files()

if __name__ == '__main__':
    # For single file
    file_name = '/Users/songyang/project/analyze/drive_test/SANY/2021-8-11/data/新纳测试/自由测试_merge.csv'
    read_from_trc_logfile(file_name)

    # For folder
    # folder = '/Users/songyang/project/analyze/drive_test/Hyundai/2021-6-25/data/210616_ACE_CAN_Logged'
    # for root, dirs, files in os.walk(folder):
    #     for file in files:
    #         item = os.path.join(root, file)
    #         fmt = os.path.splitext(item)[-1]
    #         if fmt.lower() != '.trc':
    #             continue
    #         else:
    #             read_from_trc_logfile(item)

