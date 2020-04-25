
# -*- coding: utf-8 -*

import threading
import app_painter
import pyqtgraph as pg
import imu_logger

def main():
    '''main'''
    app = pg.mkQApp()
    painter = app_painter.AppPainter()

    timer = pg.QtCore.QTimer()
    timer.timeout.connect(painter.draw)
    timer.start(100)

    # user has to configurate '_args' to specific which devices' data need to be shown in graph.
    _args = [
            ('/dev/cu.usbserial-FTCC03Q1', 115200, False, (painter,)),
            ('/dev/cu.usbserial', 115200, False, (painter,))
            ]

    for arg in _args:
        threading.Thread(target=imu_logger.run, args=arg).start()

    app.exec_()


if __name__ == '__main__':
    main()
