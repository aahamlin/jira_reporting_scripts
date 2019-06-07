from collections import OrderedDict

from ..config import settings
from .base_command import BaseCommand
from .. import jira


class JQLCommand(BaseCommand):
    '''JQL command runs any valid JQL query string.

    Given a list of add_field the Jira query string be appended with additional non-default fields to retrieve.
    Given a list of add_column the CSV report will add additional columns to the output.

    TODO: Mapping from Jira fields to column names (such as 'customfield_10112' to 'severity') is not taken
    into account. Refer to qjira/jira.py for the set of mappings.
    '''
    
    def __init__(self, jql=None, add_field=None, add_column=None, *args, **kwargs):
        super(JQLCommand, self).__init__('jql', reverse_sprints=True, *args, **kwargs)

        if not jql:
            raise TypeError('Missing keyword "jql"')

        self._jql = jql
        self._add_fields = add_field or []
        self._add_columns = add_column or []
    
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

    def request_fields(self):
        fields = super(JQLCommand, self).request_fields()
        if self._add_fields and len(self._add_fields)>0:
            fields += self._add_fields

        return fields
