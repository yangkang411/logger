
# -*- coding: utf-8 -*

import math
import os
import threading
import time
from datetime import datetime
import sched
from threading import Timer
import imu_logger

def cal():
    R2D = 57.29577951308232

    ax = 0.0504403673
    ay = -0.000505248841
    az = -0.998726963
    
    roll = math.atan2(-ay, -az) * R2D
    print("roll:", roll)

    pitch = math.asin(ax) * R2D
    print("pitch:", pitch)

    pass

def play_sound(sentence):
    cmd = "say '{0}'".format(sentence)
    os.system(cmd)

def test():
    logger = imu_logger.IMULogger()
    # frame = bytearray(b'\x55\x55\x41\x32\x1E\x00\x51\xFF\xC9\xFF\x67\x00\x00\x00\x00\x00\x00\xFF\xEB\xFF\xEC\xF3\x3D\x1D\x70\x1D\x70\x1D\x70\x00\x06\x5A\x54\x00\x00\x6D\xC9\x55\x55\x41\x32\x1E\x00\x51\xFF\xC9\xFF\x67\xFF\xFE\x00\x00\x00\x01\xFF\xEB\xFF\xEC\xF3\x3E\x1D\x70\x1D\x70\x1D\x70\x00\x06\x5A\x5E\x00\x00\x31\x33')
    # logger.handle_packet_A2(frame)

    frame = bytearray(b'\x55\x55\x53\x31\x18\x00\x00\xFF\xFE\xF3\x32\xFF\xF3\x00\x01\xFF\xF8\x23\xB9\x24\x26\x24\xCA\x2A\xFF\x96\x81\x03\x00\x24\x8A')
    logger.handle_packet_S1(frame)

def crc_test():
    logger = imu_logger.IMULogger()
    # frame = bytearray(b'\x50\x52\x00')
    frame = bytearray(b'\x57\x46\x05\x01\x00\x03\x41\x32')
    frame = bytearray(b'\x57\x46\x05\x01\x00\x03\x64\x32')
    crc = logger.calc_crc(frame)
    print(hex(crc))
    # SOFTWARE_RESET: [0X55,0X55,0X53,0X52,0X00,0X7E,0X4F]
    # PROGRAM_RESET : [0X55,0X55,0X50,0X52,0X00,0X27,0X1F]
    # Algorithm Reset Command OF MTLT : [0X55,0X55,0X50,0X52,0X00,0X53,0X4C]


def printTime(inc):
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
    t = Timer(inc, printTime, (inc,))
    t.start()

def splitLPFString():
    s = '2.26089145389181e-05	0.000149459181284952	0.000493455367785529	0.00112316786339784	0.00202896369942417	0.00312870308570863	0.00428333858693355	0.00532023538567916	0.00606094718811040	0.00634955688101024	0.00607761184847596	0.00520216201785279	0.00375437709406590	0.00183754210275241	-0.000385278397410189	-0.00271216661348274	-0.00492892146359787	-0.00683753299351386	-0.00828255474685345	-0.00917166273090619	-0.00948750584317722	-0.00928917532011385	-0.00870307828209258	-0.00790448815482462	-0.00709235378477426	-0.00646089565633348	-0.00617196886710506	-0.00633206507211488	-0.00697717455133807	-0.00806762628912028	-0.00949362336675360	-0.0110906896898667	-0.0126628528659705	-0.0140103022266629	-0.0149576329923019	-0.0153787055684625	-0.0152146244551433	-0.0144823074851846	-0.0132724374351445	-0.0117370789656463	-0.0100686950361301	-0.00847350466540769	-0.00714291861883044	-0.00622705972378801	-0.00581408212406196	-0.00591818992868931	-0.00647803465000700	-0.00736571398438935	-0.00840510639540070	-0.00939696552788821	-0.0101472496859049	-0.0104947076497494	-0.0103338467192999	-0.00963005736531777	-0.00842477020414033	-0.00682992056611304	-0.00501249721845399	-0.00317134406052763	-0.00150947137260081	-0.000205763755403908	0.000609943277428653	0.000874918907235230	0.000602189747562053	-0.000121425372095535	-0.00114762307393785	-0.00228753813276283	-0.00333834438193965	-0.00411179988344004	-0.00446072951355450	-0.00429972772828217	-0.00361717574571928	-0.00247688679348809	-0.00100914922280270	0.000607574244066537	0.00217172105689242	0.00348695610824047	0.00438977401457842	0.00477250047858723	0.00459846274356703	0.00390719855790225	0.00280897159381588	0.00146936256848773	8.60986263290196e-05	-0.00113862675057876	-0.00202645791729885	-0.00244783229354183	-0.00234008374395422	-0.00171615312025011	-0.000662683615897644	0.000672231167440508	0.00209992590522013	0.00341773736223806	0.00443754219385098	0.00501225190515873	0.00505654496875428	0.00455892518913211	0.00358341315601110	0.00226063308716153	0.000769546189682441	-0.000687605151942096'
    s = s.replace('	',',')
    items = s.split(',')
    gap = 6
    len = s.count(',',0)
    y = len % gap


    str = ''
    for i, item in enumerate(items):
        str += item + ','
        if i != 0 and (i % gap == 0):
            print (str)
            str = ''
        if len - i < y:
            print (item + ',',end='')
    
    print()            
    pass

def splitCalibrationHexString(hex_str):
    s = hex_str.upper()
    items = s.split(' ')

    # s = s.replace('	',',')
    # items = s.split(',')
    # gap = 6
    # len = s.count(',',0)
    # y = len % gap

    str = ''
    for i, item in enumerate(items):
        item_list = list(item)
        # 在Index 2和0处插入空格
        item_list.insert(2, ' ')
        item_list.insert(0, ' ')
        # list转string
        s = "".join(item_list)
        # 空格替换为 0X
        s = s.replace(' ', ', 0X')
        str += s
   
    str = str[2:] 
    print(str) 
    pass

def parseCalibrationHexString():
    filename = 'bin.txt'
    s = ''
    with open(filename, 'r') as file_to_read:
        while True:
            lines = file_to_read.readline() # 整行读取数据
            if not lines:
                break

            items = lines.split(' ')
            for i in range(2, 14):
                s += items[i]
                s += ' '
        pass
    
    splitCalibrationHexString(s[0:-1])
    pass

def killProcess():
    print("dfdfdfdf")
    time.sleep(0.1*100000)
    os.system('taskkill /f /im %s' % 'DataAcquire.exe')

    pass

def main():
    '''main'''
    # killProcess()

    # crc_test()

    splitLPFString()
    return 

    parseCalibrationHexString()
    return

    hex_str = '0000 1d00 3a00 5700 7400 9100 ae00 c200 d600 ea00 1201 3a01 6201 0000 0000 0000'
    splitCalibrationHexString(hex_str)
    return 

    test()
    return

    crc_test()
    return
    # printTime(1)
    a = [1,2,3]
    del a[0]
    print(a)
    return

    while True:
        sentence = "retry start_collection ..."
        threading.Thread(target=play_sound, args=(sentence,)).start()
        time.sleep(2)

if __name__ == '__main__':
    main()
        