'''
Receive and parse CAN message.
Requires PI2/3/4 and Waveshare Tech PiCAN board 'RS485 CAN HAT'
@author: Ocean
'''

import os
import sys
import math
import time
import datetime
import can
import threading
import time
from can.protocols import j1939
from can_parser import PGNType, CarolaCANID, CANParser


class CANReceiver:
    '''
        Receive and parse standard J1939 CAN message.
    '''
    def __init__(self):
        ## close can0
        os.system('sudo ifconfig can0 down')
        ## set bitrate of can0
        os.system('sudo ip link set can0 type can bitrate 500000')
        ## open can0
        os.system('sudo ifconfig can0 up')
        # os.system('sudo /sbin/ip link set can0 up type can bitrate 250000')
        ## show details can0 for debug.
        # os.system('sudo ip -details link show can0')

        if 0:
            ## set up CAN Bus of J1939
            self.bus = j1939.Bus(channel='can0', bustype='socketcan_native')
            # set up Notifier
            self.notifier = can.Notifier(self.bus, [self.msg_handler])
        else:
            # set up can interface.
            self.can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes')# socketcan_native socketcan_ctypes
            ## set up Notifier
            self.notifier = can.Notifier(self.can0, [self.msg_handler])

        self.create_log_files()
        self.can_parser = CANParser()
        self.last_speed_65215 = 0
        self.last_gear = 0
        self.idx = 0

    def msg_handler(self,msg):
        self.idx += 1
        (_Priority, _PGN, _PF, _PS, _SA) = self.can_parser.parse_PDU(msg.arbitration_id)
        
        if msg.arbitration_id == CarolaCANID.WS.value:      # Carola wheel speed.
            self.handle_Carola_wheel_speed(msg)
            pass
        elif msg.arbitration_id == CarolaCANID.GEAR.value:  # Carola Gear message.
            self.handle_Carola_gear(msg)
            pass
        elif _PGN == PGNType.WSI.value:               # PGN 65215 Wheel speed message.
            self.handle_J1939_WSI(msg)
            pass
        elif _PGN == PGNType.CCVS1.value:             # PGN 65265 Wheel speed message.
            self.handle_J1939_CCVS1(msg)
            pass
        elif _PGN == PGNType.GEAR.value:              # PGN 61445 Gear message.
            self.handle_J1939_gear(msg)
            pass
        else:
            pass
        pass

    def handle_Carola_wheel_speed(self,msg):    # Carola wheel speed.
        '''
            
        '''
        str = '{0:f},'.format(msg.timestamp)
        data = self.can_parser.parse_wheel_speed_carola(msg.data)
        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
        self.log_file_carola_vel.write(str )
        self.log_file_carola_vel.flush()

        # Test
        (speed_fr, speed_fl, speed_rr, speed_rl) = data
        pass

    def handle_Carola_gear(self,msg):    # Carola Gear message.
        '''
            
        '''
        str = '{0:f},'.format(msg.timestamp)
        data = self.can_parser.parse_gear_carola(msg.data)
        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
        self.log_file_carola_gear.write(str )
        self.log_file_carola_gear.flush()

        # Test
        (gear,) = data
        pass

    def handle_J1939_WSI(self,msg):    # PGN 65215
        '''
            
        '''
        str = '{0:f},'.format(msg.timestamp)
        data = self.can_parser.parse_velocity2(msg.data)
        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
        self.log_file_65215_vel.write(str )
        self.log_file_65215_vel.flush()

        # Test
        (front_axle_speed, front_left_wheel_speed, front_right_wheel_speed, \
        rear_left1_wheel_speed, rear_right1_wheel_speed, \
        rear_left2_wheel_speed, rear_right2_wheel_speed) = data
        if math.fabs(rear_left1_wheel_speed - self.last_speed_65215) > 1.0001:
            print(rear_left1_wheel_speed - self.last_speed_65215)
        self.last_speed_65215 = rear_left1_wheel_speed

        pass

    def handle_J1939_CCVS1(self,msg):    # PGN 65265
        '''
            
        '''
        str = '{0:f},'.format(msg.timestamp)
        data = self.can_parser.parse_velocity1(msg.data)
        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
        self.log_file_65265_vel.write(str )
        self.log_file_65265_vel.flush()
        pass

    def handle_J1939_gear(self,msg):    # PGN 61445
        '''

        '''
        str = '{0:f},'.format(msg.timestamp)
        data = self.can_parser.parse_gear(msg.data)
        str += ','.join('{0:f}'.format(i) for i in data) + '\n'
        self.log_file_61445_gear.write(str )
        self.log_file_61445_gear.flush()
        pass

    def create_log_files (self):
        '''
        create log files.
        '''
        if not os.path.exists('data/'):
            os.mkdir('data/')
        start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        # file_dir               = os.path.join('data', start_time + '.csv')
        file_dir_carola_vel    = os.path.join('data', start_time + '_carola_vel' + '.csv')
        file_dir_carola_gear   = os.path.join('data', start_time + '_carola_gear' + '.csv')
        file_dir_65215_vel     = os.path.join('data', start_time + '_65215_vel' + '.csv')
        file_dir_65265_vel     = os.path.join('data', start_time + '_65265_vel' + '.csv')
        file_dir_61445_gear    = os.path.join('data', start_time + '_61445_gear' + '.csv')

        # self.log_file_all   = open(file_dir, 'w')
        self.log_file_carola_vel   = open(file_dir_carola_vel, 'w')
        self.log_file_carola_gear  = open(file_dir_carola_gear, 'w')
        self.log_file_65215_vel    = open(file_dir_65215_vel, 'w')
        self.log_file_65265_vel    = open(file_dir_65265_vel, 'w')
        self.log_file_61445_gear   = open(file_dir_61445_gear, 'w')

        # print('Start logging: {0}'.format(file_dir))
        # header = 'time, payload'.replace(' ', '')
        # self.log_file_all.write(header + '\n')
        # self.log_file_all.flush()

        header = 'time, speed_fr, speed_fl, speed_rr, speed_rl, gear'.replace(' ', '')
        self.log_file_carola_vel.write(header + '\n')
        self.log_file_carola_vel.flush()

        header = 'time, gear'.replace(' ', '')
        self.log_file_carola_gear.write(header + '\n')
        self.log_file_carola_gear.flush()

        header = 'time, speed_fa, speed_fl, speed_fr, speed_rl1, speed_rr1, speed_rl2, speed_rr2, gear'.replace(' ', '')
        self.log_file_65215_vel.write(header + '\n')
        self.log_file_65215_vel.flush()

        header = 'time, speed, gear'.replace(' ', '')
        self.log_file_65265_vel.write(header + '\n')
        self.log_file_65265_vel.flush()

        header = 'time, gear'.replace(' ', '')
        self.log_file_61445_gear.write(header + '\n')
        self.log_file_61445_gear.flush()

        pass

    def close_log_files (self):
        # self.log_file_all.close()
        self.log_file_carola_vel.close()
        self.log_file_carola_gear.close()
        self.log_file_65215_vel.close()
        self.log_file_65265_vel.close()
        self.log_file_61445_gear.close()


if __name__ == "__main__":
    receiver = CANReceiver()

    while 1:
        time.sleep(1)
