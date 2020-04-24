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
    _args = [                                                      \
            ('/dev/cu.usbserial-FTCC03Q1', 115200, False, None),   \
            ('/dev/cu.usbserial', 115200, False, None),            \
            ]

    # # for PI
    # _args = [
    #             ('/dev/ttyUSB0', 115200, False, None),    \
    #             ('/dev/ttyUSB1', 115200, False, None),    \
    #         ]

    for arg in _args:
        t = threading.Thread(target=imu_logger.run, args=arg)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()
