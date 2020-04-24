# coding:utf8
"""
ApplicationBase
Created on 2020-4-22
@author: Ocean
"""

from abc import ABCMeta, abstractmethod


class ApplicationBase():
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def on_message(self, *args):
        '''
        on_message will be invoked when driver parse a whole frame successful.
        '''
        pass
