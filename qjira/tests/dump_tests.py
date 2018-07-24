import sys
import io
import unittest
import keyring
import keyring.backend

from requests.exceptions import HTTPError
from requests import Response

try:
    from contextlib import redirect_stdout, redirect_stderr
except ImportError:
    from contextlib2 import redirect_stdout, redirect_stderr

import qjira.__dump__ as prog

from . import test_util
from . import test_data
from .main_tests import TestableKeyring

PY3 = sys.version_info > (3,)

class TestDumpCLI(test_util.MockJira, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        keyring.set_keyring(TestableKeyring())
        
    def setUp(self):
        keyring.get_keyring().entries['qjira-sp_userb'] = 'xyzzy'
        self.std_out = io.StringIO() if PY3 else io.BytesIO()
        self.std_err = io.StringIO() if PY3 else io.BytesIO()
        self.setup_mock_jira()

    def tearDown(self):
        self.teardown_mock_jira()
    
    def test_dump_command(self):
        self.json_response = {
            'total': 1,
            'issues': [test_data.singleSprintStory()]
        }

        with redirect_stdout(self.std_out):
            with redirect_stderr(self.std_err):
                prog.main([ '-w', 'blah','ABC-123'])

        print(self.std_out.getvalue())
        
