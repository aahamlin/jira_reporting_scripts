from operator import itemgetter

import re

from ..config import settings
from ..log import Log
from .command import BaseCommand
from ..dataprocessor import load_transitions

def networkdays(start, end):
    return '=NETWORKDAYS("{}","{}")'.format(start, end)

class CycleTimeCommand(BaseCommand):
    '''Class encapsulating cycle time of an issue. This class will
   calculate the days from being moved to In Progress by devs
   to being Closed by testers. Results are sorted by start and
   end dates, oldest to newest.

   Limitations: 

   This does not subtract time for an issue
   moved from In Progress back to Open. 

   This does not record separate values for bugs being dev
   complete Resolved and being test complete Closed.
    '''

    def __init__(self, *args, **kwargs):
        super(CycleTimeCommand, self).__init__('cycletime', pre_load=load_transitions, *args, **kwargs)

        self._add_columns = []

    @property
    def pivot_field(self):
        return 'transitions'

    @property
    def header_keys(self):
        _header_keys = super(CycleTimeCommand, self).header_keys
        for col in self._add_columns:
            if col not in _header_keys:
                _header_keys.append(col)
        
        return _header_keys
    

    def post_process(self, rows):
        """Summarize lead & cycle time for items.

        Accumulates the transitions elements. Lead time is time from
        Ready to Resolve/Verified. Cycle time is time from WorkInProgress
        to Resolve/Verified.
        """

        accumulated = {}
        # map date to status
        # TODO update mapping & header property based on configuration from INI files
        status_cols = [
            ('.+_to_Ready','lead_begin', 'lt', False),
            ('.+_to_WorkInProgress','cycle_begin', 'lt', True),
            ('from_WorkInProgress_to_WorkCompleted', 'sub_cycle1_begin', 'gt', False),
            ('from_WorkCompleted_to_Resolved','sub_cycle1_end', 'gt', False),
            ('from_Resolved_to_VerifyingInProgress', 'sub_cycle2_begin', 'gt', True),
            ('from_VerifyingInProgress_to_Resolved', 'sub_cycle2_end', 'gt', False),
            ('(?!from_WorkCompleted).+_to_Resolved', 'cycle_end', 'gt', False),
            ('.+_to_Resolved', 'lead_end', 'gt', False),
           
        ]
        
        for r in rows:
            issue_key = r['issue_key']
            if issue_key not in accumulated:
                accumulated[issue_key] = {k:v for k,v in r.items() if k in ['project_key', 'fixVersions_0_name', 'issuetype_name','status_name']}

            for tranz,col,srt,cnt in status_cols:
                if col not in self._add_columns:
                    self._add_columns.append(col)

                count_col = 'count_{0}'.format(col)

                if cnt and count_col not in self._add_columns:
                    self._add_columns.append(count_col)
                
                if re.match(tranz, r['transitions_name']):
                    d = r['transitions_change_date']
                    if col not in accumulated[issue_key]:
                        accumulated[issue_key][col] = d
                    elif srt == 'lt' and d < accumulated[issue_key][col]:
                        accumulated[issue_key][col] = d
                    elif srt == 'gt' and d > accumulated[issue_key][col]:
                        accumulated[issue_key][col] = d

                    if cnt and count_col not in accumulated[issue_key]:
                        accumulated[issue_key][count_col] = 1
                    elif cnt:
                        accumulated[issue_key][count_col] = accumulated[issue_key][count_col] + 1

        rows = [dict(v, issue_key=k) for k,v in accumulated.items()]
        #print(rows)
        return rows
