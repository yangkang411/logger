# coding: utf-8
"""
Parse CAN asc file based on python-can.
Created on 2020-6-4
@author: Ocean

ref: 
https://python-can.readthedocs.io/en/master/_modules/can/io/asc.html
"""

import os
import datetime
from can.io.asc import ASCReader

def parse_PDU(pdu):
    '''
    function: parse PDU and print Priority, PGN, PF, PS, SA info.

    in: int, PDU, eg 0x0cf029a2
    out: tuple, (priority, PGN, PF, PS, SA)
    '''
    priority = (pdu >> 26) & 7  # 0b0111
    PF = (pdu >> 16) & 255      # 0b11111111
    PS = (pdu >> 8) & 255       # 0b11111111
    SA = pdu & 255              # 0b11111111

    if PF < 240:
        PGN = PF * 256
    else:
        PGN = PF * 256 + PS

    return (priority, PGN, PF, PS, SA)

def parse_payload(pgn, msg):
    '''
    Parse CAN msg to get gyro/accel/tilt/velocity data.

    in: PGN, CAN msg
    out: tuple
    '''
    data = None
    if pgn == 61481: # Slope Sensor Information 2
        data = parse_tilt(msg)
    elif pgn == 61482: # Angular Rate
        data = parse_gyro(msg)
    elif pgn == 61485: # Acceleration Sensor
        data = parse_accel(msg)
    elif pgn == 65265: # Cruise Control/Vehicle Speed 1
        data = parse_velocity(msg)
    else: # unknown PGN msg
        pass
    
    return data

def parse_gyro(msg):
    '''
    Parse CAN msg to get Angular Rate data.

    in: CAN msg
    out: tuple, (gyro_x, gyro_y, gyro_z) in [deg/s]
    '''
    wx_uint = msg.data[0] + 256 * msg.data[1] 
    wy_uint = msg.data[2] + 256 * msg.data[3] 
    wz_uint =  msg.data[4] + 256 * msg.data[5] 
    wx = wx_uint * (1/128.0) - 250.0
    wy = wy_uint * (1/128.0) - 250.0
    wz = wz_uint * (1/128.0) - 250.0
    # print('WX: {0:3.2f} WY: {1:3.2f} WZ: {2:3.2f}'.format(wx,wy,wz))
    return (wx, wy, wz)

def parse_accel(msg):
    '''
    Parse CAN msg to get Acceleration Sensor data.

    in: CAN msg
    out: tuple, (accel_x, accel_y, accel_z) in [m/s²]
    '''

    ax_uint = msg.data[0] + 256 * msg.data[1] 
    ay_uint = msg.data[2] + 256 * msg.data[3] 
    az_uint =  msg.data[4] + 256 * msg.data[5] 
    ax = ax_uint * (0.01) - 320.0
    ay = ay_uint * (0.01) - 320.0
    az = az_uint * (0.01) - 320.0
    # print('AX: {0:3.2f} AY: {1:3.2f} AZ: {2:3.2f}'.format(ax,ay,az))
    return (ax, ay, az)

def parse_tilt(msg):
    '''
    Parse CAN msg to get tilt data.

    in: CAN msg
    out: tuple, (roll, pitch) in [deg]
    '''

    pitch_uint = msg.data[0] + 256 * msg.data[1] +  65536 * msg.data[2]
    roll_uint = msg.data[3] + 256 * msg.data[4] +  65536 * msg.data[5]
    pitch = pitch_uint * (1/32768) - 250.0
    roll = roll_uint * (1/32768) - 250.0
    # print('Roll: {0:3.2f} Pitch: {1:3.2f}'.format(roll,pitch))
    return (roll, pitch)

def parse_velocity(msg):
    '''
    Parse CAN msg to get Wheel-Based Vehicle Speed. Speed of the vehicle as calculated from wheel or tailshaft speed.

    in: CAN msg
    out: Wheel-Based Vehicle Speed in [km/h]
    '''
    vel_unint = msg.data[1] + 256 * msg.data[2] 
    vel_km_perhr = vel_unint * (1/256.0)
    vel_m_persec = vel_km_perhr / 3.6
    # print('{0:3.2f}'.format(vel_km_perhr))
    return (vel_km_perhr,)


if __name__ == '__main__':
    # asc_file = sys.argv[1]
    asc_file = '/Users/songyang/project/analyze/jd/data/PitchAndRollLog_EngineRunning_Full 6-03-2020 3-39-21 pm Messages File.asc'

    if not os.path.exists('data/'):
        os.mkdir('data/')

    start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    file_dir        = os.path.join('data', 'asc_' + start_time + '.csv')
    file_dir_gyro   = os.path.join('data', 'asc_' + start_time + '_gyro' + '.csv')
    file_dir_accel  = os.path.join('data', 'asc_' + start_time + '_accel' + '.csv')
    file_dir_tilt   = os.path.join('data', 'asc_' + start_time + '_tilt' + '.csv')
    file_dir_vel    = os.path.join('data', 'asc_' + start_time + '_vel' + '.csv')

    data_file_all   = open(file_dir, 'w')
    data_file_gyro  = open(file_dir_gyro, 'w')
    data_file_accel = open(file_dir_accel, 'w')
    data_file_tilt  = open(file_dir_tilt, 'w')
    data_file_vel   = open(file_dir_vel, 'w')

    print('Start logging:{0}'.format(file_dir))
    header = 'time, ID, PGN, payload'.replace(' ', '')
    data_file_all.write(header + '\n')
    data_file_all.flush()

    try:
        for item in ASCReader(asc_file):
            # print(item)

            (priority, PGN, PF, PS, SA) = parse_PDU(item.arbitration_id)
            # print('{0},{1},{2},{3},{4},{5}'.format(hex(item.arbitration_id), priority, PGN, PF, PS, SA))

            # get gyro/accel/tilt/velocity data.
            data = parse_payload(PGN, item)
            if data:
                str = '{0:f},{1},{2},'.format(item.timestamp, hex(item.arbitration_id),PGN)
                str += ','.join('{0:f}'.format(i) for i in data)

                data_file_all.write(str + '\n')
                data_file_all.flush()

                if PGN == 61481: # Slope Sensor Information 2
                    data_file_tilt.write(str + '\n')
                    data_file_tilt.flush()
                elif PGN == 61482: # Angular Rate
                    data_file_gyro.write(str + '\n')
                    data_file_gyro.flush()
                elif PGN == 61485: # Acceleration Sensor
                    data_file_accel.write(str + '\n')
                    data_file_accel.flush()
                elif PGN == 65265: # Cruise Control/Vehicle Speed 1
                    data_file_vel.write(str + '\n')
                    data_file_vel.flush()
                else: # unknown PGN msg
                    pass
    except Exception as e:
        print(e)

