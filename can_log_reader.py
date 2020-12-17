# -*- coding: utf-8 -*
"""
Parse CAN log of CAN-Tester and save to csv file.
Created on 2020-7-7
@author: Ocean

Note: 这个脚本没有写完，解析这个文件是一件优先级不高的事。暂且放着。
"""

import sys
import os
import datetime
import time
import struct
import math
from enum import Enum
from can_reader import CanReader, PGN


def parse_can_tester_log(log_file):
    '''

    '''
    start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if not os.path.exists('data/'):
        os.mkdir('data/')
    file_dir = os.path.join('data', 'can_'+ start_time+'.csv')
    print('Start: {0}'.format(file_dir))
    ref_file = open(file_dir, 'w')
    header = 'Time(s),Roll(deg),Pitch(deg),X-Rate(dps),Y-Rate(dps),Z-Rate(dps),X-Accel(m/s2),Y-Accel(m/s2),Z-Accel(m/s2)'
    ref_file.write(header + '\n')
    ref_file.flush()

    can_reader = CanReader(None)

    with open(log_file, 'r', encoding='utf-8') as f:
        idx = 1
        line = f.readline()
        while line:
            try:
                # ignore the first line.
                if idx == 1:
                    idx += 1
                    line = f.readline()
                    continue

                item = line.split(',')
                # get system time.
                sys_time = item[1]
                sys_time = sys_time.split('"')[1].split(':')
                sys_time = float(sys_time[0]) * 3600 + float(sys_time[1]) * 60 + float(sys_time[2])
                
                # get frame id
                frame_id = item[5]
                frame_id = int(frame_id, 16)

                # get msg
                msg = item[9].split('|')[1].split(' ')[1:-1]
                msg = [ int(p, 16) for p in msg]
                # parse PDU from frame_id
                can_reader.parse_PDU(frame_id)

                if can_reader.PGN == PGN.SSI2.value:    # Slope Sensor Information 2
                    data = can_reader.parse_tilt(msg)

                elif can_reader.PGN == PGN.ARI.value:   # Angular Rate
                    data = can_reader.parse_gyro(msg)

                elif can_reader.PGN == PGN.ACCS.value:  # Acceleration Sensor
                    data = can_reader.parse_accel(msg)

                else: # unknown PGN msg
                    pass

            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))

if __name__ == '__main__':
    f = '/Users/songyang/Desktop/t/07061351_0001.csv'
    parse_can_tester_log(f)
