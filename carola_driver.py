'''
Convert Carola velocity CAN message to standard J1939 CAN message.
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
from can_parser import PGNType, CANParser


class CarolaDriver:
    '''
        Parse Carola CAN message. 
        Convert velocity and gear message to standard J1939 CAN message.
    '''
    def __init__(self):
        self.cnt = 0
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

        self.can_parser = CANParser()
        self.create_log_files()
        self.lines = 0
        self.gear = 0
        self.last_speed = 0

    def msg_handler(self,msg):
        return

    def convert_speed_msg(self,msg):
        '''
            Convert 100Hz Carola speed message to 10Hz J1939 PGN odometer message.
        '''
        if msg.arbitration_id == 0XAA:
            self.cnt += 1
            # if self.cnt % 10 != 0: # 100Hz -> 10Hz
            #     return 

            # time = datetime.datetime.fromtimestamp(msg.timestamp)
            # print(time)

            # parse wheels speed from msg.
            (speed_fr, speed_fl, speed_rr, speed_rl) = self.can_parser.parse_wheel_speed_carola(msg.data)
            # print("speed:", speed_fr, speed_fl, speed_rr, speed_rl)

            # Test
            #if math.fabs(speed_fl - self.last_speed) > 1.0001:
            #    print(speed_fl - self.last_speed)
            #self.last_speed = speed_fl
            #return
            
            #### construct PGN-65215 id and data
            # SA CAN NOT be 0X80 which equal to MTLT's address.
            id = self.can_parser.generate_PDU(Priority = 6, PGN = 65215, SA = 0X88)
            
            offset = -7.8125 #km/h
            front_axle_speed = (speed_fr + speed_fl)/2
            front_left_wheel_speed  = int((speed_fl - front_axle_speed - offset) * 16 + 0.5)
            front_right_wheel_speed = int((speed_fr - front_axle_speed - offset) * 16 + 0.5)
            rear_left1_wheel_speed  = int((speed_rl - front_axle_speed - offset) * 16 + 0.5)
            rear_right1_wheel_speed = int((speed_rr - front_axle_speed - offset) * 16 + 0.5)
            rear_left2_wheel_speed  = rear_left1_wheel_speed
            rear_right2_wheel_speed = rear_right1_wheel_speed
            front_axle_speed = int(front_axle_speed * 256 + 0.5)
            
            data = []
            data.append(front_axle_speed % 256)
            data.append(int(front_axle_speed/256))
            data.append(front_left_wheel_speed)
            data.append(front_right_wheel_speed)
            data.append(rear_left1_wheel_speed)
            data.append(rear_right1_wheel_speed)
            data.append(rear_left2_wheel_speed)
            data.append(rear_right2_wheel_speed)

            m = can.Message(arbitration_id = id, data = data, extended_id = True)
            self.can0.send(m)
            # print(m)

            #### construct PGN-65265 id and data
            id = self.can_parser.generate_PDU(Priority = 6, PGN = 65265, SA = 0X88)
            speed = int((speed_rr + speed_rl)/2 * 256 + 0.5)
            data = [0] * 8
            data[1] = speed%256
            data[2] = int(speed/256)

            m = can.Message(arbitration_id = id, data = data, extended_id = True)
            self.can0.send(m)
            # print(m)

            ## save to log files.
            s = datetime.datetime.now().strftime('%H:%M:%S.%f')
            s += ',' + str(msg.arbitration_id)
            s += ','.join('{0:f}'.format(i) for i in (speed_fr, speed_fl, speed_rr, speed_rl))
            s += ',' + str(self.gear) + '\n'
            self.log_file_vel.write(s)
            self.log_file_vel.flush()
            self.log_file_all.write(s)
            self.log_file_all.flush()
            
            ##
            self.lines += 1
            if self.lines % 100 == 0:
                print("[{0}]:Log counter of: {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.lines))
                sys.stdout.flush()

    def convert_gear_msg(self,msg):
        if msg.arbitration_id == 0X3BC:
            # parse carola gear from msg.
            # Carola    ->    PGN61445
            #    P      ->    251
            #    R      ->    -1
            #    N      ->     0
            #    D      ->     1
            (gear,) = self.can_parser.parse_gear_carola(msg.data)
            self.gear = gear
            offset = -125
            if gear == 32: # P
                gear = 251
                pass
            elif gear == 16: # R
                gear = -1 - offset
                pass
            elif gear == 8: # N
                gear = 0 - offset
                pass
            elif gear == 0: # D
                gear = 1 - offset
                pass
            else:
                return

            data = [0] * 8
            data[3] = gear            
            #### construct PGN-61445 id and data
            id = self.can_parser.generate_PDU(Priority = 6, PGN = 61445, SA = 0X88)
            m = can.Message(arbitration_id = id, data = data, extended_id = True)
            self.can0.send(m)
            # print(m)
            ## save to log files.
            s = datetime.datetime.now().strftime('%H:%M:%S.%f')
            s += ',' + str(msg.arbitration_id)
            s += ',' + str(gear) + '\n'
            self.log_file_gear.write(s)
            self.log_file_gear.flush()
            self.log_file_all.write(s)
            self.log_file_all.flush()

    def handle_speed_msg(self):
        self.notifier.listeners.append(self.convert_speed_msg)

    def handle_gear_msg(self):
        self.notifier.listeners.append(self.convert_gear_msg)

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
        self.log_file_gear  = open(file_dir_gear, 'w')

        print('Start logging: {0}'.format(file_dir))
        header = 'time, ID, payload'.replace(' ', '')
        self.log_file_all.write(header + '\n')
        self.log_file_all.flush()        
        header = 'time, ID, speed_fr, speed_fl, speed_rr, speed_rl, gear'.replace(' ', '')
        self.log_file_vel.write(header + '\n')
        self.log_file_vel.flush()
        header = 'time, ID, gear'.replace(' ', '')
        self.log_file_gear.write(header + '\n')
        self.log_file_gear.flush()
        pass

    def close_log_files (self):
        self.log_file_all.close()
        self.log_file_vel.close()
        self.log_dir_gear.close()


if __name__ == "__main__":
    drv = CarolaDriver()
    drv.handle_speed_msg()
    drv.handle_gear_msg()

    while 1:
        time.sleep(1)
