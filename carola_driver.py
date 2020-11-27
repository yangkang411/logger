'''
Convert Carola velocity CAN message to standard J1939 CAN message.
Requires PI2/3/4 and Waveshare Tech PiCAN board 'RS485 CAN HAT'
@author: Ocean
'''

import os
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
        Parse Carolar CAN message. 
        Convert velocity and gear message to standard J1939 CAN message.
    '''
    def __init__(self):
        self.cnt = 0
        ## close can0
        os.system('sudo ifconfig can0 down')
        ## set bitrate of can0
        os.system('sudo ip link set can0 type can bitrate 250000')
        ## open can0
        os.system('sudo ifconfig can0 up')
        # os.system('sudo /sbin/ip link set can0 up type can bitrate 250000')
        ## show details can0 for debug.
        # os.system('sudo ip -details link show can0')

        self.can_parser = CANParser()
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

    def msg_handler(self,msg):
        return

    def convertSpeedMsg(self,msg):
        '''
            Convert 100Hz Carola speed message to 10Hz J1939 PGN odometer message.
        '''
        if msg.arbitration_id == 0XAA:
            self.cnt += 1
            if self.cnt % 10 != 0:
                return 
            # time = datetime.datetime.fromtimestamp(msg.timestamp)
            # print(time)

            # parse wheels speed from msg.
            (speed_fr, speed_fl, speed_rr, speed_rl) = self.can_parser.parse_wheel_speed(msg.data)
            # print("speed:", speed_fr, speed_fl, speed_rr, speed_rl)

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
            print(m)

            #### construct PGN-65265 id and data
            id = self.can_parser.generate_PDU(Priority = 6, PGN = 65265, SA = 0X88)
            speed = int((speed_rr + speed_rl)/2 * 256 + 0.5)
            data = [0] * 8
            data[1] = speed%256
            data[2] = int(speed/256)

            m = can.Message(arbitration_id = id, data = data, extended_id = True)
            self.can0.send(m)
            print(m)

    def convertGearMsg(self,msg):
        if msg.arbitration_id == 0X3BC:
            # parse carola gear from msg.
            # Carola    ->    PGN61445
            #    P      ->    251
            #    R      ->    -1
            #    N      ->     0
            #    D      ->     1
            (gear,) = self.can_parser.parse_gear_carola(msg.data)
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
            print(m)

    def handleSpeedMsg(self):
        self.notifier.listeners.append(self.convertSpeedMsg)

    def handleGearMsg(self):
        self.notifier.listeners.append(self.convertGearMsg)


if __name__ == "__main__":
    drv = CarolaDriver()
    drv.handleSpeedMsg()
    drv.handleGearMsg()

    while 1:
        pass
