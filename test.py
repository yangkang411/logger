
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
    s = '0	0.00186010006877822	0.00255604295203759	0.000236836131702715	0.000945478295432865	0.00279818160403025	0.000916190521605920	0.000198527884663607	0.00249618487146067	0.00176616146500160	-0.000107755814452256	0.00175318726037004	0.00244996655458446	0.000131589601710956	0.000841055140600508	0.00269457538284657	0.000813394842954039	9.65364074262702e-05	0.00239499130412910	0.00166575956528739	-0.000207372240002254	0.00165435016398436	0.00235190269043739	3.42929205748542e-05	0.000744519640572656	0.00259879510897894	0.000718363886885965	2.24890701993252e-06	0.00230144144310795	0.00157294157287735	-0.000299464089428759	0.00156297877670711	0.00226124612891801	-5.56544074828845e-05	0.000655275997430544	0.00251024964561437	0.000630511141229194	-8.49165402673467e-05	0.00221495791724897	0.00148713463357088	-0.000384599735322182	0.00147850917249711	0.00217743735574764	-0.000138807519492986	0.000572773417146862	0.00242839250775240	0.000549294396299344	-0.000165497902250990	0.00213500696742025	0.00140780916399378	-0.000463304617967228	0.00140042002174648	0.00209995911983621	-0.000215679619935162	0.000496502710194436	0.00235271848940812	0.000474212398489334	-0.000239992511080846	0.00206109515225045	0.00133447558311450	-0.000536064488256247	0.00132822937373777	0.00202833324091127	-0.000286745148134226	0.000425993148929491	0.00228276054558136	0.000404801756632154	-0.000308860132675976	0.00199276630270706	0.00126668129064761	-0.000603328405646916	0.00126149168214006	0.00196211765828442	-0.000352442706405237	0.000360809562354440	0.00221808690974759	0.000340634082042115	-0.000372525804308749	0.00192959870671187	0.00120400787369491	-0.000665511509667865	0.00119979505518579	0.00190090370254081	-0.000413177767019798	0.000300549650328787	0.00215829842908094	0.000281313344585612	-0.000431382457850455	0.00187120250641737	0.00114606852438383	-0.000722997582077780	0.00114275871355594	0.00184431357331233	-0.000469325174700329	0.000244841500652779	0.00210302610096242	0.000226473428461856	-0.000485793344868152	0.00181721729208242	0.00109250565256662'
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

def main():
    '''main'''

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
        