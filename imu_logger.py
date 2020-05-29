# -*- coding: utf-8 -*
"""
Read, parse and save IMU data via serial port or binary file.
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
        self.apps = []
        self.first_line = True
        self.packet_type = None
        self.data_file = None
        self.log_file = None
        self.lines = 0
        self.b_send_reset_cmd = False
        self.port = None
        self.sn = None
        self.version = None
        self.odr = 0
        self.start_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        print('IMU driver start at:{0}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        # # create log file.
        # self.port = self.cmt.port.split(os.sep)[-1] # /dev/cu.usbserial-143200
        # file_dir = os.path.join('data', self.start_time+'_' + self.port + '.log')
        # self.log_file = open(file_dir, 'w')

    def reinit(self):
        ''' re-init parameters when occur SerialException.
        '''
        # DO NOT send reset cmmond when re-init logger.
        self.cmt.close()
        self.data_lock.acquire()
        while not self.data_queue.empty():
            self.data_queue.get()
        self.data_lock.release()
        self.exit_thread = False
        self.threads = []  # clear threads
        self.odr = 0

    def add_app(self, app):
        if app is not None:
            self.apps.append(app)

    def clean_apps(self):
        self.apps = []

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
                            self.odr += 1

                            # query sn if .cmt is not 'communicator.DataFile'
                            if self.sn is None and not isinstance(self.cmt, communicator.DataFile):
                                self.send_packet_GP() # send 'GP' command if hasn't got sn info.

                            # # Reset IMU to start logging from 1st packet.
                            # 1. For MTLT, it just repond SR msg, but not reset indeed, so user should as fllows to log from 1st packet:
                            #   a. run imu_logger.py and recognize serial port at first.
                            #   b. power on MTLT.
                            # 2. For other devices, they can respond SR and actually reset, so, no matter run imu_logger.py or power on device firstly, user can get and log from the 1st packet.
                            if self.b_send_reset_cmd: 
                                self.send_packet_reset() # just send reset command once.

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
            self.packet_type = tp
            tm_ms = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print("[{0}]: PACKET TYPE: {1}".format(tm_ms, self.packet_type))

        if self.packet_type == 'ID':
            self.handle_packet_ID(frame)
        elif self.packet_type == 'PK':
            self.handle_packet_PK(frame)
        elif self.packet_type == 'SR' or \
            self.packet_type == 'AR':
            self.handle_packet_RST(frame)
        elif self.packet_type == 'a1':
            self.handle_packet_a1(frame, False)
        elif self.packet_type == 'a2':
            pass
        elif self.packet_type == 'z1':
            self.handle_packet_z1(frame)
        elif self.packet_type == 's1':
            pass
        elif self.packet_type == 's2':
            pass
        elif self.packet_type == 'A1': # OpenIMU335-VG
            self.handle_packet_A1(frame)
            pass
        elif self.packet_type == 'A2': # MTLT-305
            self.handle_packet_A2(frame)
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

    def send_packet_reset(self):
        '''
        Set reset command to device.

        For MTLT:
        1. PROGRAM_RESET CAN let MTLT work in while(1).
        2. SOFTWARE_RESET is useless for MTLT.
        3. Only 'Algorithm Reset Command' can make MTLT to reset.

        For Other Device:
        1. SOFTWARE_RESET cmd is work.
        2. Not support 'Algorithm Reset Command'.
        '''
        software_rst_cmd = [0X55,0X55,0X53,0X52,0X00,0X7E,0X4F] # SOFTWARE_RESET
        algo_rst_cmd = [0X55,0X55,0X41,0X52,0X00,0X53,0X4C] # Algorithm Reset Command OF MTLT 
        program_rst_cmd = [0X55,0X55,0X50,0X52,0X00,0X27,0X1F] # PROGRAM_RESET

        self.write(software_rst_cmd)
        self.b_send_reset_cmd = False

        # if 'MTLT' in self.version: # 
        #     self.write(algo_rst_cmd)
        #     pass
        # else:
        #     self.write(software_rst_cmd)

    def send_packet_GP(self):
        '''
        Request SN and Model, eg. "1808541032" and "MTLT305D-400 5020-1382-01 19.1.6"
        IMU will response 'ID' packet when receive 'GP' packet.
        '''
        cmd = [0X55,0X55,0X47,0X50,0X02,0X49,0X44,0X23,0X3d] # Get Packet Request
        self.write(cmd)
        pass
    
    def handle_packet_PK(self, frame):
        '''
        Response 'PK' packet.
        '''
        print("Receive Response of 'PK'")
        pass

    def handle_packet_RST(self, frame):
        '''
        Response 'SR' and 'AR' packet.
        '''
        # # empty data_queue.
        # self.data_lock.acquire()
        # while not self.data_queue.empty():
        #     self.data_queue.get()
        # self.data_lock.release()

        if self.packet_type is 'SR':
            print("Receive Response of 'SR'")
        elif self.packet_type is 'AR':
            print("Receive Response of 'AR'")
        # self.b_send_reset_cmd = False

    def handle_packet_ID(self, frame):
        '''
        Handle 'ID' packet which contain SN and Model, eg. "1808541032" and "MTLT305D-400 5020-1382-01 19.1.6"
        '''
        # # empty data_queue.
        # self.data_lock.acquire()
        # while not self.data_queue.empty():
        #     self.data_queue.get()
        # self.data_lock.release()

        PAYLOAD_IDX = 5
        PAYLOAD_LEN = frame[4]
        tm_ms = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]

        pack_fmt = '>I{0}s'.format(PAYLOAD_LEN - 4) # PAYLOAD_LEN - sizeof(U4)
        len_fmt = '{0}B'.format(PAYLOAD_LEN)
        payload = frame[PAYLOAD_IDX : -2]

        b = struct.pack(len_fmt, *payload)
        d = struct.unpack(pack_fmt, b)
        self.sn = d[0]
        self.version = d[1].decode().replace('\x00','') # delete \x00 
        str = "[{0}]: {1}, Device info, SN: {2}, Version: {3}".format(tm_ms, self.port, self.sn, self.version)
        print(str)
        sys.stdout.flush()

        # log
        # self.log_file.write(str + '\n')
        pass

    def handle_packet_a1(self, frame):
        '''
        Parse 'a1' packet.
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
        PAYLOAD_LEN = frame[4] #47
        tm_ms = datetime.datetime.now().strftime('%H:%M:%S_%f')[:-3]
        
        pack_fmt = '<Id8f3B'
        len_fmt = '{0}B'.format(PAYLOAD_LEN)
        payload = frame[PAYLOAD_IDX : -2]

        if self.first_line:
            self.first_line = False
            if not os.path.exists('data/'):
                os.mkdir('data/')
            self.port = self.cmt.port.split(os.sep)[-1] # /dev/cu.usbserial-143200     
            file_dir = os.path.join('data', self.packet_type+'_' + self.start_time + '_' + self.port + '.csv')
            print('Start logging:{0}'.format(file_dir))
            self.data_file = open(file_dir, 'w')

            header = 'pc_tm, itow, dblItow, roll, pitch,       \
                    gyro_x, gyro_y, gyro_z,             \
                    acc_x, acc_y, acc_z,                \
                    ekfOpMode, accelLinSwitch, turnSwitch'.replace(' ', '')
            self.data_file.write(header + '\n')
            self.data_file.flush()

        try:
            b = struct.pack(len_fmt, *payload)
            d = struct.unpack(pack_fmt, b)
        except Exception as e:
            print("Decode payload error: {0}".format(e)) 

        str = '{0},{1:d},{2:f},{3:f},{4:f},         \
            {5:f},{6:f},{7:f},{8:f},{9:f},{10:f},   \
            {11:d},{12:d},{13:d}'                   \
            .format(tm_ms,d[0],d[1],d[2],d[3],      \
                d[4],d[5],d[6],d[7],d[8],d[9],      \
                d[10],d[11],d[12]).replace(' ', '')

        self.data_file.write(str + '\n')
        self.data_file.flush()
        self.lines += 1

        if len(self.apps) != 0 and self.sn is not None:
            data = collections.OrderedDict()
            data['pc_tm']   = tm_ms
            data['itow']    = int(d[0])
            data['dblItow'] = float(d[1])
            data['roll']    = float(d[2])
            data['pitch']   = float(d[3])
            data['gyro_x']  = float(d[4])
            data['gyro_y']  = float(d[5])
            data['gyro_z']  = float(d[6])
            data['acc_x']   = float(d[7])
            data['acc_y']   = float(d[8])
            data['acc_z']   = float(d[9])
            data['ekfOpMode'] = int(d[10])
            data['accelLinSwitch'] = int(d[11])
            data['turnSwitch'] = int(d[12])
            msg = {}
            msg['sn'] = self.sn
            msg['version'] = self.version
            msg['type'] = 'a1'
            msg['data'] = data
            for app in self.apps:
                app.on_message(msg)

        if self.lines % 1000 == 0:
            print("[{0}]:Log counter of {1}: {2}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.port, self.lines))
            sys.stdout.flush()

    def handle_packet_z1(self, frame):
        '''
        Parse 'z1' packet.
            typedef struct {
                uint32_t timer;
                float    accel_mpss[3];
                float    rate_dps[3];
                float    mag_G[3];
            }data1_payload_t;
        '''
        PAYLOAD_IDX = 5
        PAYLOAD_LEN = frame[4] # 40
        tm_ms = datetime.datetime.now().strftime('%H:%M:%S_%f')[:-3]
        
        pack_fmt = '<I9f'
        len_fmt = '{0}B'.format(PAYLOAD_LEN)
        payload = frame[PAYLOAD_IDX : -2]

        if self.first_line:
            self.first_line = False
            if not os.path.exists('data/'):
                os.mkdir('data/')
            self.port = self.cmt.port.split(os.sep)[-1] # /dev/cu.usbserial-143200     
            file_dir = os.path.join('data', self.packet_type+'_' + self.start_time + '_' + self.port + '.csv')
            print('Start logging:{0}'.format(file_dir))
            self.data_file = open(file_dir, 'w')

            header = 'pc_tm, itow,                             \
                    accel_mpss_x, accel_mpss_y, accel_mpss_z,  \
                    rate_dps_x, rate_dps_y, rate_dps_z,        \
                    mag_G_x, mag_G_y, mag_G_z'.replace(' ', '')
            self.data_file.write(header + '\n')
            self.data_file.flush()

        try:
            b = struct.pack(len_fmt, *payload)
            d = struct.unpack(pack_fmt, b)
        except Exception as e:
            print("Decode payload error: {0}".format(e)) 

        str = '{0},{1:d},{2:f},{3:f},{4:f},         \
            {5:f},{6:f},{7:f},{8:f},{9:f},{10:f}'   \
            .format(tm_ms,d[0],d[1],d[2],d[3],      \
                d[4],d[5],d[6],d[7],d[8],d[9]).replace(' ', '')

        self.data_file.write(str + '\n')
        self.data_file.flush()
        self.lines += 1

        if self.lines % 1000 == 0:
            print("[{0}]:Log counter of {1}: {2}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.port, self.lines))
            sys.stdout.flush()

    def handle_packet_A1(self, frame):
        '''
        Parse 'A1' packet.
        Please refer to page 67 of DMUX80ZA manual for A1 packet format.
        '''
        PAYLOAD_IDX = 5
        PAYLOAD_LEN = frame[4] # 0X20
        tm_ms = datetime.datetime.now().strftime('%H:%M:%S_%f')[:-3]

        pack_fmt = '>13hIH' # Note: Big Endian!
        len_fmt = '{0}B'.format(PAYLOAD_LEN)
        payload = frame[PAYLOAD_IDX : -2]

        if self.first_line:
            self.first_line = False
            if not os.path.exists('data/'):
                os.mkdir('data/')
            self.port = self.cmt.port.split(os.sep)[-1] # /dev/cu.usbserial-143200     
            file_dir = os.path.join('data', self.packet_type + '_' + self.start_time+'_' + self.port + '.csv')
            print('Start logging:{0}'.format(file_dir))
            self.data_file = open(file_dir, 'w')

            header = 'pc_tm, roll, pitch, yaw,       \
                    gyro_x, gyro_y, gyro_z,          \
                    acc_x, acc_y, acc_z,             \
                    mag_x, mag_y, mag_z,             \
                    xRateTemp,                       \
                    timeITOW, BITstatus'.replace(' ', '')
            self.data_file.write(header + '\n')
            self.data_file.flush()

        try:
            b = struct.pack(len_fmt, *payload)
            d = struct.unpack(pack_fmt, b)
        except Exception as e:
            print("Decode payload error: {0}".format(e)) 

        s = 360/math.pow(2, 16) # [360°/2^16]
        roll    = d[0] * s # roll  in [deg]
        pitch   = d[1] * s # pitch in [deg]
        yaw = d[2] * s # yaw   in [deg]

        s = 1260/math.pow(2, 16) # [1260°/2^16]
        gyro_x = d[3] * s # Corrected gyro_x in [deg/sec]
        gyro_y = d[4] * s # Corrected gyro_y in [deg/sec]
        gyro_z = d[5] * s # Corrected gyro_z in [deg/sec]

        s = 20/math.pow(2, 16) # [20/2^16]
        accel_x = d[6] * s # xAccel in [g]
        accel_y = d[7] * s # yAccel in [g]
        accel_z = d[8] * s # zAccel in [g]

        s = 20/math.pow(2, 16) # [20/2^16]
        mag_x = d[9] * s  # X magnetometer in [Gauss]
        mag_y = d[10] * s  # X magnetometer in [Gauss]
        mag_z = d[11] * s  # X magnetometer in [Gauss]

        s = 200/math.pow(2, 16) # [200/2^16]
        xRateTemp = d[12] * s  # xRateTemp in [C]
        
        timeITOW  = d[13] # DMU ITOW in [ms]
        BITstatus = d[14] # Master BIT and Status

        str = '{0},{1:f},{2:f},{3:f},{4:f},         \
            {5:f},{6:f},{7:f},{8:f},{9:f},{10:f},   \
            {11:f},{12:f},{13:f},{14:d},{15:d}'     \
            .format(tm_ms, roll, pitch, yaw,        \
                    gyro_x, gyro_y, gyro_z,         \
                    accel_x, accel_y, accel_z,      \
                    mag_x, mag_y, mag_z,            \
                    xRateTemp, timeITOW, BITstatus).replace(' ', '')

        self.data_file.write(str + '\n')
        self.data_file.flush()
        self.lines += 1

        # haven't test below code snippet
        if len(self.apps) != 0 and self.sn is not None:
            data = collections.OrderedDict()
            data['pc_tm']   = tm_ms
            data['roll']    = roll
            data['pitch']   = pitch
            data['yaw']   = yaw
            data['gyro_x']  = gyro_x
            data['gyro_y']  = gyro_y
            data['gyro_z']  = gyro_z
            data['acc_x']   = accel_x
            data['acc_y']   = accel_y
            data['acc_z']   = accel_z
            data['mag_x']   = mag_x
            data['mag_y']   = mag_y
            data['mag_z']   = mag_z
            data['xRateTemp'] = xRateTemp
            data['timeITOW'] = timeITOW
            data['BITstatus'] = BITstatus
            msg = {}
            msg['sn'] = self.sn
            msg['version'] = self.version
            msg['type'] = 'A1'
            msg['data'] = data
            for app in self.apps:
                app.on_message(msg)

        if self.lines % 1000 == 0:
            print("[{0}]:Log counter of {1}: {2}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.port, self.lines))
            sys.stdout.flush()

    def handle_packet_A2(self, frame):
        '''
        Parse 'A2' packet.
        Please refer to page 37 of MTLT305D manual for A2 packet format.
        '''
        PAYLOAD_IDX = 5
        PAYLOAD_LEN = frame[4] # 0X1E
        tm_ms = datetime.datetime.now().strftime('%H:%M:%S_%f')[:-3]

        pack_fmt = '>12hIH' # Note: Big Endian!
        len_fmt = '{0}B'.format(PAYLOAD_LEN)
        payload = frame[PAYLOAD_IDX : -2]

        if self.first_line:
            self.first_line = False
            if not os.path.exists('data/'):
                os.mkdir('data/')
            self.port = self.cmt.port.split(os.sep)[-1] # /dev/cu.usbserial-143200     
            file_dir = os.path.join('data', self.packet_type + '_' + self.start_time+'_' + self.port + '.csv')
            print('Start logging:{0}'.format(file_dir))
            self.data_file = open(file_dir, 'w')

            header = 'pc_tm, roll, pitch, yaw,       \
                    gyro_x, gyro_y, gyro_z,          \
                    acc_x, acc_y, acc_z,             \
                    xRateTemp, yRateTemp, zRateTemp, \
                    timeITOW, BITstatus'.replace(' ', '')
            self.data_file.write(header + '\n')
            self.data_file.flush()

        try:
            b = struct.pack(len_fmt, *payload)
            d = struct.unpack(pack_fmt, b)
        except Exception as e:
            print("Decode payload error: {0}".format(e)) 

        s = 360/math.pow(2, 16) # [360°/2^16]
        roll    = d[0] * s # roll  in [deg]
        pitch   = d[1] * s # pitch in [deg]
        yaw = d[2] * s # yaw   in [deg]

        s = 1260/math.pow(2, 16) # [1260°/2^16]
        gyro_x = d[3] * s # Corrected gyro_x in [deg/sec]
        gyro_y = d[4] * s # Corrected gyro_y in [deg/sec]
        gyro_z = d[5] * s # Corrected gyro_z in [deg/sec]

        s = 20/math.pow(2, 16) # [20/2^16]
        accel_x = d[6] * s # xAccel in [g]
        accel_y = d[7] * s # yAccel in [g]
        accel_z = d[8] * s # zAccel in [g]

        s = 200/math.pow(2, 16) # [200/2^16]
        xRateTemp = d[9] * s  # xRateTemp in [C]
        yRateTemp = d[10] * s # yRateTemp in [C]
        zRateTemp = d[11] * s # zRateTemp in [C]
        
        timeITOW  = d[12] # DMU ITOW in [ms]
        BITstatus = d[13] # Master BIT and Status

        str = '{0},{1:f},{2:f},{3:f},{4:f},         \
            {5:f},{6:f},{7:f},{8:f},{9:f},{10:f},   \
            {11:f},{12:f},{13:d},{14:d}'            \
            .format(tm_ms, roll, pitch, yaw,        \
                    gyro_x, gyro_y, gyro_z,         \
                    accel_x, accel_y, accel_z,      \
                    xRateTemp, yRateTemp, zRateTemp,\
                    timeITOW, BITstatus).replace(' ', '')

        self.data_file.write(str + '\n')
        self.data_file.flush()
        self.lines += 1

        # haven't test below code snippet
        if len(self.apps) != 0 and self.sn is not None:
            data = collections.OrderedDict()
            data['pc_tm']   = tm_ms
            data['roll']    = roll
            data['pitch']   = pitch
            data['yaw']   = yaw
            data['gyro_x']  = gyro_x
            data['gyro_y']  = gyro_y
            data['gyro_z']  = gyro_z
            data['acc_x']   = accel_x
            data['acc_y']   = accel_y
            data['acc_z']   = accel_z
            data['xRateTemp'] = xRateTemp
            data['yRateTemp'] = yRateTemp
            data['zRateTemp'] = zRateTemp
            data['timeITOW'] = timeITOW
            data['BITstatus'] = BITstatus
            msg = {}
            msg['sn'] = self.sn
            msg['version'] = self.version
            msg['type'] = 'A2'
            msg['data'] = data
            for app in self.apps:
                app.on_message(msg)

        if self.lines % 1000 == 0:
            print("[{0}]:Log counter of {1}: {2}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.port, self.lines))
            sys.stdout.flush()

    def handle_packet_e2(self, frame):
        '''
        Parse 'e2' packet.

        '''
        PAYLOAD_IDX = 5
        PAYLOAD_LEN = frame[4] # 0X1E
        tm_ms = datetime.datetime.now().strftime('%H:%M:%S_%f')[:-3]

        pack_fmt = '>12hIH' # Note: Big Endian!
        len_fmt = '{0}B'.format(PAYLOAD_LEN)
        payload = frame[PAYLOAD_IDX : -2]

        if self.first_line:
            self.first_line = False
            if not os.path.exists('data/'):
                os.mkdir('data/')
            self.port = self.cmt.port.split(os.sep)[-1] # /dev/cu.usbserial-143200     
            file_dir = os.path.join('data', self.packet_type + '_' + self.start_time+'_' + self.port + '.csv')
            print('Start logging:{0}'.format(file_dir))
            self.data_file = open(file_dir, 'w')

            header = 'pc_tm, roll, pitch, yaw,       \
                    gyro_x, gyro_y, gyro_z,          \
                    acc_x, acc_y, acc_z,             \
                    xRateTemp, yRateTemp, zRateTemp, \
                    timeITOW, BITstatus'.replace(' ', '')
            self.data_file.write(header + '\n')
            self.data_file.flush()

        try:
            b = struct.pack(len_fmt, *payload)
            d = struct.unpack(pack_fmt, b)
        except Exception as e:
            print("Decode payload error: {0}".format(e)) 

        s = 360/math.pow(2, 16) # [360°/2^16]
        roll    = d[0] * s # roll  in [deg]
        pitch   = d[1] * s # pitch in [deg]
        yaw = d[2] * s # yaw   in [deg]

        s = 1260/math.pow(2, 16) # [1260°/2^16]
        gyro_x = d[3] * s # Corrected gyro_x in [deg/sec]
        gyro_y = d[4] * s # Corrected gyro_y in [deg/sec]
        gyro_z = d[5] * s # Corrected gyro_z in [deg/sec]

        s = 20/math.pow(2, 16) # [20/2^16]
        accel_x = d[6] * s # xAccel in [g]
        accel_y = d[7] * s # yAccel in [g]
        accel_z = d[8] * s # zAccel in [g]

        s = 200/math.pow(2, 16) # [200/2^16]
        xRateTemp = d[9] * s  # xRateTemp in [C]
        yRateTemp = d[10] * s # yRateTemp in [C]
        zRateTemp = d[11] * s # zRateTemp in [C]
        
        timeITOW  = d[12] # DMU ITOW in [ms]
        BITstatus = d[13] # Master BIT and Status




    def get_data_from_serial_port(self, port, baud):
        self.cmt = communicator.SerialPort()
        self.cmt.port = port
        self.cmt.baud = baud

    def get_data_from_file(self, data_file):
        self.cmt = communicator.DataFile(data_file)

    def print_realtime_odr(self, inc = 1):
        _time = datetime.datetime.now().strftime("%H:%M:%S.%f")
        # print('[{0}]: ODR {1}, {2}'.format(_time, self.odr, self.data_queue.qsize()))
        print('[{0}]: ODR {1}'.format(_time, self.odr))
        t = threading.Timer(inc, self.print_realtime_odr, (inc,))
        t.start()
        self.odr = 0

def play_sound(sentence):
    '''
    Only tested on MacOS.
    https://blog.csdn.net/weixin_41822224/article/details/100167499
    '''
    cmd = "say '{0}'".format(sentence)
    os.system(cmd)

def parse_bin_file(data_file):
    '''wrapper'''
    logger = IMULogger()
    logger.get_data_from_file(data_file)
    
    while True:
        logger.reinit()
        if logger.start_collection():
            print("retry start_collection ...")
            sys.stdout.flush()
            sentence = "retry start_collection ..."
            threading.Thread(target=play_sound, args=(sentence,)).start()
            time.sleep(1)

'''
Please check below items:
1. Set SOFTWARE_RESET if desired. SOFTWARE_RESET is usless for MTLT305
2. Config serial port and baud.
3. 
'''
def run(port, baud, b_rst = False, apps = None):
    '''wrapper'''
    logger = IMULogger()

    if apps is not None:
        for app in apps:
            logger.add_app(app)

    logger.set_reset_flag(b_rst) # True: reset IMU when receive the first packet.
 
    # chose get data from serial or file.
    logger.get_data_from_serial_port(port, baud)

    # data_file = '/Users/songyang/project/analyze/drive_test/2020-3-11/log/drive_short/300RI.bin'
    # logger.get_data_from_file(data_file)
    
    # # check realtime ODF
    # logger.print_realtime_odr()

    while True:
        logger.reinit()
        if logger.start_collection():
            print("retry start_collection ...")
            sys.stdout.flush()
            sentence = "retry start_collection ..."
            threading.Thread(target=play_sound, args=(sentence,)).start()
            time.sleep(1)

def main():
    # config serial port parameters.
    port = '/dev/cu.usbserial-FTCC03Q1'
    baud = 115200
    run(port, baud, False, None)

    # data_file = '/Users/songyang/Desktop/20200425135413.imu'
    # parse_bin_file(data_file)

if __name__ == '__main__':
    main()
