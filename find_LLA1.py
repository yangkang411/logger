
# -*- coding: utf-8 -*
"""
Find LLA according to given data index.
Created on 2020-4-16
@author: Ocean
"""

import sys
import os
import threading
import time
import datetime
import math


def test(query_idx):
    '''
    1. 根据截断后的 ref_roll 还原原始 Novatel idx
    2. 根据idx找出时间戳
    3. 在sim results中找到对应的时间戳和 idx。
    '''
    ########################################################## 
    # 4-16 drive-test
    # sim_file = '/Users/songyang/project/analyze/drive_test/2020-4-16/data/A1_20200416_150842_ttyUSB1_2043604047.csv'
    # nov_file = '/Users/songyang/project/analyze/drive_test/2020-4-16/novatel_ref/novatel_20200416_165432.csv'
    # span_offset = 252

    # 4-21 drive-test
    sim_file = '/Users/songyang/project/analyze/drive_test/2020-4-21/data/A1_20200421_152042_ttyUSB0_2043604047.csv'
    nov_file = '/Users/songyang/project/analyze/drive_test/2020-4-21/novatel_ref/novatel_20200421_163831.csv'
    span_offset = 0

    ##########################################################
    query_idx = int(query_idx)
    span_idx = query_idx + span_offset

    # query Novatel info by given span_idx.
    with open(nov_file, 'r', encoding='utf-8') as f:
        idx = 0
        line = f.readline()
        while line:
            try:
                idx += 1
                if idx == span_idx:
                    item = line.split(',')
                    span_timestamp = item[0]
                    day = span_timestamp.split('_')[0]
                    span_time_str = span_timestamp.split('.')[0]
                    span_ms = span_timestamp.split('.')[1]

                    span_time_float = time.strptime(span_time_str, "%Y-%m-%d_%H:%M:%S")
                    span_time_float = time.mktime(span_time_float) + float(span_ms)*0.001
                    span_time_float += 8*3600 # align with UTC+8.
                    # print(span_time_str, span_time_float)

                    lat = item[3]
                    lon = item[4]
                    alt = item[5]
                    roll  = item[6]
                    pitch = item[7]

                    print('''Novatel info: 
                    query_idx: {0}
                    file_idx: {1}
                    time: {2}
                    lat: {3}
                    lon: {4}
                    alt: {5}
                    roll: {6}
                    pitch: {7} \n'''.format(query_idx, span_idx, item[0], lat, lon, alt, roll, pitch))

                    print('LLA: {0} {1} {2} \n'.format(lat, lon, alt))

                    break
                line = f.readline()

            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))

    with open(sim_file, 'r', encoding='utf-8') as f:
        idx = 0
        # output = None
        line = f.readline()
        while line:
            try:
                idx += 1
                if idx == 1: # the 1st row is header.
                    line = f.readline()
                    continue

                item = line.split(',')
                sim_time_str = item[0]
                sim_ms = sim_time_str.split('_')[1]
                sim_time = sim_time_str.split('_')[0]
                sim_time_str = "{0} {1}".format(day, sim_time)
                sim_time_float = time.strptime(day+' '+sim_time, "%Y-%m-%d %H:%M:%S")
                sim_time_float = time.mktime(sim_time_float) + float(sim_ms)*0.001
                # print(sim_time_str, sim_time_float)

                if idx == 2:
                    sim_time_last = sim_time_float

                if span_time_float >= sim_time_last and span_time_float <= sim_time_float:
                    sim_file_idx = idx
                    sim_result_idx = idx - 1

                    print('''IMU info: 
                    data_idx: {0}
                    file_idx: {1}
                    time: {2}
                    roll: {3}
                    pitch: {4}'''.format(sim_result_idx, sim_file_idx, item[0], item[1], item[2]))

                    break
                else:
                    sim_time_last = sim_time_float

                line = f.readline()

            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))
    
def main():
    '''
    Find LLA according to the index of simulation results by similar timestamp.

    input:  
            simulation results file name;
            Novatel log file name;
            index of simulation results.

    output: (print in terminal)
            index of Novatel log.
            lat and log.
    '''
    sim_file = '/Users/songyang/project/analyze/drive_test/2020-4-16/data/A1_20200416_150842_ttyUSB1_2043604047.csv'
    nov_file = '/Users/songyang/project/analyze/drive_test/2020-4-16/novatel_ref/novatel_20200416_165432.csv'
    sim_idx = 13544
    print('query_idx: ', sim_idx, '\n')

    ########################################################## 
    # 4-16 drive-test
    start_idx = 106
    scale1 = 2  # 335 200hz --> 305 100hz
    scale2 = 10 # 305 100hz --> Novatel 10hz

    # # 335 align with 305
    # sim_idx = (sim_idx + 106) * scale1
    # # 335 align with Novatel
    sim_idx = (((sim_idx-1) * scale2 + 106) - 1 ) * scale1 
    print('sim_idx: ', sim_idx, '\n')
    ##########################################################
    
    with open(sim_file, 'r', encoding='utf-8') as f:
        idx = 0
        line = f.readline()
        while line:
            try:
                idx += 1                
                if idx == sim_idx + 1: # count header.
                    item = line.split(',')
                    sim_timestamp = item[0]
                    sim_ms = sim_timestamp.split('_')[1]
                    sim_time = sim_timestamp.split('_')[0]
                    print('IMU info: ', item, '\n')
                    break
                line = f.readline()

            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))

    with open(nov_file, 'r', encoding='utf-8') as f:
        idx = 0
        output = None
        line = f.readline()
        while line:
            try:
                idx += 1
                if idx == 1: # the 1st row is header.
                    line = f.readline()
                    continue

                item = line.split(',')
                span_time = item[0]
                span_ms = span_time.split('.')[1]
                span_time = span_time.split('.')[0].replace('_', ' ')
                span_time_float = time.strptime(span_time, "%Y-%m-%d %H:%M:%S")
                span_time_float = time.mktime(span_time_float) + float(span_ms)*0.001
                span_time_float += 8*3600 # align with UTC+8.
                # print(span_time_float)

                if idx == 2:
                    day = item[0].split('_')[0]
                    sim_time_str = "{0} {1}".format(day, sim_time)
                    sim_time_float = time.strptime(sim_time_str, "%Y-%m-%d %H:%M:%S")
                    sim_time_float = time.mktime(sim_time_float) + float(sim_ms)*0.001
                    span_time_last = span_time_float

                if sim_time_float >= span_time_last and sim_time_float <= span_time_float:
                    # index, lat, lon
                    output = '{0}   {1}   {2}'.format(idx, item[3], item[4])
                    print('Novate info: ', item, '\n')
                    break
                line = f.readline()

            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))
                
        print('input  [idx, time_str, time_float]: {0}   {1}   {2} \n'.format(sim_idx, sim_timestamp, sim_time_float))
        if output is not None:
            print('output [time_str, time_float, idx, lat, lon]: {0}   {1}   {2}\n'.format(sim_time_str, span_time_float, output))
        else:
            print('Can not find LLA!\n')


if __name__ == '__main__':
    test(sys.argv[1])
