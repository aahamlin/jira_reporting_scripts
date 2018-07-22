from collections import OrderedDict

from ..config import settings
from .command import BaseCommand
from .. import jira


class JQLCommand(BaseCommand):
    '''JQL command runs any valid JQL query string.

    Given a list of add_field the Jira query string be appended with additional non-default fields to retrieve.
    Given a list of add_column the CSV report will add additional columns to the output.

    TODO: Mapping from Jira fields to column names (such as 'customfield_10112' to 'severity') is not taken
    into account. Refer to qjira/jira.py for the set of mappings.
    '''
    
    def __init__(self, jql=None, add_field=[], add_column=[], *args, **kwargs):
        super(JQLCommand, self).__init__('jql', *args, **kwargs)

        if not jql:
            raise TypeError('Missing keyword "jql"')

        self._jql = jql
        self._add_fields = add_field
        self._add_columns = add_column

    @property
    def header(self):
        '''JQL command returns all fields.
        '''
        columns =  super(JQLCommand, self).header

        for c in self._add_columns:
            columns[c] = c

        return columns
    
    @property
    def query(self):
        '''Return the user-provided JQL query'''
        return self._jql

    def retrieve_fields(self, fields):
        
        if self._add_fields and len(self._add_fields)>0:
            return fields + self._add_fields
        else:
            return fields
