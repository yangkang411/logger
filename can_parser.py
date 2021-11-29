# coding: utf-8
"""
General CAN messages Parser.

Created on 2020-10-29
@author: Ocean

"""

import os
import sys
import math
from enum import Enum
import datetime
import struct


class PGNType(Enum):
    SSI2       = 61481   # Slope Sensor Information 2
    ARI        = 61482   # Angular Rate
    ACCS       = 61485   # Acceleration Sensor
    CCVS1      = 65265   # Cruise Control/Vehicle Speed 1, to get Wheel-Based Vehicle Speed
    GEAR       = 61445   # 'Transmission Selected Gear' in 'Electronic Transmission Controller' message.
    WSI        = 65215   # Wheel Speed Information   
    TACHOGRAPH = 65132   # Tachograph

class CarolaCANID(Enum):
    WS         = 0XAA   # Wheel speeds.
    GEAR       = 0X3BC  # Gear message.


class CANParser():
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

    def generate_PDU(self, Priority, PGN, SA):
        # PDU = Priority << 26 + PGN << 8 + SA
        PDU =  Priority * math.pow(2, 26) + PGN * math.pow(2, 8) + SA
        return int(PDU)

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
        if gear_unint == 251: # 0XFB
            print('gear park')
            pass
        else:
            gear_unint += offset
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

    def parse_wheel_speed_carola(self, msg):
        '''
        Parse WHEEL_SPEEDS info from Toyota Corolla.
        
        in: CAN msg
        out: in [km/h]
            WHEEL_SPEED_FR
            WHEEL_SPEED_FL
            WHEEL_SPEED_RR
            WHEEL_SPEED_RL
        
        dbc: MSB, unsigned
            BO_ 170 WHEEL_SPEEDS: 8 XXX
            SG_ WHEEL_SPEED_FR : 7|16@0+ (0.01,-67.67) [0|250] "kph" XXX
            SG_ WHEEL_SPEED_FL : 23|16@0+ (0.01,-67.67) [0|250] "kph" XXX
            SG_ WHEEL_SPEED_RR : 39|16@0+ (0.01,-67.67) [0|250] "kph" XXX
            SG_ WHEEL_SPEED_RL : 55
            |16@0+ (0.01,-67.67) [0|250] "kph" XXX
        '''
        offset = -67.67
        speed_fr = (msg[0] * 256 + msg[1]) * 0.01 + offset
        speed_fl = (msg[2] * 256 + msg[3]) * 0.01 + offset
        speed_rr = (msg[4] * 256 + msg[5]) * 0.01 + offset
        speed_rl = (msg[6] * 256 + msg[7]) * 0.01 + offset
        return (speed_fr, speed_fl, speed_rr, speed_rl)

    def parse_gear_carola(self, msg):
        '''
        Parse Gear info from Toyota Corolla.

        in: CAN msg
        out: Gear vaule

        dbc: MSB, unsigned
            SG_ Name : StartBit | Length @ ByteOrder SignedFlag (Factor,Offset) [Minimum | Maximum] "Unit" Receiver1,Receiver2
            BO_ 956 GEAR_PACKET: 8 XXX
            SG_ GEAR : 13|6@0+ (1,0) [0|63] "" XXX
            SG_ SPORT_ON : 3|1@0+ (1,0) [0|1] "" XXX

        meaning:
            Gear Value
            P     32
            R     16
            N     8
            D     0
        '''
        gear = msg[1]
        return (gear,)

    def parse_GPS_LLA(self, msg):
        '''
        Parse latitude or longitude or altitude info from SANY GPS CAN msg.
        
        in: CAN msg
        out: in [degree] if latitude or longitude, in [meter] if altitude.
        '''
        pack_fmt = '<1d'.format(8)
        len_fmt = '8B'
        b = struct.pack(len_fmt, *msg)
        d = struct.unpack(pack_fmt, b)
        return (d[0],)

    def parse_GPS_angle(self, msg):
        '''
        Parse yaw and slop info from SANY GPS CAN msg.
        
        in: CAN msg
        out: in [degree]
             yaw
             slop
        '''
        pack_fmt = '<2f'.format(8)
        len_fmt = '8B'
        b = struct.pack(len_fmt, *msg)
        d = struct.unpack(pack_fmt, b)
        return (d[0], d[1])

if __name__ == '__main__':    
    pass

