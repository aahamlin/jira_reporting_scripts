"""
Reports worklog entries for list of issues.
"""

# remember datetime fields

# a worklog structure (JSON), several fields
# removed for readability.
#{
#    "startAt": 0,
#    "maxResults": 4,
#    "total": 4,
#    "worklogs": [
#        {
#            "author": {
#                "name": "andrew.hamlin",
#                "displayName": "Andrew Hamlin",
#                "active": true,
#                "timeZone": "America/New_York"
#            },
#            "updateAuthor": {
#               ...replicates author, not sure the difference
#            },
#            "comment": "worked more than estimate",
#            "started": "2018-04-05T10:39:00.000-0400",
#            "timeSpentSeconds": 86400,
#        },
#        {...}
#     ]
#}
        
import copy
from .command import BaseCommand
from ..jira import get_worklog
from ..log import Log

class WorklogCommand(BaseCommand):
    def __init__(self, author=[], *args, **kwargs):
        super(WorklogCommand, self).__init__('worklog', *args, **kwargs)

        if not author:
            raise TypeError('Missing required argument "author"')

        self._author = author

    @property
    def query(self):
        """Build worklog author query"""
        return 'worklogAuthor in (%s)' % ', '.join(self._author)

    @property
    def datetime_fields(self):
        base_fields = super(WorklogCommand, self).datetime_fields
        base_fields.append('worklog_started')
        return base_fields
    
    def pre_process(self, generate_data):
        """Return a generator of this source issue, including
        all worklog entries recorded against it."""

        username=self.kwargs.get('username')
        password=self.kwargs.get('password')
        
        for x in generate_data:
            w = get_worklog(self._base_url, x['issue_key'], username=username, password=password)
            #print('worklog entries: {0}'.format(len(w['worklogs'])))
            for wk in w['worklogs']:
                y = {'worklog': copy.copy(wk)}
                y.update(x.copy())
                yield y
            

        
