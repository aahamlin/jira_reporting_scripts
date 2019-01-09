import datetime
import unittest

from qjira.commands import CycleTimeCommand

from . import test_data
from . import test_util

class TestCycleTime(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.setup_mock_jira()
        self.command_under_test = CycleTimeCommand(base_url='localhost:3000', project=['TEST'])

    def tearDown(self):
        self.teardown_mock_jira()
        
    def test_header(self):
        self.assertIsInstance(self.command_under_test.header_keys,
                              list)

    def test_query(self):
        self.assertEqual(self.command_under_test.query,
                          'issuetype = Story AND status in (Done, Accepted)')

    def test_process(self):
        self.json_response = {
            'total': 1,
            'issues': [test_data.multiSprintStory()]
        }
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 1)
        # cycletime command will record the in-progress to done dates 
        self.assertDictContainsSubset(
            {'cycle_begin': datetime.date(2017, 1, 30), 'cycle_end':  datetime.date(2017, 1, 31)}, data[0])

    def test_process_done_wo_progress(self):
        self.json_response = {
            'total': 1,
            'issues': [test_data.doneWithNoProgress()]
        }
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 1)
        # cycletime command will record the in-progress to done dates
        self.assertDictContainsSubset(
            {'cycle_end':  datetime.date(2017, 1, 31)}, data[0])
        with self.assertRaises(KeyError):
            data[0]['cycle_begin']

    def test_process_accepted(self):
        self.json_response = {
            'total': 1,
            'issues': [test_data.acceptedStory()]
        }
        data = list(self.command_under_test.execute())

        self.assertEqual(len(data), 1)
        # cycletime command will record the in-progress to done dates 
        self.assertDictContainsSubset(
            {'cycle_begin': datetime.date(2017, 1, 30), 'cycle_end':  datetime.date(2017, 1, 31)}, data[0])

    def test_process_story_cycle_times_negativedays_fix(self):
        self.json_response = {
            'total': 1,
            'issues': [test_data.negativeHistoryStory()]
        }
        data = list(self.command_under_test.execute())
        
        self.assertEqual(len(data), 1)
        self.assertDictContainsSubset({
            'cycle_begin': datetime.date(2017,1,30),
            'cycle_end': datetime.date(2017,1,31)
        }, data[0])
    
