#from . import test_context

import unittest
import datetime
from copy import copy

from qjira.commands import VelocityCommand
from qjira import Log

from qjira.config import settings

from . import test_data
from . import test_util

class TestVelocity(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.setup_mock_jira()
        self.command_under_test = VelocityCommand(base_url='localhost:3000', project=['TEST'])
        
    def tearDown(self):
        self.teardown_mock_jira()
        
    def test_header(self):
        self.assertIsInstance(self.command_under_test.header_keys, list)
        
    def test_query(self):
        self.assertEqual('issuetype = Story', self.command_under_test.query)

    def test_process_0(self):
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 0)

    def test_process(self):
        '''The velocity command will calculate the planned points when a story 
        enters a sprint, the carried points when a story is not complete and
        enters a new sprint, the completed points when a story is finished in 
        a sprint.

        sprint_name | planned | carried | total | completed
        My sprint     3.0       0.0       3.0     3.0

        '''
        self.json_response = {
            'total': 2,
            'issues': [
                test_data.multiSprintStory(),
                test_data.singleSprintStory()
            ]
        }
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 2)
        self.assertDictContainsSubset({
            'sprint_name':'Chambers Sprint 9',
            'planned_effort': 6.0,
            'carried_effort': 0.0,
            'story_points': 6.0,
            'completed_effort': 3.0
        }, data[0])
        self.assertDictContainsSubset({
            'sprint_name': 'Chambers Sprint 10',
            'planned_effort': 0.0,
            'carried_effort': 3.0,
            'story_points': 3.0,
            'completed_effort': 3.0
        }, data[1])

    def test_process_bugs_in_stories_only(self):
        '''Test that bug points calculations are constrained to story-related sprints.

        In this test, a bug is retrieved from a different sprint than the story. It's 
        points will not be included, result set includes only 1 story.'''

        self.command_under_test._include_bugs = True
        self.json_response = {
            'total': 2,
            'issues': [
                test_data.singleSprintStory(),
                test_data.simpleBug()
            ]
        }
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 1)
        self.assertDictContainsSubset({
            'sprint_name':'Chambers Sprint 9',
            'planned_effort': 3.0,
            'carried_effort': 0.0,
            'story_points': 3.0,
            'completed_effort': 3.0
        }, data[0])

    def test_process_bugs_in_filtered_range_min(self):
        '''Test that bug points calculations respect a date filter (min).'''
        self.command_under_test._include_bugs = True
        self.json_response = {
            'total': 2,
            'issues': [
                test_data.singleSprintStory(),
                test_data.simpleBug()
            ]
        }
        
        self.command_under_test._filter_by_date = datetime.date.min
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 2)

        
    def test_process_bugs_in_filtered_range_max(self):
        '''Test that bug points calculations respect a date filter (max).'''
        self.command_under_test._include_bugs = True
        self.json_response = {
            'total': 2,
            'issues': [
                test_data.singleSprintStory(),
                test_data.simpleBug()
            ]
        }

        self.command_under_test._filter_by_date = datetime.date.max
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 1)

    def test_process_without_sprint_startDate_in_filtered_range(self):
        '''Test that a future item will be included with a filter by date.'''
        self.command_under_test._filter_by_date = datetime.date.today()
        self.command_under_test._forecast = True
        self.json_response = {
            'total': 1,
            'issues': [
                test_data.future_sprint_story()
            ]
        }
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 1)

class TestVelocityWithBugs(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.setup_mock_jira()
        self.command_under_test = VelocityCommand(base_url='localhost:3000', project=['TEST'], include_bugs=True, filter_by_date=datetime.date(2017, 6, 15))

    def tearDown(self):
        self.teardown_mock_jira()

    def test_query(self):
        self.assertEqual('issuetype in (Story, Bug)', self.command_under_test.query)

    def test_process_include_bugs(self):
        '''Bugs will have effort_value calculated successfully'''
        self.json_response = {
            'total': 1,
            'issues': [test_data.simpleBug()]
        }
        
        data = list(self.command_under_test.execute())
        
        self.assertEqual(len(data), 1)
        self.assertDictContainsSubset({'planned_effort': 3.0,
                                       'carried_effort': 0.0,
                                       'completed_effort': 3.0},
                                      data[0])

class TestVelocityWithForecast(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.setup_mock_jira()
        self.command_under_test = VelocityCommand(base_url='localhost:3000', project=['TEST'], forecast=True)

    def tearDown(self):
        self.teardown_mock_jira()

    def test_process_includes_future_sprint(self):
        '''Forecasting will include sprints that are defined (e.g. with start and end date) but have not completed.

        Sprints should be sorted by sprint startDate.

        The no sprint story test data includes a 3 point story that has no defined sprint.
        '''
        self.json_response = {
            'total': 2,
            'issues': [
                test_data.in_progress_story(),
                test_data.noSprintStory()
            ]
        }
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 1)
        self.assertDictContainsSubset({
            'planned_effort': 5.0,
            'carried_effort': 0.0,
            'completed_effort': 0.0
        }, data[0])

class TestVelocityTimeOriginalEstimate(test_util.MockJira, unittest.TestCase):

    def setUp(self):
        self.setup_mock_jira()
        self._effort_field = settings['effort_engine']['effort_field']
        settings.set('effort_engine','effort_field','timeoriginalestimate')
        self.command_under_test = VelocityCommand(base_url='localhost:3000', project=['TEST'])
        
    def tearDown(self):
        self.teardown_mock_jira()
        settings.set('effort_engine','effort_field', self._effort_field)


    def test_settings(self):
        '''Velocity Command will process timeoriginalestimate setting'''
        self.assertEqual(u'timeoriginalestimate', self.command_under_test._effort_field)

    def test_process(self):
        '''The velocity command will calculate the planned original estimate when a story 
        enters a sprint, the carried estimate when a story is not complete and
        enters a new sprint, the completed estimate when a story is finished in 
        a sprint.

        sprint_name | planned | carried | total | completed
        My sprint     3.0       0.0       3.0     3.0

        '''
        self.json_response = {
            'total': 2,
            'issues': [
                test_data.multiSprintStoryByTime(),
                test_data.singleSprintStoryByTime()
            ]
        }
        data = list(self.command_under_test.execute())
        self.assertEqual(len(data), 2)
        self.assertDictContainsSubset({
            'sprint_name':'Chambers Sprint 9',
            'planned_effort': 57600,
            'carried_effort': 0,
            'timeoriginalestimate': 57600,
            'completed_effort': 28800
        }, data[0])
        self.assertDictContainsSubset({
            'sprint_name': 'Chambers Sprint 10',
            'planned_effort': 0,
            'carried_effort': 28800,
            'timeoriginalestimate': 28800,
            'completed_effort': 28800
        }, data[1])
    
