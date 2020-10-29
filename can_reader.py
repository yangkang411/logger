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
from enum import Enum
import datetime
from can.io.blf import BLFReader
from can.io.asc import ASCReader


class PGN(Enum):
    SSI2       = 61481   # Slope Sensor Information 2
    ARI        = 61482   # Angular Rate
    ACCS       = 61485   # Acceleration Sensor
    CCVS1      = 65265   # Cruise Control/Vehicle Speed 1, to get Wheel-Based Vehicle Speed
    GEAR       = 61445   # 'Transmission Selected Gear' in 'Electronic Transmission Controller' message.
    WSI        = 65215   # Wheel Speed Information   
    TACHOGRAPH = 65132   # Tachograph

class CanParser():
    def __init__(self):
        pass

    def parse_PDU(self, PDU):
        '''
        function: get Priority, PGN, PF, PS, SA info from PDU.

        in: int, PDU, eg 0x0cf029a2
        '''
        priority = (PDU >> 26) & 7  # 0b0111
        PF = (PDU >> 16) & 255      # 0b11111111
        PS = (PDU >> 8) & 255       # 0b11111111
        SA = PDU & 255              # 0b11111111

        if PF < 240:
            PGN = PF * 256
        else:
            PGN = PF * 256 + PS
        # print('{0},{1},{2},{3},{4},{5}'.format(hex(PDU), priority, PGN, PF, PS, SA))
        return (priority, PGN, PF, PS, SA)

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

    def parse_velocity1(self, msg):
        '''
        Parse CAN msg (PGN 65265) to get Wheel-Based Vehicle Speed. Speed of the vehicle as calculated from wheel or tailshaft speed.

        in: CAN msg
        out: Wheel-Based Vehicle Speed in [km/h]
        '''
        vel_unint = msg[1] + 256 * msg[2] 
        vel_km_perhr = vel_unint * (1/256.0)
        vel_m_persec = vel_km_perhr / 3.6
        # print('{0:3.2f}'.format(vel_km_perhr))
        return (vel_km_perhr,)

    def parse_velocity2(self, msg):
        '''
        Parse CAN msg (PGN 65215) to get Wheel Speed Information.

        in: CAN msg
        out: (front_axle_speed, front_left_wheel_speed, front_right_wheel_speed
        rear_left1_wheel_speed, rear_right1_wheel_speed, rear_left2_wheel_speed,rear_right2_wheel_speed)
        '''
        offset = -7.8125 #km/h
        # Front Axle Speed, the average speed of the two front wheels. range:[0, 250.996] km/h. 
        front_axle_speed        = (msg[0] + 256 * msg[1]) / 256.0
        # The speed of the front axle, left wheel speed, 
        front_left_wheel_speed  = msg[2] / 16 + offset + front_axle_speed
        # The speed of the front axle, right wheel speed, 
        front_right_wheel_speed = msg[3] / 16 + offset + front_axle_speed
        # The speed of the rear axle #1, left wheel speed, 
        rear_left1_wheel_speed  = msg[4] / 16 + offset + front_axle_speed
        # The speed of the rear axle #1, right wheel speed, 
        rear_right1_wheel_speed = msg[5] / 16 + offset + front_axle_speed
        # The speed of the rear axle #2, left wheel speed, 
        rear_left2_wheel_speed  = msg[6] / 16 + offset + front_axle_speed
        # The speed of the rear axle #2, right wheel speed, 
        rear_right2_wheel_speed = msg[7] / 16 + offset + front_axle_speed

        return(front_axle_speed, front_left_wheel_speed, front_right_wheel_speed, \
                rear_left1_wheel_speed, rear_right1_wheel_speed, \
                rear_left2_wheel_speed, rear_right2_wheel_speed)

    def parse_gear(self, msg):
        '''
        Parse CAN msg (PGN 61445) to get gear info.

        in: CAN msg
        out: gear value
            Range: -125 to +125, 
            negative values are reverse gears, 
            positive values are forward gears, 
            zero is neutral. 
            251 (0xFB) is park.
        '''
        offset = -125
        gear_unint = msg[3]
        if gear_unint == 251:
            print('gear park')
        gear_unint += offset
        # print(gear_unint)
        return (gear_unint,)

    def parse_tachograph(self, msg):
        '''
        function: get Tachograph infomation.

        in: CAN msg
        out: Direction indicator, Tachograph vehicle speed
        '''
        direction_indicator = msg[3]
        direction_indicator = direction_indicator >> 6  # get last 2 bits
        tachograph_vehicle_speed = (msg[6] + msg[7] * 256) / 256
        return (direction_indicator,tachograph_vehicle_speed)

class CanReader():
    '''
    Parse CAN messages from usual logging file of CAN communacation based on python-can.
    Now support blf and asc format file.    
    '''
    def __init__(self, file_name):
        self.file = file_name
        self.reader = None
        self.msg = None

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

    def parse_payload(self, msg):
        '''
        Parse CAN msg to get gyro/accel/tilt/velocity data.

        in: CAN msg
        '''
        can_parser = CanParser()
        (_Priority, _PGN, _PF, _PS, _SA) = can_parser.parse_PDU(msg.arbitration_id)

        data = None
        str = '{0:f},{1},{2},'.format(msg.timestamp, hex(msg.arbitration_id), _PGN)

        if _PGN == PGN.SSI2.value:    # Slope Sensor Information 2
            data = can_parser.parse_tilt(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_tilt.write(str )
            self.log_file_tilt.flush()
        elif _PGN == PGN.ARI.value:   # Angular Rate
            data = can_parser.parse_gyro(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_gyro.write(str )
            self.log_file_gyro.flush()
        elif _PGN == PGN.ACCS.value:  # Acceleration Sensor
            data = can_parser.parse_accel(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_accel.write(str )
            self.log_file_accel.flush()
        elif _PGN == PGN.CCVS1.value: # Cruise Control/Vehicle Speed 1
            data = can_parser.parse_velocity1(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_vel1.write(str )
            self.log_file_vel1.flush()
        elif _PGN == PGN.WSI.value: # Wheel Speed Information
            data = can_parser.parse_velocity2(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_file_vel2.write(str )
            self.log_file_vel2.flush()
        elif _PGN == PGN.GEAR.value:
            data = can_parser.parse_gear(msg.data)
            str += ','.join('{0:f}'.format(i) for i in data) + '\n'
            self.log_dir_gear.write(str )
            self.log_dir_gear.flush()            
            pass
        elif _PGN == PGN.TACHOGRAPH.value:
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


if __name__ == '__main__':
    # file_name = sys.argv[1]
    file_name = '/Users/songyang/project/analyze/drive_test/CNH/2020-5-27/data/C9-MY134_OBW1_B009_2020-05-22_15-47-02_25200kg_MS1_rural_motorway__begins_with_strong_uphill.blf'
    can_reader = CanReader(file_name)

    try:
        for item in can_reader.reader:
            # print(item)
            data = can_reader.parse_payload(item)
    except Exception as e:
        print(e)

