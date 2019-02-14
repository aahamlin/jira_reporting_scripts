import unittest
import datetime

from qjira.commands import WorklogCommand
from qjira.config import settings

from . import test_data
from . import test_util

class TestWorklogAuthorFilterTestCase(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.setup_mock_jira()
        self.command_under_test = WorklogCommand(base_url='localhost:3000', author=['Andrew.Hamlin'])
        
    def tearDown(self):
        self.teardown_mock_jira()
        
    def test_header(self):
        self.assertIsInstance(self.command_under_test.header_keys, list)

    def test_process(self):
        """worklog returns hours per worklog author.

        output includes string version of worklog start date and float to 3 digits."""
        self.json_response = (x for x in [{
            'total': 1,
            'issues': [
                test_data.singleSprintStory()
            ]
        },
        {
            'total': 3,
            'worklogs': [
                {
                    "author": {
                        "name": "andrew.hamlin",
                        "displayName": "Andrew Hamlin",
                        "active": True,
                        "timeZone": "America/New_York"
                    },
                    "comment": "worked more than estimate",
                    "started": "2018-04-05T10:39:00.000-0400",
                    "timeSpentSeconds": 86400,
                },
                {
                    "author": {
                        "name": "andrew.hamlin",
                        "displayName": "Andrew Hamlin",
                        "active": True,
                        "timeZone": "America/New_York"
                    },
                    "comment": "worked more than estimate",
                    "started": "2018-04-05T10:39:00.000-0400",
                    "timeSpentSeconds": 14400,
                },
                {
                    "author": {
                        "name": "someone.else",
                        "displayName": "Someone Else",
                        "active": True,
                        "timeZone": "America/New_York"
                    },
                    "comment": "worked more than estimate",
                    "started": "2018-04-05T10:39:00.000-0400",
                    "timeSpentSeconds": 28800,
                },
            ]
        }])
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 1)
        self.assertDictContainsSubset({
            'worklog_author_name':'andrew.hamlin',
            'worklog_timeSpentDays':'3.500',
            'worklog_started':str(datetime.date(2018, 4, 5))
        }, data[0])

class TestWorklogMultiAuthorFilterTestCase(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.setup_mock_jira()
        self.command_under_test = WorklogCommand(base_url='localhost:3000', author=['Andrew.Hamlin', 'Someone.Else'])
        
    def tearDown(self):
        self.teardown_mock_jira()
        
    def test_header(self):
        self.assertIsInstance(self.command_under_test.header_keys, list)

    def test_process(self):
        """worklog returns hours per worklog author.

        output includes string version of worklog start date and float to 3 digits."""
        self.json_response = (x for x in [{
            'total': 1,
            'issues': [
                test_data.singleSprintStory()
            ]
        },
        {
            'total': 3,
            'worklogs': [
                {
                    "author": {
                        "name": "andrew.hamlin",
                        "displayName": "Andrew Hamlin",
                        "active": True,
                        "timeZone": "America/New_York"
                    },
                    "comment": "worked more than estimate",
                    "started": "2018-04-05T10:39:00.000-0400",
                    "timeSpentSeconds": 86400,
                },
                {
                    "author": {
                        "name": "andrew.hamlin",
                        "displayName": "Andrew Hamlin",
                        "active": True,
                        "timeZone": "America/New_York"
                    },
                    "comment": "worked more than estimate",
                    "started": "2018-04-05T10:39:00.000-0400",
                    "timeSpentSeconds": 14400,
                },
                {
                    "author": {
                        "name": "someone.else",
                        "displayName": "Someone Else",
                        "active": True,
                        "timeZone": "America/New_York"
                    },
                    "comment": "worked more than estimate",
                    "started": "2018-04-05T10:39:00.000-0400",
                    "timeSpentSeconds": 28800,
                },
            ]
        }])
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 2)
        self.assertDictContainsSubset({
            'worklog_author_name':'andrew.hamlin',
            'worklog_timeSpentDays':'3.500',
            'worklog_started':str(datetime.date(2018, 4, 5))
        }, data[0])
        self.assertDictContainsSubset({
            'worklog_author_name':'someone.else',
            'worklog_timeSpentDays':'1.000',
            'worklog_started':str(datetime.date(2018, 4, 5))
        }, data[1])
