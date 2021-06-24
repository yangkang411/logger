# coding: utf-8
"""
Parse CAN messages from usual logging file of CAN communacation based on python-can.
Now support blf and asc format file.

Created on 2020-6-13
@author: Ocean

ref: 
https://python-can.readthedocs.io/en/master/_modules/can/io/asc.html
https://python-can.readthedocs.io/en/master/_modules/can/io/blf.html
https://www.javaroad.cn/questions/25895

There are 2 ways to install python-can:
1. pip install python-can
2. Installing python-can in development mode:
    git clone https://github.com/hardbyte/python-can.git
    cd python-can
    python3 setup.py develop
"""

import os
import sys
import datetime
from can.io.blf import BLFReader
from can.io.asc import ASCReader
from can_parser import PGNType, CANParser

class CanReader():
    '''
    Parse CAN messages from usual logging file of CAN communacation based on python-can.
    Now support blf and asc format file.    
    '''
    def __init__(self, file_name):
        self.file = file_name
        self.reader = None
        self.msg = None

        self.log_file_all = None
        self.log_file_gyro = None
        self.log_file_accel = None
        self.log_file_tilt = None
        self.log_file_vel1 = None
        self.log_file_vel2 = None
        self.log_dir_gear = None
        self.log_dir_tacho = None

        if file_name is not None:
            self.reader_factory()
            self.create_log_files()
        pass
    
    def reader_factory(self):
        '''
        Determine reader type.
        '''
        (filepath, tempfilename) = os.path.split(self.file)
        (shotname, extension) = os.path.splitext(tempfilename)
        if extension.lower() == '.asc':
            self.reader = ASCReader(self.file)
        elif extension.lower() == '.blf':
            self.reader = BLFReader(self.file)
        else:
            raise Exception("Invalid logging file! It should be a .asc or .blf file.")            
        pass
 
    def create_log_files (self):
        '''
        create log files.
        '''
        if not os.path.exists('data/'):
            os.mkdir('data/')
        start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if isinstance(self.reader, ASCReader):
            prefix = 'asc_'
        elif isinstance(self.reader, BLFReader):
            prefix = 'blf_'
        else:
            raise Exception("Invalid logging file! It should be a .asc or .blf file.")            
        pass

        file_dir        = os.path.join('data', prefix + start_time + '.csv')
        file_dir_gyro   = os.path.join('data', prefix + start_time + '_gyro' + '.csv')
        file_dir_accel  = os.path.join('data', prefix + start_time + '_accel' + '.csv')
        file_dir_tilt   = os.path.join('data', prefix + start_time + '_tilt' + '.csv')
        file_dir_vel1   = os.path.join('data', prefix + start_time + '_vel1' + '.csv')
        file_dir_vel2   = os.path.join('data', prefix + start_time + '_vel2' + '.csv')
        file_dir_gear   = os.path.join('data', prefix + start_time + '_gear' + '.csv')
        file_dir_tacho  = os.path.join('data', prefix + start_time + '_tachograph' + '.csv')

        self.log_file_all   = open(file_dir, 'w')
        self.log_file_gyro  = open(file_dir_gyro, 'w')
        self.log_file_accel = open(file_dir_accel, 'w')
        self.log_file_tilt  = open(file_dir_tilt, 'w')
        self.log_file_vel1  = open(file_dir_vel1, 'w')
        self.log_file_vel2  = open(file_dir_vel2, 'w')
        self.log_dir_gear   = open(file_dir_gear, 'w')
        self.log_dir_tacho   = open(file_dir_tacho, 'w')

        print('Start logging: {0}'.format(file_dir))
        header = 'time, ID, PGN, payload'.replace(' ', '')
        self.log_file_all.write(header + '\n')
        self.log_file_all.flush()        
        pass

    def close_log_files (self):
        self.log_file_all.close()
        self.log_file_gyro.close()
        self.log_file_accel.close()
        self.log_file_tilt.close()
        self.log_file_vel1.close()
        self.log_file_vel2.close()
        self.log_dir_gear.close()
        self.log_dir_tacho.close()
        
    def parse_payload(self, msg):
        '''
        Parse CAN msg to get gyro/accel/tilt/velocity data.

        in: CAN msg
        '''
        can_parser = CANParser()
        (_Priority, _PGN, _PF, _PS, _SA) = can_parser.parse_PDU(msg.arbitration_id)

        data = None
        str = '{0:f},{1},{2},'.format(msg.timestamp, hex(msg.arbitration_id), _PGN)

        if _PGN == PGNType.SSI2.value:    # Slope Sensor Information 2
            data = can_parser.parse_tilt(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_tilt.write(str )
            self.log_file_tilt.flush()
        elif _PGN == PGNType.ARI.value:   # Angular Rate
            data = can_parser.parse_gyro(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_gyro.write(str )
            self.log_file_gyro.flush()
        elif _PGN == PGNType.ACCS.value:  # Acceleration Sensor
            data = can_parser.parse_accel(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_accel.write(str )
            self.log_file_accel.flush()
        elif _PGN == PGNType.CCVS1.value: # Cruise Control/Vehicle Speed 1
            data = can_parser.parse_velocity1(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_vel1.write(str )
            self.log_file_vel1.flush()
        elif _PGN == PGNType.WSI.value: # Wheel Speed Information
            data = can_parser.parse_velocity2(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_vel2.write(str )
            self.log_file_vel2.flush()
        elif _PGN == PGNType.GEAR.value:
            data = can_parser.parse_gear(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_dir_gear.write(str )
            self.log_dir_gear.flush()            
            pass
        elif _PGN == PGNType.TACHOGRAPH.value:
            data = can_parser.parse_tachograph(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_dir_tacho.write(str )
            self.log_dir_tacho.flush()            
            pass
        else: # unknown PGN msg
            pass
        
        if data is not None:
            self.log_file_all.write(str)
            self.log_file_all.flush()
        pass

class CANTestLogReader():
    '''
    Parse CAN messages from CANTestLog.
    '''
    def __init__(self, file_name):
        self.file = file_name
        self.gear = 0
        self.log_file_all = None
        self.log_file_vel = None
        self.log_dir_gear = None
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

        file_dir        = os.path.join('data', start_time + '.csv')
        file_dir_vel    = os.path.join('data', start_time + '_vel' + '.csv')
        file_dir_gear   = os.path.join('data', start_time + '_gear' + '.csv')
        self.log_file_all   = open(file_dir, 'w')
        self.log_file_vel   = open(file_dir_vel, 'w')
        self.log_dir_gear   = open(file_dir_gear, 'w')

        print('Start logging: {0}'.format(file_dir))
        header = 'time, time(sec), ID, payload'.replace(' ', '')
        self.log_file_all.write(header + '\n')
        self.log_file_all.flush()
        header = 'time, time(sec), ID, payload'.replace(' ', '')
        self.log_file_vel.write(header + '\n')
        self.log_file_vel.flush()        
        self.log_dir_gear.write(header + '\n')
        self.log_dir_gear.flush()        
        pass

    def close_log_files (self):
        self.log_file_all.close()
        self.log_file_vel.close()
        self.log_dir_gear.close()

    def read(self,):
        can_parser = CANParser()
        with open(self.file, 'r', encoding='utf-8') as f:
            idx = 0
            line = f.readline()
            while line:
                try:
                    idx += 1
                    # ignore the first line header.
                    if idx == 1:
                        line = f.readline()
                        continue
                    
                    item = line.split(',')
                    # get system time.
                    sys_time = item[2]
                    sys_time = sys_time.split(':')
                    second = sys_time[2].split('.')
                    sys_time = float(sys_time[0]) * 3600 + float(sys_time[1]) * 60 + float(second[0]) + float(second[1])/1e3 + float(second[2])/1e6
                    
                    # get frame id
                    id = item[3]
                    id = int(id, 16)

                    # # get msg
                    msg = item[7].split(' ')[0:-1]
                    msg = [ int(p, 16) for p in msg]

                    data = None
                    s = '{0},{1},{2},'.format(item[2],sys_time,id)
                    if id == 0XAA:  # 170
                        data = can_parser.parse_wheel_speed_carola(msg)
                        s += ','.join('{0:f}'.format(i) for i in data)
                        s += ',' + str(self.gear) + '\n'
                        self.log_file_vel.write(s )
                        self.log_file_vel.flush()
                        # print(speed_fr, speed_fl, speed_rr, speed_rl) 
                    elif id == 0X3BC:  # 956
                        data = can_parser.parse_gear_carola(msg)
                        s += ','.join('{0:d}'.format(i) for i in data) + '\n'
                        self.log_dir_gear.write(s )
                        self.log_dir_gear.flush()
                        self.gear = data[0]
                        # print(data)
                    else: # unknown id
                        pass

                    if data is not None:
                        self.log_file_all.write(s)
                        self.log_file_all.flush()
                    pass

                    line = f.readline()

                except Exception as e:
                    print('Error at line {0} :{1}'.format(idx,e))


def read_from_blf_and_asc(file_name):
    can_reader = CanReader(file_name)
    try:
        for item in can_reader.reader:
            # print(item)
            data = can_reader.parse_payload(item)
        can_reader.close_log_files()
    except Exception as e:
        print(e)

def read_from_CAN_test(file_name):
    '''
    Read from CANTest Log file.
        Index,Direction,Timesteamp,ID,Format,Type,Length,Data,
        0,Receive,15:57:03.554.0,0x000001aa,Standard,Data,0x06,00 00 00 00 00 B1 ,
        495,Receive,15:57:04.044.0,0x000003bc,Standard,Data,0x08,00 20 00 00 00 00 00 00 ,
    '''
    can_reader = CANTestLogReader(file_name)
    can_reader.read()
    can_reader.close_log_files()

def split(file_name):
    '''
    If there are several units on CAN bus, <asc_20210623_141100_accel.csv> will contain accel data of 
    serveral units, for example, in blow log, there are 4 units in CAN bus and get accel data from 
    4 different units.
    This function is used to split <asc_20210623_141100_accel.csv> to 4 csv file, which only contains 1 
    unit accel data.

    time,id,PGN,acc_x,acc_y,acc_z
    2400.002477,0x8f02d80,61485,-7.360000,0.030000,6.540000
    2400.005934,0x8f02d81,61485,-0.150000,0.060000,9.820000
    2400.006486,0x8f02d82,61485,9.700000,0.100000,-1.380000
    2400.007036,0x8f02d83,61485,-3.890000,-0.090000,-8.990000
    '''
    address = {}  # {'address_id' : log_file}

    with open(file_name, 'r', encoding='utf-8') as f:
        idx = -1
        line = f.readline()

        (filepath, tempfilename) = os.path.split(file_name)
        (shotname, extension) = os.path.splitext(tempfilename)

        while line:
            try:
                idx += 1
                item = line.split(',')
                add  = item[1]
                if add not in address:
                    log_file = os.path.join('data', shotname + '_' + add + '.csv')
                    address[add] = open(log_file, 'w')

                address[add].write(line)
                line = f.readline()
            except Exception as e:
                print('Error at line {0} :{1}'.format(idx,e))    
    pass

if __name__ == '__main__':
    # file_name = sys.argv[1]
    # file_name = '/Users/songyang/project/analyze/drive_test/Hitachi/2021-6-23/data/raw_data/Hitachi_data/DATA2_ACEINNA_Case3_2400-2560.asc'
    # read_from_blf_and_asc(file_name)

    # Read and parse CAN-Test csv log.
    # file_name = '/Users/songyang/project/code/github/logger/data/data_2020-11-30/Carola_CAN/2020-11-30/can_log.csv'
    # read_from_CAN_test(file_name)

    file_name = './data/asc_20210623_151949_tilt.csv'
    split(file_name)



