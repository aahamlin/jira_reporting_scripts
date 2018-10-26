""" Command base class for processing Jira issues"""
import abc
import copy
import re
from functools import partial
from collections import OrderedDict

from .. import jira
from .. import dataprocessor as dp
from .. import unicode_csv_writer

from ..log import Log
from ..config import settings
        
def query_builder(name, items):
    return '{0} in ({1})'.format(name, ','.join(items))

class BaseCommand:

    __metaclass__ = abc.ABCMeta
    
    def __init__(self, name, pivot_field=None,
                 base_url=None, project=[],
                 fixversion=[], all_fields=False,
                 settings=settings,
                 *args, **kwargs):
        '''Initialize a command.
        
        Required Arguments:

        name - name of command and config section
        project - list of JIRA Project keys
        base_url -- JIRA Cloud instance, e.g. your-company.atlassian.net

        Optional Arguments:

        fixversion - list of FixVersion values
        '''
        if not base_url:
            raise TypeError('Missing keyword "base_url"')

        self._name = name
        self._projects = project
        self._base_url = base_url
        self._fixversions = fixversion
        self._all_fields = all_fields
        self._pivot_field = pivot_field
        self._settings = settings

        effort_engine_name = settings.get('jira','default_effort_engine')
        self._effort_engine = dict(settings.items(effort_engine_name))
        
        self.kwargs = kwargs
        
    def _configure_http_request(self):
        '''Sub-classes can continue currying this function.'''
        return partial(jira.all_issues,
                       self._base_url,
                       fields=self._get_jira_fields(),
                       **self.kwargs)

    @property
    def show_all_fields(self):
        return self._all_fields

    @property
    def header(self):
        '''
        Return OrderedDict of CSV column keys and user-friendly names.
        '''
        header_keys = settings.get(self._name, 'headers').split(',')
        header = OrderedDict(zip(header_keys, header_keys))
        header.update({k:v for k,v in settings.items('headers') if k in header.keys()})
        return header
    
    @property
    def header_keys(self):
        '''Return the list of CSV column keys to print.

        See also, expand_header.
        '''
        return list(self.header.keys())

    @property
    def query(self):
        '''Return the JQL query for this command.'''
        #raise NotImplementedError()
        return settings.get(self._name, 'query')

    @property
    def writer(self):
        '''Return the writer interface for this command.

        Defines a single function matching: unicode_csv_writer.write'''
        return unicode_csv_writer
    
    def retrieve_fields(self, default_fields):
        '''Command may provide a set of Jira Fields. The provided list is
        a copy of the default that can be modified, appended or replaced.

        Argument:
        default_fields - list of default Jira fields
        '''
        return default_fields

    @property
    def count_fields(self):
        return []

    @property
    def datetime_fields(self):
        return ['lastViewed', 'created', 'updated']

    @property
    def pivot_field(self):
        return self._pivot_field

    
    def _create_query_string(self):
        query = []
        if self._projects:
            query.append(query_builder('project', self._projects))
        if self._fixversions:
            query.append(query_builder('fixversion', self._fixversions))
        query.append(self.query)
        return ' AND '.join(query)

    def _get_jira_fields(self):
        if self.show_all_fields:
            return self.retrieve_fields(['*navigable'])
        else:
            return self.retrieve_fields(jira.default_fields())

    def expand_header(self, d):
        '''Return a list of column names from a dict object.

        If the command was launched with the show_all_fields option or does not supply a header list, 
        then use all keys of the provided row.

        Note: When using show_all_fields, only keys in the FIRST row will be returned!
 
        Otherwise, return the defined set of fields from the header property.
        '''
        if self.show_all_fields or not self.header:
            return d.keys()
        else:
            return self.header_keys
        
    def http_request(self):
        query_string = self._create_query_string()
        base_request = self._configure_http_request()
        req = base_request(query_string)
        Log.debug('http_request: {0}'.format(req))
        return req

    def pre_process(self, generate_data):
        '''Return a generator from the source generator. Include pivot
        on a field to generate new rows from the list.
        '''
        Log.debug('pre_process: {0}'.format(generate_data))

        pivot_on = self.pivot_field
        for x in generate_data:
            if pivot_on and pivot_on in x and x[pivot_on]:
                pivots = copy.copy(x[pivot_on])
                del x[pivot_on]
                Log.debug('Pivot on field {0}, {1} item(s)'.format(pivot_on, len(pivots)))
                #print('> pivot on {0} sprints'.format(len(sprints)))
                # Create new json object for each pivot field
                for pivot in pivots:
                    #print('> next sprint: {0}'.format(sprint['name']))
                    y = {pivot_on: pivot}
                    y.update(x.copy())
                    yield y
            else:
                yield x

    
    def post_process(self, generate_rows):
        '''Override to construct a new row generator from the source generator'''
        Log.debug('post_process: {0}'.format(generate_rows))
        return generate_rows

    def execute(self):
        flatten_rows = partial(dp.flatten_json_struct,
                               count_fields=self.count_fields,
                               datetime_fields=self.datetime_fields)
        http_req = self.http_request()
        generate_rows = ({k:v for k,v in flatten_rows(x)}
                         for x in self.pre_process(http_req))
        Log.debug('execute: {0}'.format(generate_rows))
        return self.post_process(generate_rows)
