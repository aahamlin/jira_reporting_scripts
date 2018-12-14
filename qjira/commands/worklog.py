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
    def __init__(self, author=[], start_date=None, end_date=None, group_by=None, restrict_to_username=True, total_by_username=False, *args, **kwargs):
        super(WorklogCommand, self).__init__('worklog', *args, **kwargs)

        if restrict_to_username and not author:
            author = [self.kwargs.get('username')]

        user_query = super(WorklogCommand, self).query
        if not author and not user_query:
            raise TypeError('Missing required argument "author"')

        self._base_query = user_query
        self._author = [a.lower() for a in author]
        self._restrict_to_username = restrict_to_username
        self._total_by_username = total_by_username
        self._group_by = group_by

        self._start_date = start_date
        self._end_date = end_date

        if start_date and end_date:
            self._date_filter = lambda d: d >= start_date and d <= end_date
        elif start_date:
            self._date_filter = lambda d: d >= start_date
        elif end_date:
            self._date_filter = lambda d: d <= end_date
        else:
            self._date_filter = None

    @property
    def query(self):
        """Build worklog author query"""
        
        if self._base_query is not None:
            base_query = self._base_query
        else:
            base_query = 'worklogAuthor in (%s)' % ', '.join(self._author)
            
        if self._start_date and self._end_date:
            return ' AND '.join([base_query, 'worklogDate >= %s AND worklogDate <= %s' % (self._start_date, self._end_date)])
        elif self._start_date:
            #print('filtering worklogs by start-date', self._start_date)
            return ' AND '.join([base_query, 'worklogDate >= %s' % self._start_date])
        elif self._end_date:
            return ' AND '.join([base_query, 'worklogDate <= %s' % self._end_date])
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
        if self._date_filter:
            rows = [r for r in rows if self._date_filter(r['worklog_started'])]

        accumulated = {}

        date_max = str(date.max)
        
        for r in rows:
            #print([k for k in r.keys() if k.startswith('worklog_')])
            
            author_name = r['worklog_author_name']
            if author_name not in accumulated:
                accumulated[author_name] = {}

            activerow = accumulated[author_name]
                
            if self._group_by and self._group_by not in r:
                raise Exception('group_by failed: column "%s" does not exist.' % self._group_by)

            if self._group_by:
                group_by = r[self._group_by]
                if group_by not in accumulated[author_name]:
                    accumulated[author_name][group_by] = {}

                activerow = accumulated[author_name][group_by]
            
            started = str(r['worklog_started'])
            
            if started not in activerow:
                activerow[started] = {}

            if 'worklog_timeSpentSeconds' not in activerow[started]:
                activerow[started]['worklog_timeSpentSeconds'] = 0
                
            activerow[started]['worklog_timeSpentSeconds'] = activerow[started]['worklog_timeSpentSeconds'] + r['worklog_timeSpentSeconds']
            
            if 'issue_keys' not in activerow[started]:
                activerow[started]['issue_keys'] = []

            if r['issue_key'] not in activerow[started]['issue_keys']:
                activerow[started]['issue_keys'].append(r['issue_key'])

            if not self._total_by_username:
                continue
                
            if date_max not in activerow:
                activerow[date_max] = {}

            if 'worklog_timeSpentSeconds' not in activerow[date_max]:
                activerow[date_max]['worklog_timeSpentSeconds'] = 0

            activerow[date_max]['worklog_timeSpentSeconds'] = activerow[date_max]['worklog_timeSpentSeconds'] + r['worklog_timeSpentSeconds']

            if 'issue_keys' not in activerow[date_max]:
                activerow[date_max]['issue_keys'] = [u'Total of entire time period']



        rows = list(self.flatten_levels(accumulated))
        #rows = [dict(worklog_timeSpentDays='{:.3f}'.format(v1['worklog_timeSpentSeconds']/60/60/8),
        #             issue_keys=' '.join(v1['issue_keys']),
        #             worklog_started=k1,
        #             worklog_author_name=k) for k,v in accumulated.items() for k1, v1 in v.items()]
        
        rows = sorted(rows, key=itemgetter('worklog_started'))
        rows = sorted(rows, key=itemgetter('worklog_author_name'))
          
        return rows

    def flatten_levels(self, accumulated):
        if self._group_by:
            for k, v in accumulated.items():
                for k1, v1 in v.items():
                    for k2, v2 in v1.items():
                        yield dict(worklog_timeSpentDays='{:.3f}'
                                   .format(v2['worklog_timeSpentSeconds']/60/60/8),
                                   issue_keys=' '.join(v2['issue_keys']),
                                   worklog_started=k2,
                                   project_name=k1,
                                   worklog_author_name=k)
        else:
            for k, v in accumulated.items():
                for k1, v1 in v.items():
                    yield dict(worklog_timeSpentDays='{:.3f}'
                               .format(v1['worklog_timeSpentSeconds']/60/60/8),
                               issue_keys=' '.join(v1['issue_keys']),
                               worklog_started=k1,
                               worklog_author_name=k)
                    
