# -*- coding: utf-8 -*
"""
Driver for OpenIMU.
Created on 2020-3-11
@author: Ocean
"""

import sys
import os
import threading
import datetime
import time
import operator
import struct
import glob
import math
import json
import collections
import serial
import serial.tools.list_ports
if sys.version_info[0] > 2:
    from queue import Queue
else:
    from Queue import Queue
import communicator

D2R = 0.017453292519943
R2D = 57.29577951308232
GRAVITY = 9.80665

class IMULogger:
    def __init__(self):
        ''' initialization
        '''
        # self.cmt = communicator.SerialPort()
        self.cmt = None
        self.threads = []  # thread of receiver and paser
        self.exit_thread = False  # flag of exit threads
        self.exit_lock = threading.Lock()  # lock of exit_thread
        self.data_queue = Queue()  # data container
        self.data_lock = threading.Lock()  # lock of data_queue
        self.first_line = True
        self.packet_type = None
        self.log_file = None
        self.lines = 0
        self.b_send_reset_cmd = False
        self.start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        print('IMU driver start at:{0}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    def reinit(self):
        ''' re-init parameters when occur SerialException.
        '''
        # DO NOT send reset cmmond when re-init logger.
        self.cmt.close()
        if not self.data_queue.empty():
            self.data_queue.get()
        self.exit_thread = False
        self.threads = []  # clear threads

    def receiver(self):
        ''' receive IMU data and push data into data_queue.
            return when occur Exception
        '''
        while True:
            self.exit_lock.acquire()
            if self.exit_thread:
                self.exit_lock.release()
                self.cmt.close()
                return
            self.exit_lock.release()

            try:
                data = bytearray(self.cmt.read(self.cmt.read_size))
            except Exception as e:
                self.exit_lock.acquire()
                self.exit_thread = True  # Notice thread paser to exit.
                self.exit_lock.release()
                return  # exit thread receiver

            if len(data):
                # print(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S:') + ' '.join('0X{0:x}'.format(data[i]) for i in range(len(data))))
                self.data_lock.acquire()
                for d in data:
                    self.data_queue.put(d)
                self.data_lock.release()
            else:
                time.sleep(0.001)

    def parser(self):
        ''' get IMU data from data_queue and parse data into one whole frame.
            return when occur Exception in thread receiver.
        '''
        HEADER = [0X55, 0X55]
        PACKAGE_TYPE_IDX = 2
        PAYLOAD_LEN_IDX = 4
        MAX_FRAME_LIMIT = 256  # assume max len of frame is smaller than MAX_FRAME_LIMIT.

        sync_pattern = collections.deque(2*[0], 2)
        find_header = False
        frame = []
        payload_len = 0

        while True:
            self.exit_lock.acquire()
            if self.exit_thread:
                self.exit_lock.release()
                return  # exit thread parser
            self.exit_lock.release()

            self.data_lock.acquire()
            if self.data_queue.empty():
                self.data_lock.release()
                time.sleep(0.001)
                continue
            else:
                data = self.data_queue.get()
                self.data_lock.release()
                # print(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S:') + hex(data))

                if find_header:
                    frame.append(data)
                    if PAYLOAD_LEN_IDX + 1 == len(frame):
                        payload_len = frame[PAYLOAD_LEN_IDX]
                    elif 2 + 2 + 1 + payload_len + 2 == len(frame):  # 2: len of header 'UU'; 2: package type 'a1'; 1: payload len; 2:len of checksum.
                        find_header = False
                        # checksum
                        packet_crc = 256 * frame[-2] + frame[-1]    
                        if packet_crc == self.calc_crc(frame[PACKAGE_TYPE_IDX : -2]):
                            # find a whole frame
                            self.parse_frame(frame)
                            if self.b_send_reset_cmd:
                                self.b_send_reset_cmd = False
                                cmd = [0X55,0X55,0X53,0X52,0X00,0X7E,0X4F] # SOFTWARE_RESET
                                self.write(cmd)

                        else:
                            print("CRC error!")
                            sentence = "CRC error!"
                            threading.Thread(target=play_sound, args=(sentence,)).start()
                            error_data = ' '.join(["%02X" % x for x in frame]).strip()
                            # cerror_datamd = [hex(d) for d in frame]
                            print(error_data)

                    else:
                        pass

                    if payload_len > MAX_FRAME_LIMIT or len(frame) > MAX_FRAME_LIMIT:
                        find_header = False
                        payload_len = 0

                else:  # if hasn't found header 'UU'
                    sync_pattern.append(data)
                    if operator.eq(list(sync_pattern), HEADER):
                        frame = HEADER[:]
                        find_header = True
                        sync_pattern.append(0)
                    else:
                        pass

    def write(self,n):
        try:
            self.cmt.write(n)
        except Exception as e:
            print(e)
            self.exit_lock.acquire()
            self.exit_thread = True  # Notice thread paser and receiver to exit.
            self.exit_lock.release()

    def set_reset_flag(self, reset = False):
        '''
        Set 'self.b_send_reset_cmd' True can make logger to send software reset command to IMU once.
        '''
        self.b_send_reset_cmd = reset

    def handle_KeyboardInterrupt(self):
        ''' handle KeyboardInterrupt.
            returns: True when occur KeyboardInterrupt.
                     False when receiver and parser threads exit.
        '''
        while True:
            self.exit_lock.acquire()
            if self.exit_thread:
                self.exit_lock.release()
                return False  # return when receiver and parser threads exit
            self.exit_lock.release()

            try:
                time.sleep(0.1)
            except KeyboardInterrupt:  # response for KeyboardInterrupt such as Ctrl+C
                self.exit_lock.acquire()
                self.exit_thread = True  # Notice thread receiver and paser to exit.
                self.exit_lock.release()
                print('User stop this program by KeyboardInterrupt! File:[{0}], Line:[{1}]'.format(__file__, sys._getframe().f_lineno))
                return True

    def start_collection(self):
        ''' start two threads: receiver and parser.
            returns False when user trigger KeyboardInterrupt to stop this program.
            otherwise returns True.
        '''
        if not self.cmt.open():
            return True

        funcs = [self.receiver, self.parser]
        for func in funcs:
            t = threading.Thread(target=func, args=())
            t.start()
            print("Thread[{0}({1})] start at:[{2}].".format(t.name, t.ident, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.threads.append(t)

        if self.handle_KeyboardInterrupt():
            return False

        for t in self.threads:
            t.join()
            print("Thread[{0}({1})] stop at:[{2}].".format(t.name, t.ident, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        self.cmt.close()
        return True

    def parse_frame(self, frame):
        '''Parses packet payload.
        '''
        PACKET_TYPE_IDX = 2
        tp = '{0}{1}'.format(chr(frame[PACKET_TYPE_IDX]) ,chr(frame[PACKET_TYPE_IDX+1]))
        if self.packet_type != tp:
            print("PACKET TYPE: {0}".format(self.packet_type))
            self.packet_type = tp

        if self.packet_type == 'a1':
            self.handle_packet_a1(frame, False)
        elif self.packet_type == 'a2':
            pass
        elif self.packet_type == 'z1':
            pass
        elif self.packet_type == 's1':
            pass
        elif self.packet_type == 's2':
            pass

    def calc_crc(self,payload):
        '''Calculates CRC per 380 manual
        '''
        crc = 0x1D0F
        for bytedata in payload:
           crc = crc^(bytedata << 8) 
           for i in range(0,8):
                if crc & 0x8000:
                    crc = (crc << 1)^0x1021
                else:
                    crc = crc << 1

        crc = crc & 0xffff
        return crc

    def handle_packet_a1(self, frame, save_as_sim_fmt = False):
        '''
        Parse 'a1' packet.
        save_as_sim_fmt: 
            False: Default, save log as 'a1' order.
            True: Save log as sim format which can be used in dmu380_sim_src.
                  [accel: g, gyro: deg/sec, mag: Gauss, AccTemp, RateTemp]

            typedef struct {
                uint32_t itow;          // msec
                double   dblItow;       // s
                float    roll;          // deg
                float    pitch;         // deg
                float    corrRates[3];  // deg/s
                float    accels[3];     // "m/s/s"
                uint8_t  ekfOpMode;
                uint8_t  accelLinSwitch;
                uint8_t  turnSwitch;
            }angle1_payload_t;
        '''
        PAYLOAD_IDX = 5
        PAYLOAD_LEN = 47
        tm_ms = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]

        pack_fmt = '<Id8f3B'
        len_fmt = '{0}B'.format(PAYLOAD_LEN)
        payload = frame[PAYLOAD_IDX : -2]

        if self.first_line:
            self.first_line = False
            if not os.path.exists('data/'):
                os.mkdir('data/')
            file_dir = os.path.join('data', self.packet_type+'_'+ self.start_time+'.csv')
            print('Start logging:{0}'.format(file_dir))
            self.log_file = open(file_dir, 'w')

            if not save_as_sim_fmt: # save log as 'a1' packet
                header = 'pc_tm, itow, dblItow, roll, pitch,       \
                        gyro_x, gyro_y, gyro_z,             \
                        acc_x, acc_y, acc_z,                \
                        ekfOpMode, accelLinSwitch, turnSwitch'.replace(' ', '')
                self.log_file.write(header + '\n')
                self.log_file.flush()

        try:
            b = struct.pack(len_fmt, *payload)
            d = struct.unpack(pack_fmt, b)
        except Exception as e:
            print("Decode payload error: {0}".format(e)) 

        if not save_as_sim_fmt: # Save log as 'a1' packet
            str = '{0},{1:d},{2:f},{3:f},{4:f},         \
                {5:f},{6:f},{7:f},{8:f},{9:f},{10:f},   \
                {11:d},{12:d},{13:d}'                   \
                .format(tm_ms,d[0],d[1],d[2],d[3],      \
                    d[4],d[5],d[6],d[7],d[8],d[9],      \
                    d[10],d[11],d[12]).replace(' ', '')
        else:# Save log as sim format. Save 'roll' and 'pitch' in last two columns.
            str = '{0:f},{1:f},{2:f},{3:f},{4:f},{5:f},     \
                   {6:f},{7:f},{8:f},{9:f},{10:f},{11:f},   \
                   {12:f},{13:f},{14:f},{15:f}'             \
                .format(d[7]/GRAVITY, d[8]/GRAVITY, d[9]/GRAVITY, d[4], d[5], d[6], \
                        0, 0, 0, 0, 0, 0, 0, 0, d[2],d[3]).replace(' ', '')

        self.log_file.write(str + '\n')
        self.log_file.flush()
        self.lines += 1
        if self.lines % 1000 == 0:
            print("[{0}]:Log counter: {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.lines))

    def get_data_from_serial_port(self):
        self.cmt = communicator.SerialPort()
        self.cmt.port = '/dev/cu.usbserial-AH01EAT5' 
        # self.cmt.port = '/dev/cu.usbserial-143400' 
        self.cmt.baud = 230400

    def get_data_from_file(self):
        data_file = '/Users/songyang/project/analyze/drive_test/2020-3-11/log/drive_short/300RI.bin'
        self.cmt = communicator.DataFile(data_file)


def play_sound(sentence):
    '''
    Only tested on MacOS.
    https://blog.csdn.net/weixin_41822224/article/details/100167499
    '''
    cmd = "say '{0}'".format(sentence)
    os.system(cmd)


def main():
    '''main'''
    logger = IMULogger()
    logger.set_reset_flag(True) # reset IMU when receive the first packet.
    logger.get_data_from_serial_port()
    # logger.get_data_from_file()
    
    while True:
        logger.reinit()
        if logger.start_collection():
            print("retry start_collection ...")
            sentence = "retry start_collection ..."
            threading.Thread(target=play_sound, args=(sentence,)).start()
            time.sleep(1)


if __name__ == '__main__':
    main()
    
