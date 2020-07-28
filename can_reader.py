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
"""

import os
from enum import Enum
import datetime
from can.io.blf import BLFReader
from can.io.asc import ASCReader


class PGN(Enum):
    SSI2  = 61481   # Slope Sensor Information 2
    ARI   = 61482   # Angular Rate
    ACCS  = 61485   # Acceleration Sensor
    CCVS1 = 65265   # Cruise Control/Vehicle Speed 1, to get Wheel-Based Vehicle Speed


class CanReader():
    '''
    Parse CAN messages from usual logging file of CAN communacation based on python-can.
    Now support blf and asc format file.    
    '''
    def __init__(self, file_name):
        self.file = file_name
        self.reader = None
        self.msg = None
        self.priority = None
        self.PDU = None
        self.PGN = None
        self.PF = None
        self.PS = None
        self.SA = None
        self.PGN = None
        self.PGN = None

        if file_name is not None:
            self.reader_factory()
            self.create_log_files ()
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
        file_dir_vel    = os.path.join('data', prefix + start_time + '_vel' + '.csv')

        self.log_file_all   = open(file_dir, 'w')
        self.log_file_gyro  = open(file_dir_gyro, 'w')
        self.log_file_accel = open(file_dir_accel, 'w')
        self.log_file_tilt  = open(file_dir_tilt, 'w')
        self.log_file_vel   = open(file_dir_vel, 'w')

        print('Start logging: {0}'.format(file_dir))
        header = 'time, ID, PGN, payload'.replace(' ', '')
        self.log_file_all.write(header + '\n')
        self.log_file_all.flush()        
        pass

    def parse_PDU(self, PDU):
        '''
        function: get Priority, PGN, PF, PS, SA info from PDU.

        in: int, PDU, eg 0x0cf029a2
        '''
        self.PDU = PDU
        self.priority = (self.PDU >> 26) & 7  # 0b0111
        self.PF = (self.PDU >> 16) & 255      # 0b11111111
        self.PS = (self.PDU >> 8) & 255       # 0b11111111
        self.SA = self.PDU & 255              # 0b11111111

        if self.PF < 240:
            self.PGN = self.PF * 256
        else:
            self.PGN = self.PF * 256 + self.PS
        # print('{0},{1},{2},{3},{4},{5}'.format(hex(PDU), self.priority, self.PGN, self.PF, self.PS, self.SA))

    def parse_payload(self, msg):
        '''
        Parse CAN msg to get gyro/accel/tilt/velocity data.

        in: CAN msg
        '''
        self.parse_PDU(msg.arbitration_id)

        data = None
        str = '{0:f},{1},{2},'.format(msg.timestamp, hex(msg.arbitration_id), self.PGN)

        if self.PGN == PGN.SSI2.value:    # Slope Sensor Information 2
            data = self.parse_tilt(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_tilt.write(str )
            self.log_file_tilt.flush()
        elif self.PGN == PGN.ARI.value:   # Angular Rate
            data = self.parse_gyro(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_gyro.write(str )
            self.log_file_gyro.flush()
        elif self.PGN == PGN.ACCS.value:  # Acceleration Sensor
            data = self.parse_accel(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_accel.write(str )
            self.log_file_accel.flush()
        elif self.PGN == PGN.CCVS1.value: # Cruise Control/Vehicle Speed 1
            data = self.parse_velocity(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_vel.write(str )
            self.log_file_vel.flush()
        else: # unknown PGN msg
            pass
        
        if data is not None:
            self.log_file_all.write(str)
            self.log_file_all.flush()
        pass

    def parse_gyro(self, msg):
        '''
        Parse CAN msg to get Angular Rate data.

        in: CAN msg
        out: tuple, (gyro_x, gyro_y, gyro_z) in [deg/s]
        '''
        wx_uint = msg[0] + 256 * msg[1] 
        wy_uint = msg[2] + 256 * msg[3] 
        wz_uint =  msg[4] + 256 * msg[5] 
        wx = wx_uint * (1/128.0) - 250.0
        wy = wy_uint * (1/128.0) - 250.0
        wz = wz_uint * (1/128.0) - 250.0
        # print('WX: {0:3.2f} WY: {1:3.2f} WZ: {2:3.2f}'.format(wx,wy,wz))
        return (wx, wy, wz)

    def parse_accel(self, msg):
        '''
        Parse CAN msg to get Acceleration Sensor data.

        in: CAN msg
        out: tuple, (accel_x, accel_y, accel_z) in [m/s²]
        '''
        ax_uint = msg[0] + 256 * msg[1] 
        ay_uint = msg[2] + 256 * msg[3] 
        az_uint =  msg[4] + 256 * msg[5] 
        ax = ax_uint * (0.01) - 320.0
        ay = ay_uint * (0.01) - 320.0
        az = az_uint * (0.01) - 320.0
        # print('AX: {0:3.2f} AY: {1:3.2f} AZ: {2:3.2f}'.format(ax,ay,az))
        return (ax, ay, az)

    def parse_tilt(self, msg):
        '''
        Parse CAN msg to get tilt data.

        in: CAN msg
        out: tuple, (roll, pitch) in [deg]
        '''
        pitch_uint = msg[0] + 256 * msg[1] +  65536 * msg[2]
        roll_uint = msg[3] + 256 * msg[4] +  65536 * msg[5]
        pitch = pitch_uint * (1/32768) - 250.0
        roll = roll_uint * (1/32768) - 250.0
        # print('Roll: {0:3.2f} Pitch: {1:3.2f}'.format(roll,pitch))
        return (roll, pitch)

    def parse_velocity(self, msg):
        '''
        Parse CAN msg to get Wheel-Based Vehicle Speed. Speed of the vehicle as calculated from wheel or tailshaft speed.

        in: CAN msg
        out: Wheel-Based Vehicle Speed in [km/h]
        '''
        vel_unint = msg[1] + 256 * msg[2] 
        vel_km_perhr = vel_unint * (1/256.0)
        vel_m_persec = vel_km_perhr / 3.6
        # print('{0:3.2f}'.format(vel_km_perhr))
        return (vel_km_perhr,)


if __name__ == '__main__':
    file_name = sys.argv[1]
    can_reader = CanReader(file_name)

    try:
        for item in can_reader.reader:
            # print(item)
            ##get gyro/accel/tilt/velocity data.
            data = can_reader.parse_payload(item)
    except Exception as e:
        print(e)

