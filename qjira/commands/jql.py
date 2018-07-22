from collections import OrderedDict

from ..config import settings
from .command import PivotCommand
from .. import jira
from .. import headers

class JQLCommand(PivotCommand):
    '''JQL command runs any valid JQL query string.

    Given a list of add_field the Jira query string be appended with additional non-default fields to retrieve.
    Given a list of add_column the CSV report will add additional columns to the output.

    TODO: Mapping from Jira fields to column names (such as 'customfield_10112' to 'severity') is not taken
    into account. Refer to qjira/jira.py for the set of mappings.
    '''

    DEFAULT_COLUMN_NAMES = settings['jql']['default_cols'].split(',')
    
    def __init__(self, jql=None, add_field=None, add_column=None, pivot_field=None, *args, **kwargs):
        super(JQLCommand, self).__init__(*args, **kwargs)

        if not jql:
            raise TypeError('Missing keyword "jql"')

        self._jql = jql
        self._add_fields = add_field
        self._add_columns = add_column
        self.pivot_field = pivot_field

    @property
    def pivot_field(self):
        return self._pivot_field

    @pivot_field.setter
    def pivot_field(self, f):
        self._pivot_field = f
            
    @property
    def header(self):
        '''JQL command returns all fields.
        '''
        columns =  JQLCommand.DEFAULT_COLUMN_NAMES
        if self._add_columns and len(self._add_columns)>0:
            columns += self._add_columns
            
        return OrderedDict([headers.get_column(n) for n in columns])
    
    @property
    def query(self):
        '''Return the user-provided JQL query'''
        return self._jql

    def retrieve_fields(self, fields):
        if self._add_fields and len(self._add_fields)>0:
            return fields + self._add_fields
        else:
            return fields
