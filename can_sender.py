'''
Continuously and periodically send fake(dummy) CAN velocity and gear message for testing MTLT335.
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


class CanSender:
    '''
        Continuously and periodically send CAN velocity and gear message for testing MTLT335.
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
        self.lines = 0

    def msg_handler(self, msg):
        return

    def send_Carola_CAN_msg(self):
        '''
            1. Sending fake velocity and gear message of Carola.
            2. Message rate of velocity messate is 100Hz, fake data: [1, 2, ... 250, 1, 2, ... 250 ...] km/hr
            3. Message rate of gear messate is 10Hz, fake data: [D, R, N, P, D ...]
        '''
        speed_id = 0XAA
        gear_id = 0X3BC
        msg_rate = 100            # 100 Hz
        send_data_circle = 100   # 
        gear_data = [0] * 8

        self.lines = 0
        offset = -67.67           # km/hr
        idx = 0

        for t in range(send_data_circle):
            for s in range(1, 251):  # speed range: [1, 250] km/hr
                # Construct wheel speed CAN message.
                wheel_raw_speed = (s - offset)/0.01
                wheel_data = [int(wheel_raw_speed/256), int(wheel_raw_speed%256)] * 4
                # Send wheel speed CAN message.
                m = can.Message(arbitration_id = speed_id, data = wheel_data, extended_id = False)
                self.can0.send(m)

                if 0 == idx%10: # Sending gear msg at 10 Hz.
                    # Construct Gear CAN message.
                    if 0 == t:
                        gear_data[1] = 0   # Gear: D
                    elif 1 == t:
                        gear_data[1] = 16  # Gear: R
                    elif 2 == t:
                        gear_data[1] = 8   # Gear: N
                    elif 3 == t:
                        gear_data[1] = 32  # Gear: P
                    else:
                        gear_data[1] = 0   # Gear: D

                    # Send Gear CAN message.
                    m = can.Message(arbitration_id = gear_id, data = gear_data, extended_id = False)
                    self.can0.send(m)

                idx += 1
                time.sleep(1/msg_rate)  #

                ##
                self.lines += 1
                if self.lines % 1000 == 0:
                    print("[{0}]:Sending wheel speed msg counter: {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.lines))
                    sys.stdout.flush()
        pass

    def send_pgn65215_msg(self):
        '''
            1. Sending PGN65215 wheel speed and PGN61445 gear CAN message.
            2. Message rate of PGN65215 messate is 10Hz, fake data: [1, 2, ... 250, 1, 2, ... 250 ...] km/hr
            3. Message rate of PGN61445 messate is 10Hz, fake data: [1, -1, 2, 3, 4, 5, 1, 1 ...]
        '''
        msg_rate = 100             # 10 Hz
        send_data_circle = 1000     # 
        gear_data = [0] * 8
        self.lines = 0

        speed_id = self.can_parser.generate_PDU(Priority = 6, PGN = 65215, SA = 0X88)
        gear_id  = self.can_parser.generate_PDU(Priority = 6, PGN = 61445, SA = 0X88)

        for t in range(send_data_circle):
            for s in range(1, 251):  # speed range: [1, 250] km/hr
                # Construct wheel speed CAN message, assume all relative speed are zero.
                offset = -7.8125          # km/hr
                front_axle_speed = s
                front_left_wheel_speed  = int((0 - offset) * 16 + 0.5)
                front_right_wheel_speed = front_left_wheel_speed
                rear_left1_wheel_speed  = front_left_wheel_speed
                rear_right1_wheel_speed = front_left_wheel_speed
                rear_left2_wheel_speed  = rear_left1_wheel_speed
                rear_right2_wheel_speed = rear_right1_wheel_speed
                front_axle_speed = int(front_axle_speed * 256 + 0.5)

                wheel_data = []
                wheel_data.append(front_axle_speed % 256)
                wheel_data.append(int(front_axle_speed/256))
                wheel_data.append(front_left_wheel_speed)
                wheel_data.append(front_right_wheel_speed)
                wheel_data.append(rear_left1_wheel_speed)
                wheel_data.append(rear_right1_wheel_speed)
                wheel_data.append(rear_left2_wheel_speed)
                wheel_data.append(rear_right2_wheel_speed)

                # Send wheel speed CAN message.
                m = can.Message(arbitration_id = speed_id, data = wheel_data, extended_id = True)
                self.can0.send(m)
                # arbitration_id = j1939.ArbitrationID(priority=6, pgn=65215)
                # m = j1939.PDU(arbitration_id=arbitration_id, data=wheel_data)
                # self.bus.send(m)

                # Construct Gear CAN message.
                offset = -125
                if 0 == t:
                    gear_data[3] = 1   # Gear: 1
                    gear_data[3] -= offset
                elif 1 == t:
                    gear_data[3] = -1 # Gear: -1
                    gear_data[3] -= offset
                elif 2 == t:
                    gear_data[3] = 2   # Gear: 2
                    gear_data[3] -= offset
                elif 3 == t:
                    gear_data[3] = 3  # Gear: 3
                    gear_data[3] -= offset
                elif 4 == t:
                    gear_data[3] = 4  # Gear: 4
                    gear_data[3] -= offset
                elif 5 == t:
                    gear_data[3] = 5  # Gear: 5
                    gear_data[3] -= offset
                elif 6 == t:
                    gear_data[3] = 251 # Gear: 251 0XFB, Park
                else:
                    gear_data[3] = 1   # Gear: 1
                    gear_data[3] -= offset

                # Send Gear CAN message.
                m = can.Message(arbitration_id = gear_id, data = gear_data, extended_id = True)
                self.can0.send(m)
                # arbitration_id = j1939.ArbitrationID(priority=6, pgn=61445)
                # m = j1939.PDU(arbitration_id=arbitration_id, data=gear_data)
                # self.bus.send(m)
                
                time.sleep(1/msg_rate)  #

                ##
                self.lines += 1
                if self.lines % 1000 == 0:
                    print("[{0}]:Sending wheel speed msg counter: {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.lines))
                    sys.stdout.flush()
        pass

    def send_pgn65265_msg(self):
        '''
            1. Sending PGN65265 wheel speed and PGN61445 gear CAN message.
            2. Message rate of PGN65265 messate is 10Hz, fake data: [1, 2, ... 250, 1, 2, ... 250 ...] km/hr
            3. Message rate of PGN61445 messate is 10Hz, fake data: [1, -1, 2, 3, 4, 5, 1, 1 ...]
        '''
        msg_rate = 100             # 10 Hz
        send_data_circle = 1000     # 
        gear_data = [0] * 8
        wheel_data = [0] * 8
        self.lines = 0

        speed_id = self.can_parser.generate_PDU(Priority = 6, PGN = 65265, SA = 0X88)
        gear_id  = self.can_parser.generate_PDU(Priority = 6, PGN = 61445, SA = 0X88)

        for t in range(send_data_circle):
            for s in range(1, 251):  # speed range: [1, 250] km/hr
                # Construct wheel speed CAN message.
                speed = int(s * 256 + 0.5)    # km/hr
                wheel_data[1] = speed%256
                wheel_data[2] = int(speed/256)

                # Send wheel speed CAN message.
                m = can.Message(arbitration_id = speed_id, data = wheel_data, extended_id = True)
                self.can0.send(m)

                # Construct Gear CAN message.
                offset = -125
                if 0 == t:
                    gear_data[3] = 1   # Gear: 1
                    gear_data[3] -= offset
                elif 1 == t:
                    gear_data[3] = -1 # Gear: -1
                    gear_data[3] -= offset
                elif 2 == t:
                    gear_data[3] = 2   # Gear: 2
                    gear_data[3] -= offset
                elif 3 == t:
                    gear_data[3] = 3  # Gear: 3
                    gear_data[3] -= offset
                elif 4 == t:
                    gear_data[3] = 4  # Gear: 4
                    gear_data[3] -= offset
                elif 5 == t:
                    gear_data[3] = 5  # Gear: 5
                    gear_data[3] -= offset
                elif 6 == t:
                    gear_data[3] = 251 # Gear: 251 0XFB, Park
                else:
                    gear_data[3] = 1   # Gear: 1
                    gear_data[3] -= offset

                # Send Gear CAN message.
                m = can.Message(arbitration_id = gear_id, data = gear_data, extended_id = True)
                self.can0.send(m)
                
                time.sleep(1/msg_rate)  #

                ##
                self.lines += 1
                if self.lines % 1000 == 0:
                    print("[{0}]:Sending wheel speed msg counter: {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.lines))
                    sys.stdout.flush()
        pass
            

if __name__ == "__main__":
    drv = CanSender()
    # drv.send_Carola_CAN_msg()
    drv.send_pgn65215_msg()
    # drv.send_pgn65265_msg()

