# -*- coding: utf-8 -*
"""
Parse Novatel ASCII log, and save [time,lla, roll, pitch] to csv log.
Created on 2020-3-12
@author: Ocean
"""

import sys
import os
import threading
import datetime
import time
import operator
import struct
import glob
import math
import json
import collections
from tqdm import tqdm
import gps


def main():
    '''main'''
    novatel_ref = r"/Users/songyang/project/analyze/drive_test/2020-3-16/novatel_ref/novatel_CPT7-2020_03_16_13_36_48.ASC"

    start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if not os.path.exists('data/'):
        os.mkdir('data/')
    file_dir = os.path.join('data', 'novatel_'+ start_time+'.csv')
    print('Start: {0}'.format(file_dir))
    ref_file = open(file_dir, 'w')
    header = 'Time,GPS_week,time(sec),lat(deg),lon(deg),alt(m),roll(deg),pitch(deg)'
    ref_file.write(header + '\n')
    ref_file.flush()

    with open(novatel_ref, 'r', encoding='utf-8') as f:
        idx = 1
        line = f.readline()
        while line:
            try:
                if line.startswith('#INSPVAXA'):
                    item = line.split(',')
                    GPS_week = item[5]
                    GPS_second = item[6]
                    latitude = item[11] # deg
                    longitude = item[12] # deg
                    altitude = item[13] # m
                    roll = item[18]  # deg
                    pitch = item[19] # deg

                    time_gps = gps.gpst2time(int(GPS_week), float(GPS_second))
                    time_utc = gps.gpst2utc(time_gps)
                    time = gps.time2epoch(time_utc)
                    time_stamp = time.strftime("%Y-%m-%d_%H:%M:%S.%f")[:-3]

                    str = '{0},{1},{2},{3},{4},{5},{6},{7}\n'.format(time_stamp, GPS_week, GPS_second,latitude,longitude,altitude,roll,pitch)
                    ref_file.write(str)
                    ref_file.flush()
                elif line.startswith('#RAWIMUSXA'):
                    pass
                else:
                    pass

                idx += 1
                line = f.readline()
                if idx % 1000 == 0:
                    print("[{0}]:line: {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idx))

            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))
            

if __name__ == '__main__':
    main()
