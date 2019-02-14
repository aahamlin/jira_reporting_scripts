'''Class encapsulating Velocity processing. This will
calculate the story points planned, completed, and 
carried over for every sprint associated with an issue.
'''
from operator import itemgetter
from functools import reduce as reduce_

import datetime

from .base_command import BaseCommand
from .engine_mixin import EngineMixin
from ..log import Log
from ..dataprocessor import load_changelog

DEFAULT_EFFORT = 0.0

class VelocityCommand(BaseCommand, EngineMixin):
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
        super(VelocityCommand, self).__init__('velocity', pivot_field='sprint', pre_load=load_changelog,  *args, **kwargs)
        EngineMixin.__init__(self)

        self._include_bugs = include_bugs
        self._forecast = forecast
        self._filter_by_date = filter_by_date
        self._target_sprint_ids = set()

        velocity_metrics_prefix = ['planned_', 'carried_', 'completed_']
        self._effort_header_keys = [self.effort_field] + [pre + self.effort_field for pre in velocity_metrics_prefix] 

        self._header_keys += self._effort_header_keys
    
    @property
    def query(self):
        if self._include_bugs:
            return self._command_settings['query_bug']
        else:
            return super(VelocityCommand, self).query

    def request_fields(self):
        fields = super(VelocityCommand, self).request_fields()
        fields += EngineMixin.request_fields(self)
        return fields

    @property
    def planned_field(self):
        return self._effort_header_keys[1]
    
    @property
    def carried_field(self):
        return self._effort_header_keys[2]

    @property
    def completed_field(self):
        return self._effort_header_keys[3]

    
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

        for s in list(self._raw_process(rows)):
            sprint_id = s['sprint_id']

            #print('> sprint_id %s in target_ids %s' % (sprint_id, self._target_sprint_ids))
            if sprint_id not in self._target_sprint_ids:
                Log.debug('Skipping filtered sprint_id {0}'.format(sprint_id))
                continue

            Log.verbose('Updating velocity in sprint_id {0}'.format(sprint_id))
            if not sprint_id in results:
                results[sprint_id] = {k:v for k, v in s.items() if k in self.header_keys}
                current_effort = (0, 0, 0, 0)
            else:
                current_effort = self._get_points(results[sprint_id])
            effort_value = self._get_points(s)
            total_effort = tuple(map(sum, zip(current_effort, effort_value)))
                
            results[sprint_id].update({
                self.planned_field: total_effort[0],
                self.carried_field: total_effort[1],
                self.effort_field: total_effort[2],
                self.completed_field: total_effort[3]
            })

        return results.values()

    def _get_points(self, r):
        '''return point fields from row {r}'''
        return (r[self.planned_field],
                r[self.carried_field],
                r.get(self.effort_field, 0),
                r[self.completed_field])
            
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
                #print('> %d skip non-sprint work item' % idx)
                continue
            
            if not self._forecast and not row.get('sprint_completeDate'):
                #print ('> %d skip incomplete sprint' % idx)
                continue

            # including bugs causes inclusion of old sprints, track sprint_ids of the stories for filtering
            sprint_id = row['sprint_id']
            sprint_start_date = row.get('sprint_startDate', datetime.date.max)
            if self._filter_by_date and self._filter_by_date <= sprint_start_date:
                Log.debug('Target by date filter <= {0}; adding sprint {1}'.format(sprint_start_date, sprint_id))
                self._target_sprint_ids.add(sprint_id)
            elif self.is_story_type(row):
                Log.debug('Target by issue type filter in {0}; adding sprint {1}'.format(row['issuetype_name'], sprint_id))
                self._target_sprint_ids.add(sprint_id)
            
            if row['issue_key'] is not last_issue_seen:
                last_issue_seen = row['issue_key']
                counter = 0
            else:
                counter += 1
            effort_value = row.get(self.effort_field, DEFAULT_EFFORT)
            planned_effort = effort_value if counter == 0 else DEFAULT_EFFORT
            carried_effort = effort_value if counter >= 1 else DEFAULT_EFFORT
            completed_effort = effort_value if self._isComplete(row) else DEFAULT_EFFORT
            Log.trace('keys: {0} {1} {2}'.format(self.planned_field, self.carried_field, self.completed_field))
            
            Log.trace('values: {0} {1} {2}'.format(planned_effort, carried_effort, completed_effort))
            update = {
                self.planned_field: planned_effort,
                self.carried_field: carried_effort,
                self.completed_field: completed_effort
            }
            Log.trace('updating {0} with {1}'.format(row['issue_key'], update))
            row.update(update)
            if Log.isDebugEnabled():
                Log.debug('Issue {0} has {1} effort in sprint "{2}" ({3})'.format(row['issue_key'], effort_value, row['sprint_name'], sprint_id))
            yield row

    def _isComplete(self, row):
        '''Issue is complete when status changed between sprint startDate & endDate'''
        completedDate = None
        for status in self.complete_status:
            if row.get(status) and not completedDate:
                #print('> found status {0} at {1}'.format(status, row[status]))
                completedDate = row[status]
        
        if not completedDate:
            return False
        
        sprintStartDate = row.get('sprint_startDate')
        sprintCompletionDate = row.get('sprint_completeDate')
        #print('> isComplete start: {0}, completion: {1}, done: {2}'.format(sprintStartDate, sprintCompletionDate, completedDate))
        return sprintCompletionDate and \
            completedDate >= sprintStartDate and \
            completedDate <= sprintCompletionDate
