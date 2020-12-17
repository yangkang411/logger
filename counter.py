# -*- coding: utf-8 -*
"""

Created on 2020-7-7
@author: 
"""
import sys
import os

def batch_parse(log_files_directory):
    for root, dirs, files in os.walk(log_files_directory):
        for file in files:
            item = os.path.join(root, file)
            fmt = os.path.splitext(item)[-1]
            if fmt.lower() != '.txt':
                continue
            parse_can_tester_log(item)
    pass

def parse_can_tester_log(log_file):
    time_1st  = None  # 第一个时间戳
    time_2nd  = None  # 第二个时间戳
    time_last = None  # 上一个时间戳
    time_end  = None  # 最后一个时间戳
    tiem_start_idx = None
    time_end_idx = None

    # get 1st timestamp, last timestamp, total count of lines. 
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

                item = line.split('\t')
                # get time.
                sys_time = item[0]

                if idx == 2:
                    time_1st = sys_time
                else:
                    time_end = sys_time

                idx += 1
                line = f.readline()
            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))

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

                item = line.split('\t')
                sys_time = item[0] # get time.

                if time_2nd is None and time_1st != sys_time:
                    time_2nd = sys_time
                    tiem_start_idx = idx
                elif time_end != sys_time:
                    time_last = sys_time
                    time_end_idx = idx

                idx += 1
                line = f.readline()
            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))

    # print(time_1st, time_2nd, time_end, tiem_start_idx, time_end_idx)
    count = int((float(time_last) - float(time_2nd) + 0.1) * 100)
    lines = time_end_idx - tiem_start_idx + 1

    r = False
    if count == lines:
        r = True

    print(' start time (sec):{0} \n end time (sec):{1} \n predict count: {2} \n real count: {3}'.format(time_2nd, time_last, count, lines))

    if r:
        print('OK')
    else:
        print('NG!!!!!')


if __name__ == '__main__':
    batch_parse(sys.argv[1])
    # f = '/Users/songyang/Desktop/t'
    # parse_can_tester_log(f)
    # batch_parse(f)

# python3 counter.py '/Users/songyang/Desktop/t/07061351_0001_0001_81.txt'
