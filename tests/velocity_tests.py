from . import test_context

import unittest

from qjira.velocity import VelocityCommand
import qjira.jira as j

from . import test_data
from . import test_util

class TestVelocity(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.setup_mock_jira(j)
        self.command_under_test = VelocityCommand(base_url='localhost:3000', project=['TEST'])
        
    def tearDown(self):
        self.teardown_mock_jira(j)
        
    def test_header(self):
        self.assertIsInstance(self.command_under_test.header, list)
        
    def test_query(self):
        self.assertEqual('issuetype = Story', self.command_under_test.query)

    def test_process_0(self):
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 0)
        
    def test_process(self):
        '''The velocity command will calculate the planned points when a story 
        enters a sprint,
        the carried points when a story is not complete and enters a new sprint,
        the completed points when a story is finished in a sprint
        '''
        self.json_response = {
            'total': 1,
            'issues': [test_data.multiSprintStory()]
        }
        data = list(self.command_under_test.execute())

        self.assertEqual(len(data), 2)
        self.assertDictContainsSubset({'planned_points': 3.0,
                                       'carried_points': 0.0,
                                       'completed_points': 0.0},
                                      data[0])
        self.assertDictContainsSubset({'planned_points': 0.0,
                                       'carried_points': 3.0,
                                       'completed_points': 3.0},
                                      data[1])
        self.assertIsNotNone(data[0]['sprint_id'])
        self.assertIsNotNone(data[1]['sprint_id'])
        self.assertNotEqual(data[0]['sprint_id'], data[1]['sprint_id'])

    def test_process_no_sprint(self):
        self.json_response = {
            'total': 1,
            'issues': [test_data.noSprintStory()]
        }
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 0)

    def test_process_zero_points(self):
        self.json_response = {
            'total': 1,
            'issues': [test_data.zeroPointStory()]
        }
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 1)
        with self.assertRaises(KeyError):
            data[0]['story_points']

class TestVelocityWithBugs(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.setup_mock_jira(j)
        self.command_under_test = VelocityCommand(base_url='localhost:3000', project=['TEST'], include_bugs=True)

    def tearDown(self):
        self.teardown_mock_jira(j)

    def test_query(self):
        self.assertEqual('issuetype in (Story, Bug)', self.command_under_test.query)

    def test_process_include_bugs(self):
        '''Bugs will have story_points calculated successfully'''
        self.json_response = {
            'total': 1,
            'issues': [test_data.simpleBug()]
        }
        
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 1)
        self.assertDictContainsSubset({'planned_points': 3.0,
                                       'carried_points': 0.0,
                                       'completed_points': 3.0},
                                      data[0])


