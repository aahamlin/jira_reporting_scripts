# -*- coding: utf-8 -*-
'''
config.py
Author: Andrew Hamlin
Description: library to load configuration settings.
'''
import os

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

INSTALLPATH = os.path.dirname(os.path.abspath(__file__))

def read_config():
    '''Create basic configuration'''
    config = configparser.ConfigParser()
    config.readfp(open(os.path.join(INSTALLPATH, 'defaults.ini')))
    config.read([os.path.expanduser('~/.qjira')])
    return config

settings = read_config()
