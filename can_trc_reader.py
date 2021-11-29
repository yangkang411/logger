# coding: utf-8
"""
Parse CAN messages from Hyundai trc log file.

Created on 2021-6-27
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
                    if line.startswith(';'):
                        continue
                    if line == '':
                        continue

                    # (id, msg, tm) = self.getFields(line, 'Hyundai')
                    (id, msg, tm) = self.getFields(line, 'Hitachi')

                    id = int(id, 16)
                    msg = msg.split(' ')
                    msg = [ int(p, 16) for p in msg]
                    tm = tm.replace(' ', '')

                    (_Priority, _PGN, _PF, _PS, _SA) = can_parser.parse_PDU(id)
                    data = None
                    str = '{0},{1},{2},'.format(tm, hex(id), _PGN)

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

            return;
            g = 9.80665
            gyro  = np.array(gyro)
            gyro  = gyro.reshape(-1,3)
            gyro  = gyro[:, [1, 0, 2]] # Swap [X, Y].
            accel = np.array(accel)
            accel = accel.reshape(-1,3)
            accel = accel[:, [1, 0, 2]] # Swap [X, Y].
            accel = accel * [1, -1, -1] # NWU -> NED, m/s^2 -> g.
            accel = accel/g
            tilt  = np.array(tilt)
            tilt  = tilt.reshape(-1,2)

            n_accel = accel.shape[0]
            n_gyro  = gyro.shape[0]
            n_tilt  = tilt.shape[0]
            minsz = min(n_accel, n_gyro, n_tilt)
            if n_accel > minsz:
                accel = np.delete(accel, -1 * (n_accel - minsz), axis = 0) # 删除多余的行
            if n_gyro > minsz:
                gyro  = np.delete(gyro, -1 * (n_gyro - minsz), axis = 0)
            if n_tilt > minsz:
                tilt  = np.delete(tilt, -1 * (n_tilt - minsz), axis = 0)
            data  = np.hstack((accel, gyro, tilt))

            (filepath, tempfilename) = os.path.split(self.file)
            (shotname, extension) = os.path.splitext(tempfilename)
            file_name = os.path.join('data', '[{0}]_sim.csv'.format(shotname))
            header_line = 'acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z,roll,pitch'
            np.savetxt(file_name, data, header=header_line, delimiter=',', comments='')

            name = shotname.lstrip(string.digits) #删除最左侧的数字。
            name = name.lstrip('_')
            tmp = {}
            tmp[name] = data;    # [dps]
            mat_path = os.path.join('data', '[{0}].mat'.format(shotname))
            io.savemat(mat_path, tmp)

    def getFields(self, line, customer):
        if 'Hyundai' == customer:
            id = line[31:40]
            msg = line[48:71]
            tm = line[15:22]
        elif 'Hitachi' == customer:
            id = line[28:36]
            msg = line[41:64]
            tm = line[10:20]
        return (id, msg, tm)

def read_from_trc_logfile(file_name):
    '''
    '''
    trc_reader = TrcReader(file_name)
    trc_reader.read()
    trc_reader.close_log_files()

if __name__ == '__main__':
    # For single file
    file_name = '/Users/songyang/project/analyze/drive_test/Hitachi/2021-11-15/data/raw_data/SensorData_20211115/front3.trc'
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



###### Sample

# ;$FILEVERSION=1.3
# ;$STARTTIME=44363.6640065461
# ;
# ;   C:\Users\HHI\Desktop\210625_ACEINNA_송부용\210616_ACE_Last_10_10_10_Test10_filtered.trc
# ;   Start time: 2021-06-16 15:56:10.165.5
# ;   Generated by PCAN-Explorer v6.2.2.1986
# ;-------------------------------------------------------------------------------
# ;   Bus  Connection   Net Connection   Protocol  Bit rate
# ;   1    Connection1  250kbs@pcan_usb  CAN       250 kBit/s
# ;   2    Connection2  500kbs@pcan_usb  CAN       500 kBit/s
# ;-------------------------------------------------------------------------------
# ;   Message   Time    Bus  Type   ID    Reserved
# ;   Number    Offset  |    |      [hex] |   Data Length Code
# ;   |         [ms]    |    |      |     |   |    Data [hex] ...
# ;   |         |       |    |      |     |   |    |
# ;---+-- ------+------ +- --+-- ---+---- +- -+-- -+ -- -- -- -- -- -- --
#      1)         1.075 2  Rx    18FF5380 -  8    00 04 00 04 AA AA AA AA
#      2)         1.373 2  Rx    0CF02980 -  8    C7 AA 7E 5C 82 6B 44 06   # Roll/Pitch
#      3)         1.629 2  Rx    08F02D80 -  8    31 79 55 7D 0A 7D 80 06   # Accel
#      4)         1.885 2  Rx    0CF02A80 -  8    C9 81 EB 7C 79 79 00 06   # Gyro
#      5)        11.015 2  Rx    18FF5380 -  8    00 04 00 04 AA AA AA AA   # Software BIT status
#      6)        11.314 2  Rx    0CF02980 -  8    A0 AF 7E 4F 81 6B 44 06
#      7)        11.570 2  Rx    08F02D80 -  8    32 79 56 7D 0E 7D 80 06
#      8)        11.869 2  Rx    0CF02A80 -  8    C7 81 EB 7C 7A 79 00 06
#      9)        21.553 2  Rx    18FF5380 -  8    00 04 00 04 AA AA AA AA
#     10)        21.809 2  Rx    0CF02980 -  8    7D B4 7E 39 80 6B 44 06
#     11)        22.065 2  Rx    08F02D80 -  8    31 79 56 7D 0A 7D 80 06
#     12)        22.364 2  Rx    0CF02A80 -  8    CA 81 E7 7C 7A 79 00 06
#     13)        31.750 2  Rx    18FF5380 -  8    00 04 00 04 AA AA AA AA
#     14)        32.049 2  Rx    0CF02980 -  8    5C B9 7E 17 7F 6B 44 07
#     15)        32.305 2  Rx    08F02D80 -  8    2E 79 56 7D 09 7D 80 07
#     16)        32.603 2  Rx    0CF02A80 -  8    CB 81 E6 7C 79 79 00 07
#     17)        38.023 2  Tx    18EAFF80 -  3    53 FF 00
#     18)        41.094 2  Rx    18FF5380 -  8    00 04 00 04 AA AA AA AA
#     19)        41.350 2  Rx    0CF02980 -  8    5E BE 7E 78 7D 6B 44 06
#     20)        41.648 2  Rx    08F02D80 -  8    2C 79 56 7D 0C 7D 80 06