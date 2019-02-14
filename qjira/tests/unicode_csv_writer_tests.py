import sys
import unittest
import re
import io

try:
    from contextlib import redirect_stdout
except ImportError:
    from contextlib2 import redirect_stdout

import qjira.unicode_csv_writer as csv_writer

from qjira.config import settings

from . import test_data
from . import test_util

PY3 = sys.version_info > (3,)

class BaseUnicodeWriterTestCase(test_util.BaseTestCase, test_util.MockJira, unittest.TestCase):

    @classmethod
    def setUpClass(cls):    
        if not settings.has_section('test'):
            settings.add_section('test')
        settings.set('test', 'headers', 'summary')

    def setUp(self):
        '''Setup for unicode tests require special handling for python version.'''
        self.std_out = io.StringIO() if PY3 else io.BytesIO()

        self.setup_mock_jira()

        self.json_response = {
            'total': 1,
            'issues': [test_data.singleSprintStory()]
        }

        # delegate to non-abstract test case
        self._setup()

    def _setup(self):
        self.command = test_util.TestCommand(project=['TEST'], base_url='localhost:3000')

    def tearDown(self):
        self.teardown_mock_jira()

class UnicodeWriterTestCase(BaseUnicodeWriterTestCase):
    
    def test_unicode_writer_encodes_ascii(self):
        '''Test that csv encoding converts unicode to ascii'''
        utf8_re = re.compile('\u201c.+\u201d', flags=re.UNICODE)
        with redirect_stdout(self.std_out):
            csv_writer.write(sys.stdout, self.command, 'ASCII')
        self.assertNotRegex_(self.std_out.getvalue(), utf8_re)
        
    def test_header_written_ok(self):
        with redirect_stdout(self.std_out):
            csv_writer.write(sys.stdout, self.command, 'ASCII')
        cols = test_util.getColumns(self.std_out.getvalue())
        self.assertEqual(1, len(cols))

    @unittest.skipIf(sys.version_info < (3,),
                     'This version of csv module does not support utf8 encoding')
    def test_unicode_writer_encodes_utf8(self):
        '''Test that csv encoding supports utf-8 option.'''
        utf8_re = re.compile('\u201c.+\u201d', flags=re.UNICODE)
        with redirect_stdout(self.std_out):
            csv_writer.write(sys.stdout, self.command, 'UTF-8')
        self.assertRegex_(self.std_out.getvalue(), utf8_re)

class AllFieldsTestCase(BaseUnicodeWriterTestCase):

    def _setup(self):
        self.command = test_util.TestCommand(project=['TEST'], base_url='localhost:3000', all_fields=True)

    def test_header_written_ok(self):
        self.assertTrue(self.command.show_all_fields)
        with redirect_stdout(self.std_out):
            csv_writer.write(sys.stdout, self.command, 'ASCII')
        cols = test_util.getColumns(self.std_out.getvalue())
        self.assertTrue(1 < len(cols))

class UnicodeWriterCallsFormattersTestCase(test_util.BaseTestCase, test_util.MockJira, unittest.TestCase):

    @classmethod
    def setUpClass(cls):    
        if not settings.has_section('test'):
            settings.add_section('test')
        settings.set('test', 'headers', 'summary,timeoriginalestimate,timespent')

    def setUp(self):
        '''Setup for unicode tests require special handling for python version.'''
        self.std_out = io.StringIO() if PY3 else io.BytesIO()

        self.setup_mock_jira()

        self.json_response = {
            'total': 1,
            'issues': [test_data.singleSprintStoryByTime()]
        }

        # delegate to non-abstract test case
        self._setup()

    def _setup(self):
        self.command = test_util.TestCommand(project=['TEST'], base_url='localhost:3000')

    def tearDown(self):
        self.teardown_mock_jira()

    def test_headers_ok(self):
        with redirect_stdout(self.std_out):
            csv_writer.write(sys.stdout, self.command, 'ASCII')
        cols = test_util.getColumns(self.std_out.getvalue())
        self.assertEqual(3, len(cols))

    def test_formatted_values(self):
        with redirect_stdout(self.std_out):
            csv_writer.write(sys.stdout, self.command, 'ASCII')
        cols = test_util.getColumns(self.std_out.getvalue(), lineno=1)
        self.assertEqual(3, len(cols))
        # summary, 28800, 14400
        vals = cols[1:]
        self.assertEqual([u'1.00', u'0.50'], vals)
