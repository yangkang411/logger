# -*- coding: utf-8 -*
"""
Parse Novatel ASCII log, and save [time,lla, velocity, roll, pitch] to csv log.
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


def parse_novatel_ASC_log(novatel_ref):
    '''
    Parse Novatel ASCII log, and save [time,lla, velocity, roll, pitch] to csv log.
    '''
    start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if not os.path.exists('data/'):
        os.mkdir('data/')
    file_dir = os.path.join('data', 'novatel_'+ start_time+'.csv')
    print('Start: {0}'.format(file_dir))
    ref_file = open(file_dir, 'w')
    header = 'Time,GPS_week,time(sec),lat(deg),lon(deg),alt(m),vel_N(m/s),vel_E(m/s),vel_U(m/s),vel_norm(m/s),roll(deg),pitch(deg),yaw(deg)'
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
                    longitude = item[12]# deg
                    altitude = item[13] # m
                    vel_N = float(item[15])     # North velocity (m/s)     NEU is left-handed coordinates!
                    vel_E = float(item[16])    # East velocity (m/s)
                    vel_U = float(item[17])    # Up velocity (m/s)
                    vel_norm = math.sqrt(vel_N * vel_N + vel_E * vel_E + vel_U * vel_U)
                    roll = item[18]     # deg
                    pitch = item[19]    # deg
                    yaw = item[20]      # deg

                    time_gps = gps.gpst2time(int(GPS_week), float(GPS_second))
                    time_utc = gps.gpst2utc(time_gps)
                    time = gps.time2epoch(time_utc)
                    time_stamp = time.strftime("%Y-%m-%d_%H:%M:%S.%f")[:-3]

                    str = '{0},{1},{2},{3},{4},{5},{6:f},{7:f},{8:f},{9:f},{10},{11},{12}\n'.  \
                        format(time_stamp, GPS_week, GPS_second, latitude,longitude,altitude,   \
                               vel_N,vel_E,vel_U,vel_norm,roll,pitch,yaw)

                    ref_file.write(str)
                    ref_file.flush()
                elif line.startswith('#RAWIMUSXA'):
                    pass
                else:
                    pass

                idx += 1
                line = f.readline()
                if idx % 10000 == 0:
                    print("[{0}]:line: {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idx))

            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))
            
def generate_vel_sim(file):
    '''
    Extract velocity info and generate velocity data for simulation.
    '''
    start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if not os.path.exists('data/'):
        os.mkdir('data/')
    file_dir = os.path.join('data', 'novatel_'+ start_time+'_velocity_sim'+'.csv')
    print('Start: {0}'.format(file_dir))
    ref_file = open(file_dir, 'w')
    header = 'odoUpdate,odoVelocity'
    ref_file.write(header + '\n')
    ref_file.flush()

    with open(file, 'r', encoding='utf-8') as f:
        idx = 1
        line = f.readline()
        while line:
            try:
                if idx == 1: # ignore the 1st line header 
                    idx += 1
                    line = f.readline()
                    continue

                item = line.split(',')
                vel_norm = float(item[9])
                str = '1,{0:f}\n'.format(vel_norm)
                ref_file.write(str)
                ref_file.flush()

                # expand velocity from 10Hz to 100/200 Hz, 
                for i in range(20-1):   # 100Hz: 10-1;   200Hz: 20-1
                    str = '0,0\n'
                    ref_file.write(str)
                ref_file.flush()
                
                idx += 1
                line = f.readline()
                if idx % 10000 == 0:
                    print("[{0}]:line: {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idx))

            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))
    pass

if __name__ == '__main__':
    parse_novatel_ASC_log(sys.argv[1])
    # generate_vel_sim(sys.argv[1])

    # f = '/Users/songyang/project/analyze/drive_test/2020-4-21/novatel_ref/novatel_CPT7-2020_04_21_15_20_37.ASC'
    # parse_novatel_ASC_log(f)

    # f = '/Users/songyang/project/code/github/logger/data/novatel_20200617_152310.csv'
    # generate_vel_sim(f)
