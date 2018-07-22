'''Add the module under test onto the sys.path'''
import os
import sys
import locale

# matches __main__.py locale
locale.setlocale(locale.LC_TIME, 'en_US')

print('adding parent directory to sys.path')
print(os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('..'))
