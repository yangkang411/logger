# -*- coding: utf-8 -*
"""
Read and parse TV raw data.
Created on 2020-3-28
@author: Ocean
"""

import os
import sys
import datetime
import time
import math
import re

def convret(tv_raw_data_file):
    ''' 
    Read and parse TV raw data.
    And output csv file for simulation.

    Input: 
    
    Output: a csv file used for simulation, format as:
            accel_x in [g]
            accel_y in [g]
            accel_z in [g]
            gyro_x in [deg/sec]
            gyro_y in [deg/sec]
            gyro_z in [deg/sec]
            mag_x in [G]
            mag_y in [G]
            mag_z in [G]
            roll in [deg]
            pitch in [deg]
            yaw in [deg]
    '''
    if not os.path.exists('data/'):
        os.mkdir('data/')

    (filepath, tempfilename) = os.path.split(tv_raw_data_file)
    (shotname, extension) = os.path.splitext(tempfilename)

    log_file_name = os.path.join('data', '{0}_sim.csv'.format(shotname))
    print('Start logging:{0}'.format(log_file_name))
    log_file = open(log_file_name, 'w')

    header_num = 35
    with open(tv_raw_data_file, 'r') as f:
        idx = 0
        line = f.readline()

        while line:
            try:
                idx += 1
                if idx < header_num: # skip header
                    line = f.readline()
                    continue                    

                if idx % 100000 == 0:
                    print(idx)

                data = line.split('\t')
                if len(data) < 10: # avoid parse the last line '16-bit CheckSum=35277'
                    break
                time = data[0] # time stamp
                ax = float(data[3]) # mXAccel in [g]
                ay = float(data[4]) # mYAccel in [g]
                az = float(data[5]) # mZAccel in [g]
                gx = float(data[6]) # mXRate in [deg/sec]
                gy = float(data[7]) # mXRate in [deg/sec]
                gz = float(data[8]) # mXRate in [deg/sec]
                roll = float(data[9]) # [deg]
                pitch = float(data[10]) # [deg]
                yaw = float(data[11]) # [deg]
                if data[12] == 'NaN': # Mag data is NaN in MTLT TV test.
                    mx = 0
                    my = 0
                    mz = 0
                else:
                    mx = float(data[12]) # mXMag in [gauss]
                    my = float(data[13]) # mYMag in [gauss]
                    mz = float(data[14]) # mZMag in [gauss]
                temp = float(data[18]) # mXRateSensTemp

                s = '{0:f},{1:f},{2:f},{3:f},{4:f},{5:f},  \
                    {6:f},{7:f},{8:f},{9:f},{10:f},{11:f},{12:f}'  \
                    .format(ax, ay, az, gx, gy, gz,      \
                        mx, my, mz, roll, pitch, yaw, temp).replace(' ', '')

                log_file.write(s + '\n')
                log_file.flush()
                line = f.readline()

            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))
                line = f.readline()


if __name__ == '__main__':
    tv_raw_data_file = sys.argv[1]
    convret(tv_raw_data_file)

# '/Volumes/productionbackup/dmudata/dmu305/19XXXXXXXX/1903046146'