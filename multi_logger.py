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
import imu_logger

def main():
    '''main'''
    threads = []

    # # for Mac
    _args = [ ('/dev/cu.usbserial', 230400) ]

    # _args = [                                       \
    #         ('/dev/cu.usbserial-A403ELTH', 57600),   \
    #         ('/dev/cu.usbserial-A6004WKM', 57600),   \
    #         ('/dev/cu.usbserial-AI05TV24', 57600),   \
    #         ('/dev/cu.usbserial-AI05TVLF', 57600)    \
    #         ]

    # # for PI
    # _args = [
    #             ('/dev/ttyUSB0', 57600),    \
    #             ('/dev/ttyUSB1', 57600),    \
    #             ('/dev/ttyUSB2', 57600),    \
    #             ('/dev/ttyUSB3', 57600)     \
    #         ]

    for arg in _args:
        t = threading.Thread(target=imu_logger.run, args=arg)
        t.start()
        print("Thread[{0}({1})] start at:[{2}].".format(t.name, t.ident, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        threads.append(t)

    for t in threads:
        t.join()
        print("Thread[{0}({1})] stop at:[{2}].".format(t.name, t.ident, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


if __name__ == '__main__':
    main()
