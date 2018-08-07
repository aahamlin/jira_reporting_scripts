import unittest
#import datetime
#from copy import copy
import sys
import io
from collections import OrderedDict

from qjira.commands import BaseCommand
from qjira import Log

from qjira.config import settings

from . import test_data
from . import test_util


PY3 = sys.version_info > (3,)


class TestCommand(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(TestCommand, self).__init__('test', *args, **kwargs)
    
    # @property
    # def header(self):
    #     return OrderedDict([('summary', 'Summary')])

    @property
    def query(self):
        return ''

class BaseCommandTestCase(test_util.SPTestCase, test_util.MockJira, unittest.TestCase):

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
        self.command = TestCommand(project=['TEST'], base_url='localhost:3000')

    def tearDown(self):
        self.teardown_mock_jira()

    def getColumns(self, val):
        lines = val.splitlines()
        cols = lines[0].split(',')
        return cols

class CommandTestCase(BaseCommandTestCase):

    def test_headers(self):
        self.assertEqual({u'summary': u'Summary'}, self.command.header)
        raise AssertionError('TODO: Update command header & header_keys to combine default_effort_engine header with specific command header.')
