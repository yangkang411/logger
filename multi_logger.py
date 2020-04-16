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
    # _args = [                                       \
    #         ('/dev/cu.usbserial-A403ELTH', 57600),   \
    #         ('/dev/cu.usbserial-A6004WKM', 57600),   \
    #         ]

    # # for PI
    _args = [
                ('/dev/ttyUSB0', 115200),    \
                ('/dev/ttyUSB1', 115200),    \
            ]

    for arg in _args:
        t = threading.Thread(target=imu_logger.run, args=arg)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()
