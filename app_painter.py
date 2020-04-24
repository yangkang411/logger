
# -*- coding: utf-8 -*
"""
Draw roll, pitch, diff-roll and diff-pitch in real time.
Created on 2020-4-22
@author: Ocean
"""
import threading
import datetime
import collections
import numpy as np
import pyqtgraph as pg
import array
import application_base

class AppPainter(application_base.ApplicationBase):
    '''
    Draw roll, pitch, diff-roll and diff-pitch in real time.
    '''
    def __init__(self):
        '''
        Structure of .data_sets:
        {
            'sn1':
            {
                'roll':[],
                'pitch':[]
            },
            'sn2':
            {
                'roll':[],
                'pitch':[],
                'roll_diff':[],  # use 'sn1' as reference.
                'pitch_diff':[]
            },
            'sn3':
            {
                'roll':[],
                'pitch':[],
                'roll_diff':[],  # use 'sn1' as reference.
                'pitch_diff':[]
            }
            ...
        }

        Structure of .latest_roll:
        {
            'sn1': { roll_vaule }
            'sn2': { roll_vaule }
            'sn3': { roll_vaule }
            ...
        }

        Structure of .latest_pitch:
        {
            'sn1': { pitch_vaule }
            'sn2': { pitch_vaule }
            'sn3': { pitch_vaule }
            ...
        }
        '''
        self.data_lock = threading.Lock()  # data locker
        self.LEN = 300 # 30 seconds for 10hz data update rate.
        win_width = 800
        win_height = 600

        self.data_sets = collections.OrderedDict()
        self.latest_roll = collections.OrderedDict()
        self.latest_pitch = collections.OrderedDict()

        self.curves_roll = {}
        self.curves_roll_diff = {}
        self.curves_pitch = {}
        self.curves_pitch_diff = {}

        self.pens = ['r', 'g', 'y', 'c', 'm', 'b', 'k', 'w']
        self.pen_idx = -1

        # # set windows background and foreground if desired.
        # pg.setConfigOption('background', 'w')
        # pg.setConfigOption('foreground', 'k')

        # create and set window property
        self.win = pg.GraphicsWindow()
        self.win.setWindowTitle('VG')
        self.win.resize(win_width, win_height)

        # create and set plot property
        self.p_roll = self.win.addPlot(row=0, col=0, name="maximum value")
        self.p_roll.showGrid(x=True, y=True)
        # self.p_roll.setRange(xRange=[0, self.LEN - 1], yRange=[-2.2, 2.2], padding=0)
        # self.p_roll.setLabels(left='deg', bottom='point', title='Roll')
        self.p_roll.setLabels(title='Roll')
        self.p_roll.addLegend(size=(0, 0), offset=(1,1))

        self.p_roll_diff = self.win.addPlot(row=1, col=0)
        self.p_roll_diff.showGrid(x=True, y=True)
        self.p_roll_diff.setLabels(title='Diff Roll')
        self.p_roll_diff.setRange(xRange=[0, self.LEN - 1], yRange=[-1, 1], padding=0)

        self.p_pitch = self.win.addPlot(row=0, col=1)
        self.p_pitch.showGrid(x=True, y=True)
        self.p_pitch.setLabels(title='Pitch')

        self.p_pitch_diff = self.win.addPlot(row=1, col=1)
        self.p_pitch_diff.showGrid(x=True, y=True)
        self.p_pitch_diff.setLabels(title='Diff Pitch')
        self.p_pitch_diff.setRange(xRange=[0, self.LEN - 1], yRange=[-1, 1], padding=0)

    def on_message(self, *args):
        '''
        handle message from IMULogger.
        parameter:
            args: message.
        '''
        self.data_lock.acquire()
        msg = args[0]

        # Init for a new device
        if msg['sn'] not in self.latest_roll:
            self.data_sets[msg['sn']] = {}

            self.data_sets[msg['sn']]['roll'] = array.array('f')
            self.data_sets[msg['sn']]['roll_diff'] = array.array('f')

            self.data_sets[msg['sn']]['pitch'] = array.array('f')
            self.data_sets[msg['sn']]['pitch_diff'] = array.array('f')

            self.pen_idx += 1
            self.curves_roll[msg['sn']] = self.p_roll.plot(pen = pg.mkPen(self.pens[self.pen_idx], width=3), name=str(msg['sn']))
            self.curves_pitch[msg['sn']] = self.p_pitch.plot(pen = pg.mkPen(self.pens[self.pen_idx], width=3), name=str(msg['sn']))
            self.curves_roll_diff[msg['sn']] = self.p_roll_diff.plot(pen = pg.mkPen(self.pens[self.pen_idx], width=3), name=str(msg['sn']))
            self.curves_pitch_diff[msg['sn']] = self.p_pitch_diff.plot(pen = pg.mkPen(self.pens[self.pen_idx], width=3), name=str(msg['sn']))

        # update latest data.
        self.latest_roll[msg['sn']] = msg['data']['roll']
        self.latest_pitch[msg['sn']] = msg['data']['pitch']
        self.data_lock.release()

    def draw(self):
        self.data_lock.acquire()
        # draw Roll
        for i, (k, v) in enumerate(self.latest_roll.items()):  # k:sn  v:roll
            if k in self.data_sets:
                self.data_sets[k]['roll'].append(v)
                if len(self.data_sets[k]['roll']) >= self.LEN:
                    del self.data_sets[k]['roll'][0]
                self.curves_roll[k].setData(self.data_sets[k]['roll'])

        # draw Pitch
        for i, (k, v) in enumerate(self.latest_pitch.items()):  # k:sn  v:pitch
            if k in self.data_sets:
                self.data_sets[k]['pitch'].append(v)
                if len(self.data_sets[k]['pitch']) >= self.LEN:
                    del self.data_sets[k]['pitch'][0]
                self.curves_pitch[k].setData(self.data_sets[k]['pitch'])

        # # draw Diff-Roll
        if len(self.latest_roll) >= 2:
            for i, (k, v) in enumerate(self.latest_roll.items()):
                if i == 0: # set 'sn1' as reference.
                    reference_roll = v
                    continue
                # roll_diff is 'sn1_roll - snx_roll'
                self.data_sets[k]['roll_diff'].append(reference_roll - v)
                if len(self.data_sets[k]['roll_diff']) >= self.LEN:
                    del self.data_sets[k]['roll_diff'][0]
                self.curves_roll_diff[k].setData(self.data_sets[k]['roll_diff'])

        # draw Diff-Pitch
        if len(self.latest_pitch) >= 2:
            for i, (k, v) in enumerate(self.latest_pitch.items()):
                if i == 0:
                    reference_key = k
                    reference_pitch = v
                    continue
                else:
                    self.data_sets[k]['pitch_diff'].append(reference_pitch - v)
                    if len(self.data_sets[k]['pitch_diff']) >= self.LEN:
                        del self.data_sets[k]['pitch_diff'][0]
                    self.curves_pitch_diff[k].setData(self.data_sets[k]['pitch_diff'])

        self.data_lock.release()
