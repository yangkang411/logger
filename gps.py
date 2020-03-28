# -*- coding: utf-8 -*
"""
ref: https://github.com/Aceinna/span_decoder/blob/master/span_decoder.cpp
Created on 2020-3-17
@author: Ocean
"""

import datetime
import time
import math

def epoch2time(ep):
    ''' 
    Convert time in list to seconds.
    eg. [1980,1, 6,0,0,0] => 315964800 seconds.

    Args: 
        ep: epoch. eg. [1980,1, 6,0,0,0]
    Return:
        corresponding seconds of ep. unint float. eg. 315964800.33 seconds.
    '''
    doy = [1,32,60,91,121,152,182,213,244,274,305,335]
    
    time = 0
    year = ep[0]
    mon = ep[1]
    day = ep[2]
    sec = ep[5]

    if (year < 1970 or 2099 < year or mon < 1 or 12 < mon):
        return time;

	# leap year if year%4==0 in 1901-2099
    days = (year - 1970) * 365 + (year - 1969) / 4 + doy[mon - 1] + day - 2
    days += 1 if (year % 4 == 0 and mon >= 3 ) else 0
    time = int(days) * 86400 + int(ep[3]) * 3600 + int(ep[4]) * 60 + sec;
    return time;

def gpst2time(week, sec):
    '''
    Return total seconds by given GPS week and seconds.

    Args: 
        week, sec: GPS week and seconds.
    Return:
        GPS time: total seconds since [1980-1-6 00:00:00] 
    '''
    SECONDS_IN_WEEK = 604800
    gpst0 = [1980,1, 6,0,0,0] # gps time reference
    time_base = epoch2time(gpst0)
    if (sec < -1E9 or 1E9 < sec):
        sec = 0.0

    time_gps = time_base + (SECONDS_IN_WEEK * week + sec)
    return time_gps    # float, in seconds.

def time2epoch(t):
    '''
    Convert GPS time in seconds to datetime. 
    '''
    # of days in a month 
    mday = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, \
            31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

	# /* leap year if year%4==0 in 1901-2099 */
    days = int(t / 86400)
    sec = int(t - days * 86400)

    day = days % 1461
    for mon in range(0,48): #[0,48)
        if day >= mday[mon]:
            day -= mday[mon]
        else:
            break

    _year = int(1970 + int(days / 1461)  * 4 + int(mon / 12))
    _mon = int(mon % 12 + 1)
    _day = int(day + 1)
    _hour = int(sec / 3600)
    _minute = int(sec % 3600 / 60)
    _sec = sec % 60 + math.modf(t)[0]

    time_stamp = "{0:d}-{1:d}-{2:d} {3:d}:{4:d}:{5:0.3f}".   \
        format(_year, _mon, _day, _hour, _minute, _sec)

    # return datetime
    return datetime.datetime.strptime(time_stamp, "%Y-%m-%d %H:%M:%S.%f")

def gpst2utc(t):
    '''
    Minus constant 18 seconds.
    '''
    return (t - 18.0)

def gps_time_test():
    '''
    Ref:https://www.labsat.co.uk/index.php/en/gps-time-calculator
    Verification of convert GPS time to UTC.
    '''    
    week = 2097
    sec = 110353.200 
    time_gps = gpst2time(week, sec) # float, seconds
    time_utc = gpst2utc(time_gps) # float, seconds
    time_utc_datetime = time2epoch(time_utc)  # datetime
    print(time_utc_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]) # datetime to string. 
    # 2020-03-16 06:38:55.200

if __name__ == '__main__':
    gps_time_test()
    pass