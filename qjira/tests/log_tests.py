""" Tests of the simplistic logging facility.
Note these are currently skipped on python 2.7. The contextlib2 documentation
states that it requires unittest2 for Python 2.x and this has not been done yet.
"""
import sys
import io
import unittest

try:
    from contextlib import redirect_stderr
except ImportError:
    from contextlib2 import redirect_stderr

from qjira.log import Log

PY3 = sys.version_info[0] > 2

class LogTest(unittest.TestCase):

    def setUp(self):
        self.std_err = io.StringIO() if PY3 else io.BytesIO()
        Log.debugLevel = 0

    def tearDown(self):
        Log.debugLevel = 0

    def test_error(self):
        with redirect_stderr(self.std_err):
            Log.error('hello')
        output = self.std_err.getvalue()
        self.assertEqual('[ERROR] hello\n', output)

    def test_info(self):
        Log.debugLevel = 1
        with redirect_stderr(self.std_err):
            Log.info('hello')
        self.assertEqual('[INFO] hello\n', self.std_err.getvalue())

    def test_debug(self):
        Log.debugLevel = 2
        with redirect_stderr(self.std_err):
            Log.debug('hello')
        self.assertEqual('[DEBUG] hello\n', self.std_err.getvalue())

    def test_verbose(self):
        Log.debugLevel = 3
        with redirect_stderr(self.std_err):
            Log.verbose('hello')
        self.assertEqual('[VERBOSE] hello\n', self.std_err.getvalue())

