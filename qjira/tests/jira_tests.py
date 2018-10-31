import unittest
import json
import datetime

from functools import partial

import qjira.jira as j
from qjira.log import Log
from qjira.dataprocessor import load_changelog

from . import test_data
from . import test_util

TEST_BASE_URL = 'http://localhost:3000'

class TestJiraFunc(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.setup_mock_jira()

    def tearDown(self):
        self.teardown_mock_jira()
                
    def test_get_project_issues(self):
        """test that all expected fields are urlencoded properly""" 

        expectedUrl = 'http://localhost:3000/rest/api/2/search?fields=-%2Anavigable%2Cproject%2Cissuetype%2Cstatus%2Csummary%2Cassignee%2CfixVersions%2Ccustomfield_10109%2Ccustomfield_10016%2Ccustomfield_10017&jql=issuetype+%3D+Story&maxResults=50&expand=changelog&startAt=0&'
        try:
            next(j.all_issues(TEST_BASE_URL, 'issuetype = Story'))
        except StopIteration:
            pass

        self.assertUrlPartsEqual(expectedUrl, self.actual_url)

    def test_get_browse_url(self):
        url = j.get_browse_url(TEST_BASE_URL, 'IIQETN-1')
        self.assertEqual('http://localhost:3000/browse/IIQETN-1', url)

    def test_get_issue(self):
        """Test that getting a single issue urlencodes properly"""
        self.json_response = {'key': 123, 'fields': {}, 'changelog': []}
        expectedUrl = 'http://localhost:3000/rest/api/2/issue/IIQETN-1'
        j.get_issue(TEST_BASE_URL, 'IIQETN-1')
        self.assertUrlPartsEqual(expectedUrl, self.actual_url)
        
    def test_as_data(self):
        issue = test_data.singleSprintStory()
        issue['fields']['customfield_10017'] = 'epic-key'
        issue['fields']['customfield_10400'] = ['foo']
        issue['fields']['customfield_10112'] = 'severity-field'
        self.json_response = {'total': 1, 'issues': [issue]}
        data = next(j.all_issues(TEST_BASE_URL, 'issuetype = Story'))
        load_changelog(data)
        self.assertDictContainsSubset(
            {
                'issue_key':124,
                'story_points': 3.0,
                'testplan_doc_link': 'https://harbor.sailpoint.com/docs/DOC-20236',
                'design_doc_link': 'https://harbor.sailpoint.com/docs/DOC-19296',
                'severity': 'severity-field',
                'epic_issue_key': 'epic-key',
                'customer': ['foo'],
                'status_InProgress': datetime.date(2017, 1, 25),
                'status_Done': datetime.date(2017, 1, 26),
                'eng_test_plan_changed': datetime.date(2017, 6, 21),
                'eng_design_changed': datetime.date(2017, 6, 21)
            },
            data)
        self.assertEqual(1, len(data['sprint']))
        
