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
from __future__ import division
import copy
from datetime import date
from operator import itemgetter
from .command import BaseCommand
from ..jira import get_worklog
from ..log import Log

class WorklogCommand(BaseCommand):
    def __init__(self, author=[], start_date=None, restrict_to_username=True, *args, **kwargs):
        super(WorklogCommand, self).__init__('worklog', *args, **kwargs)

        if restrict_to_username and not author:
            author = [self.kwargs.get('username')]
            
        if not author:
            raise TypeError('Missing required argument "author"')

        self._author = author
        self._start_date = start_date
        self._restrict_to_username = restrict_to_username

    @property
    def query(self):
        """Build worklog author query"""
        base_query = 'worklogAuthor in (%s)' % ', '.join(self._author)
        if self._start_date:
            #print('filtering worklogs by start-date', self._start_date)
            return ' AND '.join([base_query, 'worklogDate >= %s' % self._start_date])
        else:
            return base_query

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
            
    def post_process(self, rows):
        """ Summarize each user by day """

        if self._restrict_to_username:
            rows = [r for r in rows if r['worklog_author_name'] in self._author]

        # filter by start date
        if self._start_date:
            rows = [r for r in rows if r['worklog_started'] >= self._start_date]

        accumulated = {}

        date_max = str(date.max)
        
        for r in rows:
            #print([k for k in r.keys() if k.startswith('worklog_')])
            
            author_name = r['worklog_author_name']
            if author_name not in accumulated:
                accumulated[author_name] = {}

            started = str(r['worklog_started'])
            
            if started not in accumulated[author_name]:
                accumulated[author_name][started] = {}

            if 'worklog_timeSpentSeconds' not in accumulated[author_name][started]:
                accumulated[author_name][started]['worklog_timeSpentSeconds'] = 0
                
            accumulated[author_name][started]['worklog_timeSpentSeconds'] = accumulated[author_name][started]['worklog_timeSpentSeconds'] + r['worklog_timeSpentSeconds']
            
            if 'issue_keys' not in accumulated[author_name][started]:
                accumulated[author_name][started]['issue_keys'] = []

            if r['issue_key'] not in accumulated[author_name][started]['issue_keys']:
                accumulated[author_name][started]['issue_keys'].append(r['issue_key'])

            if date_max not in accumulated[author_name]:
                accumulated[author_name][date_max] = {}

            if 'worklog_timeSpentSeconds' not in accumulated[author_name][date_max]:
                accumulated[author_name][date_max]['worklog_timeSpentSeconds'] = 0

            accumulated[author_name][date_max]['worklog_timeSpentSeconds'] = accumulated[author_name][date_max]['worklog_timeSpentSeconds'] + r['worklog_timeSpentSeconds']

            if 'issue_keys' not in accumulated[author_name][date_max]:
                accumulated[author_name][date_max]['issue_keys'] = [u'Total of entire time period']
                
        rows = [dict(worklog_timeSpentDays='{:.3f}'.format(v1['worklog_timeSpentSeconds']/60/60/8),
                     issue_keys=' '.join(v1['issue_keys']),
                     worklog_started=k1,
                     worklog_author_name=k) for k,v in accumulated.items() for k1, v1 in v.items()]
        
        rows = sorted(rows, key=itemgetter('worklog_started'))
        rows = sorted(rows, key=itemgetter('worklog_author_name'))
          
        return rows
