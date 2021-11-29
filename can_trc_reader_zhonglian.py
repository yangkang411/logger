# coding: utf-8
"""
中联重科的CAN trc数据解析。

Created on 2021-8-10
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
        file_dir_tilt  = os.path.join('data', '{0}_[{1}]_tilt.csv'.format(start_time, shotname))

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
        with open(self.file, 'r', encoding='utf-8') as f:
            idx = 0
            line = f.readline()
            while line:
                try:
                    idx += 1
                    line = f.readline()
                    if idx == 1:
                        continue

                    item = line.split(',')

                    # get system time.
                    sys_time = item[0]

                    # get frame id
                    id = item[13]
                    id = int(id, 16)

                    # get msg
                    msg = item[20].split(' ')[0:-1]
                    msg = [ int(p, 16) for p in msg]

                    (_Priority, _PGN, _PF, _PS, _SA) = can_parser.parse_PDU(id)
                    data = None
                    str = '{0},{1},{2},'.format(sys_time, hex(id), _PGN)

                    if _PGN == PGNType.SSI2.value:    # Slope Sensor Information 2
                        data = can_parser.parse_tilt(msg)
                        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
                        self.log_file_tilt.write(str )
                        self.log_file_tilt.flush()
                        tilt = tilt + list(data)
                    elif _PGN == PGNType.ARI.value:   # Angular Rate
                        data = can_parser.parse_gyro(msg)
                        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
                        self.log_file_gyro.write(str )
                        self.log_file_gyro.flush()
                        gyro = gyro + list(data)
                    elif _PGN == PGNType.ACCS.value:  # Acceleration Sensor
                        data = can_parser.parse_accel(msg)
                        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
                        self.log_file_accel.write(str )
                        self.log_file_accel.flush()
                        accel = accel + list(data)
                    else: # unknown PGN msg
                        pass

                    if data is not None:
                        self.log_file_all.write(str)
                        self.log_file_all.flush()
                    pass

                    # line = f.readline()

                except Exception as e:
                    print('Error at line {0} :{1}'.format(idx,e))



def read_from_trc_logfile(file_name):
    '''
    '''
    trc_reader = TrcReader(file_name)
    trc_reader.read()
    trc_reader.close_log_files()

if __name__ == '__main__':
    # For single file
    file_name = '/Users/songyang/Desktop/-5.4deg.csv'
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

