import time
import random
from multiprocessing import Process
def run(name):
    print('%s runing' %name)
    for i in range (10000000):
        time.sleep(0.00001)
    
    print('%s running end' %name)

p1=Process(target=run,args=('anne',)) #必须加,号 
p2=Process(target=run,args=('alice',))
p3=Process(target=run,args=('biantai',))
p4=Process(target=run,args=('haha',))

p1.start()
p2.start()
p3.start()
p4.start()

p1.join() #等待p1进程停止
p2.join()
p3.join()
p4.join()

print('主线程')
