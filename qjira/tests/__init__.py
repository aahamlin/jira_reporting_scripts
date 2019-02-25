"""Test module for qjira"""
from . import test_context
import unittest
import os

from . import jira_tests
from . import log_tests
from . import base_command_tests
from . import unicode_csv_writer_tests
from . import velocity_tests
from . import cycletime_tests
from . import summary_tests
from . import techdebt_tests
from . import backlog_tests
from . import jql_tests
from . import worklog_tests
from . import dataprocessor_tests
from . import main_tests
from . import dump_tests

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(dataprocessor_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(jira_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(log_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(base_command_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(unicode_csv_writer_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(velocity_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(cycletime_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(summary_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(techdebt_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(backlog_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(jql_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(worklog_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(main_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(dump_tests))
    
    return suite

def __suite():
    suite = unittest.TestSuite()
    #suite.addTest(velocity_tests.TestVelocity('test_process'))
    #suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(unicode_csv_writer_tests))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(worklog_tests))
    return suite

if __name__ == '__main__':
    testrunner = unittest.TextTestRunner()
    testrunner.run(suite())

