'''Class encapsulating Velocity processing. This will
calculate the story points planned, completed, and 
carried over for every sprint associated with an issue.
'''
from operator import itemgetter
from functools import reduce as reduce_

import datetime

from ..config import settings
from .command import BaseCommand
from ..log import Log

DEFAULT_POINTS = 0.0

class VelocityCommand(BaseCommand):
    '''Analyze data for velocity metrics.

    Issues (story or bug) that have not been assigned at 
    least one sprint will not be reported on (because velocity
    only makes sense in the context of a sprint(s).

    Sprints without defined start and end dates  will not be
    reported unless forecasting is enabled.

    Results are accumulated by sprint_name.

    Point estimates are:
    planned points   - first seen in this sprint
    carried points   - continued from previous sprint (e.g. not planned but carried over)
    story points     - total points included in this sprint, whether planned or carried
    completed points - finished in this sprint (status = Closed, Done)
    '''

    def __init__(self, include_bugs=False, forecast=False, filter_by_date=None, *args, **kwargs):
        super(VelocityCommand, self).__init__('velocity', pivot_field='sprint', *args, **kwargs)
        self._include_bugs = include_bugs
        self._forecast = forecast
        self._filter_by_date = filter_by_date
        self._target_sprint_ids = set()
        self._sprint_id_issuetypes = settings['velocity']['sprint_id_issuetypes'].split(',')
        self._effort_field = settings['effort_engine']['effort_field']
    
    @property
    def query(self):
        if self._include_bugs:
            return settings['velocity']['query_bug']
        else:
            return super(VelocityCommand, self).query

    def post_process(self, rows):
        '''data processor wrapper to calculate points as planned, carried, completed'''
        results = self._reduce_process(rows)
        sorted_sprints = sorted(results, key=itemgetter('project_key'))
        sorted_sprints = sorted(sorted_sprints, key=itemgetter('sprint_name'))
        sorted_sprints = sorted(sorted_sprints, key=lambda x: x.get('sprint_startDate') or datetime.date.max)
        return sorted_sprints

    def _reduce_process(self, rows):
        '''reduce the {rows} to an array of dict structures where each sprint velocity is summarized in a single row.'''
        results = {}

        for s in self._raw_process(rows):
            sprint_id = s['sprint_id']
            
            if sprint_id not in self._target_sprint_ids:
                Log.debug('Skipping filtered sprint %d'.format(sprint_id))
                continue

            Log.debug('Updating velocity in sprint %d'.format(sprint_id))
            if not sprint_id in results:
                results[sprint_id] = {k:v for k, v in s.items() if k in self.header_keys}
                current_effort = (0, 0, 0, 0)
            else:
                current_effort = self._get_points(results[sprint_id])
            effort_value = self._get_points(s)
            total_effort = tuple(map(sum, zip(current_effort, effort_value)))
                
            results[sprint_id].update({
                'planned_effort': total_effort[0],
                'carried_effort': total_effort[1],
                self._effort_field: total_effort[2],
                'completed_effort': total_effort[3]
            })

        return results.values()

    def _get_points(self, r):
        '''return point fields from row {r}'''
        #return tuple([v or 0 for k,v in r.items() if k in ['planned_points','carried_points','story_points','completed_points']])
        return (r['planned_effort'],
                r['carried_effort'],
                r.get(self._effort_field, 0),
                r['completed_effort'])
            
    def _raw_process(self, rows):
        '''
        Do bulk processing of individual stories, suitable for excel.

        Stories with no defined sprint (no start or end date) are skipped. They do not count against velocity.

        Unless forecasting is turned on, sprints that are in progress (no complete date) are skipped.

        The result is a generator of dict objects.
        '''
        last_issue_seen = None
        counter = 0
        for idx,row in enumerate(rows):
            if not row.get('sprint_id'):
                continue
            
            if not self._forecast and not row.get('sprint_completeDate'):
                #print ('> skip incomplete sprint')
                continue

            # including bugs causes inclusion of old sprints, track sprint_ids of the stories for filtering
            sprint_id = row['sprint_id']
            if self._filter_by_date and self._filter_by_date <= row.get('sprint_startDate', datetime.date.max):
                self._target_sprint_ids.add(sprint_id)
            elif row['issuetype_name'] in self._sprint_id_issuetypes:
                self._target_sprint_ids.add(sprint_id)
            
            if row['issue_key'] is not last_issue_seen:
                last_issue_seen = row['issue_key']
                counter = 0
            else:
                counter += 1
            effort_value = row.get(self._effort_field, DEFAULT_POINTS)
            planned_effort = effort_value if counter == 0 else DEFAULT_POINTS
            carried_effort = effort_value if counter >= 1 else DEFAULT_POINTS
            completed_effort = effort_value if self._isComplete(row) else DEFAULT_POINTS
            update = {
                'planned_effort': planned_effort,
                'carried_effort': carried_effort,
                'completed_effort': completed_effort
            }
            row.update(update)
            if Log.isDebugEnabled():
                Log.debug('Issue {0} of {1} points in sprint {2}'.format(row['issue_key'], point_value, row['sprint_name']))
            yield row

    def _isComplete(self, row):
        '''Issue is complete when status changed between sprint startDate & endDate'''
        completedDate = row.get('status_Done') \
                        if row['issuetype_name'] == 'Story' \
                        else row.get('status_Closed')
        if not completedDate:
            return False
        
        sprintStartDate = row.get('sprint_startDate')
        sprintCompletionDate = row.get('sprint_completeDate')
        #print('> isComplete start: {0}, completion: {1}, done: {2}'.format(sprintStartDate, sprintCompletionDate, completedDate))
        return sprintCompletionDate and \
            completedDate >= sprintStartDate and \
            completedDate <= sprintCompletionDate
