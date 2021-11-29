
# -*- coding: utf-8 -*
"""
Find LLA according to given data index.
Created on 2020-11-4
@author: Ocean
"""

import sys
import os
import threading
import time
import datetime
import math


def find_idx(nov_file, line_num):
    '''
    input: 
        nov_file: Novatel csv log file which has been aligned with sim.csv.
        line_num: data index in sim.csv divide 10 or 20.
    output:
        print infomation.

    '''
    # query Novatel info by given span_idx.
    with open(nov_file, 'r', encoding='utf-8') as f:
        idx = -1
        line = f.readline()
        while line:
            try:
                idx += 1
                if idx < int(line_num):
                    line = f.readline()
                    continue

                item = line.split(',')
                span_timestamp = item[0]
                day = span_timestamp.split('_')[0]
                span_time_str = span_timestamp.split('.')[0]
                span_ms = span_timestamp.split('.')[1]

                span_time_float = time.strptime(span_time_str, "%Y-%m-%d_%H:%M:%S")
                span_time_float = time.mktime(span_time_float) + float(span_ms)*0.001
                span_time_float += 8*3600 # align with UTC+8.
                # print(span_time_str, span_time_float)

                offset = 1;  # 后来log的Novatel数据中，增加了一列用于表示状态，比如'15826;INS_SOLUTION_GOOD',所以索引号需要做调整。
                lat = item[3 + offset]
                lon = item[4 + offset]
                alt = item[5 + offset]
                roll  = item[10 + offset]
                pitch = item[11 + offset]

                print('''Novatel info: 
                file_idx: {0}
                time: {1}
                lat: {2}
                lon: {3}
                alt: {4}
                roll: {5}
                pitch: {6} \n'''.format(idx, item[0], lat, lon, alt, roll, pitch))
                print('LLA: {0} {1} {2} \n'.format(lat, lon, alt))
                break
            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))


if __name__ == '__main__':
    # find_idx(sys.argv[1], sys.argv[2])

    nov_file = '/Users/songyang/project/analyze/drive_test/2021-2-7/data/novatel_20210207_153517.csv'
    line_num = '6000'
    find_idx(nov_file, line_num)


