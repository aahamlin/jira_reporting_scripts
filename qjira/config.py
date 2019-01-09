# -*- coding: utf-8 -*-
'''
config.py
Author: Andrew Hamlin
Description: library to load configuration settings.
'''
import os

from .log import Log

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

INSTALLPATH = os.path.dirname(os.path.abspath(__file__))

def read_config():
    '''Create basic configuration'''
    config = configparser.ConfigParser()
    Log.debug("INSTALLPATH = %s" % INSTALLPATH)
    config.readfp(open(os.path.join(INSTALLPATH, 'defaults.ini')))
    if not os.getenv('QJIRA_TESTMODE'):
        Log.debug("user config = %s" % os.path.expanduser('~/.qjira.ini'))
        config.read([os.path.expanduser('~/.qjira.ini')])
    return config

settings = read_config()

