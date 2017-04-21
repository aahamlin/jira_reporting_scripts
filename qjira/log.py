'''An ultra stupid logger'''
from __future__ import print_function
import sys

class Log:
    '''Simple logger'''

    # globals
    debugLevel = 0
    
    @staticmethod
    def eprint (*args, **kwargs):
        '''print args to stderr'''
        print(*args, file=sys.stderr, **kwargs)

    @staticmethod
    def error (*msg):
        '''Log as an error'''
        Log.eprint('[ERROR]', *msg)

    @staticmethod
    def info (*msg):
        '''Log message when debug >= 0'''
        if Log.debugLevel < 0:
            return
        Log.eprint('[INFO]', *msg)

    @staticmethod
    def debug (*msg):
        '''Log message when debug >= 1'''
        if Log.debugLevel < 1:
            return
        Log.eprint('[DEBUG]', *msg)

    @staticmethod
    def verbose (*msg):
        '''Log message when debug >= 2'''
        if Log.debugLevel < 2:
            return
        Log.eprint('[VERBOSE]', *msg)

