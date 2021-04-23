
# -*- coding: utf-8 -*

import os
import time
from datetime import datetime

def killProcess():
    print('Start at:{0}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    time.sleep(12 * 3600) # 12 Hours
    os.system('taskkill /f /im %s' % 'DataAcquire.exe')
    print('Stop at:{0}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

if __name__ == '__main__':
    killProcess()
        