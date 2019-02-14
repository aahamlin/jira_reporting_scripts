#import sys
import unittest
#import re
#import io

#try:
#    from contextlib import redirect_stdout
#except ImportError:
#    from contextlib2 import redirect_stdout

from qjira.config import settings

#from . import test_data
from . import test_util

class BaseCommandTestCase(test_util.BaseTestCase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):    
        if not settings.has_section('test'):
            settings.add_section('test')
        settings.set('test', 'headers', 'summary')

    def setUp(self):
        self.command = test_util.TestCommand(project=['Test'], base_url='http://localhost:3000')

    def test_headers(self):
        """Commands define their header keys mapped to human-readable names.
        
        Each header key is mapped to a human-readable name stored in [headers] section.
        """
        self.assertEqual({u'summary': u'Summary'}, self.command.header)

    def test_headers_with_format(self):
        """Commands define their header keys mapped to human-readable names.
        
        Each header key is mapped to a human-readable name stored in [headers] section.
        """
        self.assertEqual({u'summary': u'Summary'}, self.command.header)

class BaseCommandNonMappedHeaderTestCase(test_util.BaseTestCase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):    
        if not settings.has_section('test'):
            settings.add_section('test')
        settings.set('test', 'headers', 'non_mapped_key')


    def setUp(self):
        self.command = test_util.TestCommand(project=['Test'], base_url='http://localhost:3000')

    def test_headers(self):
        """Commands define their header keys. Unmapped names default to keys.
        
        Each header key is mapped to a human-readable name stored in [headers] section.
        """
        self.assertEqual({u'non_mapped_key': u'non_mapped_key'}, self.command.header)

class BaseCommandHeaderWithFormatTestCase(test_util.BaseTestCase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):    
        if not settings.has_section('test'):
            settings.add_section('test')
        settings.set('test', 'headers', 'timeoriginalestimate')


    def setUp(self):
        self.command = test_util.TestCommand(project=['Test'], base_url='http://localhost:3000')

    def test_headers_with_format(self):
        """Header including format only returns Name portion."""
        self.assertEqual({u'timeoriginalestimate': u'Original Estimate (Days)'}, self.command.header)


class BaseCommandHeaderMissingRequiredValueTestCase(test_util.BaseTestCase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):    
        if not settings.has_section('test'):
            settings.add_section('test')
        settings.set('test', 'headers', 'empty_mapped_key')
        
        if not settings.has_section('headers'):
            settings.add_section('headers')
        settings.set('headers', 'empty_mapped_key', '')

        
    @classmethod
    def tearDownClass(cls):
        if settings.has_section('headers'):
            settings.remove_option('headers', 'empty_mapped_key')

    def test_headers_with_empty_value(self):
        """Raise exception"""

        with self.assertRaisesRegex_(ValueError, 'missing required value'):
            test_util.TestCommand(project=['Test'], base_url='http://localhost:3000')

class BaseCommandHeaderMissingFormatterTestCase(test_util.BaseTestCase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):    
        if not settings.has_section('test'):
            settings.add_section('test')
        settings.set('test', 'headers', 'non_existent_formatter')
        
        if not settings.has_section('headers'):
            settings.add_section('headers')
        settings.set('headers', 'non_existent_formatter', 'NameOnly:undefined_formatter')

        
    @classmethod
    def tearDownClass(cls):
        if settings.has_section('headers'):
            settings.remove_option('headers', 'non_existent_formatter')

    def test_headers_with_nonexistent_format(self):
        """Raise exception"""
        with self.assertRaisesRegex_(ValueError, 'defines non-existent formatter'):
            test_util.TestCommand(project=['Test'], base_url='http://localhost:3000')

class BaseCommandHeaderWithFormatterTestCase(test_util.BaseTestCase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):    
        if not settings.has_section('test'):
            settings.add_section('test')
        settings.set('test', 'headers', 'issue_key,timeoriginalestimate,timespent')

    def setUp(self):
        self.command = test_util.TestCommand(project=['Test'], base_url='http://localhost:3000')
        
    def test_header_without_format(self):
        fn = self.command.field_formatter('issue_key')
        self.assertEqual(fn('ABC-123'), 'ABC-123')
        
    def test_header_with_format(self):
        fn = self.command.field_formatter('timeoriginalestimate')
        self.assertEqual(fn(8*60*60), u'1.00')
