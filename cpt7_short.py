#!/usr/bin/python
import os
import sys
import serial
import math
import time
import datetime

def getweeknum(weekseconds):
    return math.floor(weekseconds/(7*24*3600))

def getweeksec(weekseconds):
    return weekseconds - getweeknum(weekseconds)*(7*24*3600)

def yearfour(year):
    if year<=80:
        year += 2000
    elif year<1990 and year>80:
        year += 1900
    return year

def isleapyear(year):
    return (yearfour(year)%4==0 and yearfour(year)%100!=0) or yearfour(year)%400==0
                 
def timefromGPS(weeknum,weeksec):
    year = 0
    month = 0
    day = 0
    hour = 0
    minute = 0
    second = 0
    doy = 0
    daypermon = [31,28,31,30,31,30,31,31,30,31,30,31]

    weeknum += getweeknum(weeksec)
    weeksec  = getweeksec(weeksec)
    
    weekmin  = math.floor(weeksec/60.0)
    second   = weeksec - weekmin*60.0
    weekhour = math.floor(weekmin/60)
    minute   = weekmin - weekhour*60
    weekday  = math.floor(weekhour/24)
    hour     = weekhour - weekday*24

    totalday = weekday+weeknum*7
    if totalday<360:
        year = 1980
    else:
        year = 1981
        totalday -= 360
        while True:
            if totalday<365:
                break
            if isleapyear(year): totalday -= 1
            totalday -= 365
            year += 1
    doy = totalday

    if totalday <= daypermon[0]:
        month = 1
    else:
        totalday -= daypermon[0];
        if isleapyear(year): totalday -= 1
        month = 2
        while True:
            if totalday<=daypermon[month-1]:
                break
            else:
                totalday -= daypermon[month-1]
                month += 1
    if month==2 and isleapyear(year): totalday += 1
    day = totalday
    return [year,month,day,hour,minute,second,doy]

# 删除RANGECMPB等超长字段
# RAWIMUSXB也可以删除
# inspvaxb可以设置为200、100、20hz试一下。
def configNovatel(ser):

    # need to change the following lever arm values when mounting in the car
    #'setimutoantoffset -0.2077 1.8782 1.0 0.10 0.10 0.10\r',\
    # 'setinstranslation ant2 x, y, z, std_x, std_y, std_z\r',\
    setupcommands7  = ['unlogall\r',\
                'serialconfig com1 230400 N 8 1 N OFF\r',\
                'ETHCONFIG ETHA AUTO AUTO AUTO AUTO\r',\
                'NTRIPCONFIG ncom1 client v1 106.12.40.121:2201 RTK rtkdrive 555555\r',\
                'interfacemode ncom1 rtcmv3 novatel off\r',\
                'interfacemode com1 novatel novatel on\r',\
                'alignmentmode automatic\r',\
                'setinstranslation ant1 1.0 -0.37 -1.0 0.10 0.10 0.10\r',\
                'setinstranslation ant2 0.0 0.0 0.0 0.10 0.10 0.10\r',\
                'setinsrotation rbv -180 0 90\r',\
                #'setinsrotation rbv 90 0 180\r',\
                'setinstranslation user 1.0 -0.37 -1.0 0.10 0.10 0.10\r',\
                'log INSCONFIGB ONCHANGED\r',\
                'log RAWIMUSXB ONNEW\r',\
                'log versionb once\r',\
                'log rxconfigb once\r',\
                'log rxstatusb once\r',\
                'log thisantennatypeb once\r',\
                'log inspvaxb ontime 0.1\r',\
                #'log bestposb ontime 0.1\r',\
                'log bestgnssposb ontime 0.1\r',\
                #'log bestgnssvelb ontime 0.1\r',\
                #'log heading2b onnew\r',\
                'log ncom1 gpgga ontime 1\r',\
                'saveconfig\r']
        
    for cmd in setupcommands7:
        ser.write(cmd.encode())    


if __name__ == '__main__':
    port = 'COM1'
    ser = serial.Serial(port, 230400, parity='N', bytesize = 8, 
                        stopbits = 1, timeout = None) #novatel

    if not os.path.exists('data/'):
        os.mkdir('data/')

    fname = './data/novatel_CPT7-'
    ser.flushInput()
    fmode = 'wb'
    while True:
        if ser.isOpen(): break

    print ('\Port is open now\n')
    configNovatel(ser)
    ser.flushInput()

    fname += time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime()) + '.bin'
    idx = 0
    with open(fname,fmode) as outf:
        while True:
            try:
                line = ser.readline()
                outf.write(bytes(line))  #line.decode('utf-8')

                idx += 1            
                if idx % 1000 == 0:
                    print("[{0}]:Log counter: {1}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), idx))
                    sys.stdout.flush()

            except Exception as e:
                print(e)
        outf.close()
