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
import numpy as np

from can.protocols import j1939
from can_parser import PGNType, CANParser

D2R = math.pi/180

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
        self.last_v = np.array([0, 0, 0], dtype = np.float32)
        self.w = np.array([0, 0, 0], dtype = np.float32)

    def msg_handler(self,msg):
        return

    def convert_speed_msg(self,msg):
        '''
            Convert 100Hz Carola speed message to J1939 Odometer/Accel message.
        '''
        if msg.arbitration_id != 0XAA:
            return

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
        
        #### Send PGN-65215 msg
        self.convert_pgn65215(speed_fr, speed_fl, speed_rr, speed_rl)

        #### Send PGN-65265 msg
        self.convert_pgn65265(speed_rr, speed_rl)

        #### Send PGN-126720 msg
        self.convert_pgn126720(speed_rr, speed_rl)

        #### save to log files.
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

    def convert_pgn65215(self, speed_fr, speed_fl, speed_rr, speed_rl):
        '''
            Convert Corolla speed to PGN65215 CAN speed.
        '''
        ### construct PGN-65215 id and data
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
        return

    def convert_pgn65265(self, speed_rr, speed_rl):
        '''
            Convert Corolla speed to PGN65265 CAN speed.
        '''
        # SA CAN NOT be 0X80 which equal to MTLT's address.
        id = self.can_parser.generate_PDU(Priority = 6, PGN = 65265, SA = 0X88)
        speed = int((speed_rr + speed_rl)/2 * 256 + 0.5)
        data = [0] * 8
        data[1] = speed%256
        data[2] = int(speed/256)

        m = can.Message(arbitration_id = id, data = data, extended_id = True)
        self.can0.send(m)
        # print(m)
        return

    def convert_pgn126720(self, speed_rr, speed_rl):
        '''
            Convert Corolla speed to JD PGN126720 CAN accelerations msg.
        '''
        dt = 0.01  # [second]. Note! Modify dt according to actual message rate of signal.
        # speed = int((speed_rr + speed_rl)/2 + 0.5)/3.6 # m/s
        speed = (speed_rr + speed_rl)/2/3.6 # m/s
        v = np.array([speed, 0, 0], dtype = np.float32)
        
        # a = at + an
        #   = dv/dt + w x v
        at = (v - self.last_v)/dt
        an = np.cross(self.w * D2R, v)
        a = at + an   # in NED
        a[1] = -a[1]  # Transform to NWU
        a[2] = -a[2]
        self.last_v = v

        # limit the range of acceleration.
        for i in range(3):
            if a[i] > 322.55:
                a[i] = 322.55
            if a[i] < -320:
                a[i] = -320
        # print(self.w, v, a)
        id = self.can_parser.generate_PDU(Priority = 6, PGN = 126720, SA = 0X88) # 435093640
        data = [0] * 8
        # 
        a = np.round((a + 320) * 100)
        a = a.astype(np.int64)

        # Accel Order in payload : [acc_Y, acc_X, acc_Z]
        data[1] = a[1] & 0XFF
        data[2] = a[1] >> 8
        data[3] = a[0] & 0XFF
        data[4] = a[0] >> 8
        data[5] = a[2] & 0XFF
        data[6] = a[2] >> 8

        m = can.Message(arbitration_id = id, data = data, extended_id = True)
        self.can0.send(m)


        #### save to log files.
        s = datetime.datetime.now().strftime('%H:%M:%S.%f') + ','
        s += ','.join('{0:f}'.format(i) for i in (speed_rr, speed_rl, speed, at[0],at[1],at[2], an[0], an[1], an[2])) + ','
        s += ','.join('{0:d}'.format(i) for i in a) + ','
        s += ','.join('{0:f}'.format(i) for i in self.w) + ','
        s += ','.join('{0:d}'.format(i) for i in data) + '\n'

        self.log_file_JD_acc.write(s)
        self.log_file_JD_acc.flush()

        return

    def convert_gear_msg(self,msg):
        '''
        parse carola gear from msg.
        Carola    ->    PGN61445
           P      ->    251
           R      ->    -1
           N      ->     0
           D      ->     1
        '''

        if msg.arbitration_id != 0X3BC:
            return

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
        #### save to log files.
        s = datetime.datetime.now().strftime('%H:%M:%S.%f')
        s += ',' + str(msg.arbitration_id)
        s += ',' + str(gear) + '\n'
        self.log_file_gear.write(s)
        self.log_file_gear.flush()
        self.log_file_all.write(s)
        self.log_file_all.flush()

    def get_gyro_data(self,msg):
        '''
            Parse gyro data on CAN bus.
        '''
        # if msg.arbitration_id != 0X0CF02A80:
        #     return

        can_parser = CANParser()
        (_Priority, _PGN, _PF, _PS, _SA) = can_parser.parse_PDU(msg.arbitration_id)

        if _PGN == PGNType.ARI.value:   # Angular Rate
            data = can_parser.parse_gyro(msg.data)
            # self.w = np.array(data, dtype = np.float32)
            # Note the order of rate data is YXZ
            self.w = np.array([data[1], data[0], data[2]], dtype = np.float32)
            # print(self.w)

        return

    def handle_speed_msg(self):
        self.notifier.listeners.append(self.convert_speed_msg)

    def handle_gear_msg(self):
        self.notifier.listeners.append(self.convert_gear_msg)

    def handle_gyro_msg(self):
        self.notifier.listeners.append(self.get_gyro_data)

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
        file_dir_JD_acc   = os.path.join('data', start_time + '_JD_acc' + '.csv')

        self.log_file_all   = open(file_dir, 'w')
        self.log_file_vel   = open(file_dir_vel, 'w')
        self.log_file_gear  = open(file_dir_gear, 'w')
        self.log_file_JD_acc   = open(file_dir_JD_acc, 'w')

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
        header = 'time, ID, gear'.replace(' ', '')
        self.log_file_JD_acc.write(header + '\n')
        self.log_file_JD_acc.flush()
        pass

    def close_log_files (self):
        self.log_file_all.close()
        self.log_file_vel.close()
        self.log_dir_gear.close()
        self.log_file_JD_acc.close()


if __name__ == "__main__":
    drv = CarolaDriver()
    drv.handle_speed_msg()
    drv.handle_gear_msg()
    drv.handle_gyro_msg()

    while 1:
        time.sleep(1)
