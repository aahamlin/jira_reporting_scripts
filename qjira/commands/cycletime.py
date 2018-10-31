from operator import itemgetter

from ..config import settings
from ..log import Log
from .command import BaseCommand
from ..dataprocessor import load_changelog

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
        super(CycleTimeCommand, self).__init__('cycletime', *args, **kwargs)

    ### REWRITE: use NEW changelog history management
    def pre_process(self, src):
        for x in src:
            load_changelog(x)
            if not x.get('story_points'):
                continue
            # if finished without progress, then cycletime = 0
            if not x.get('status_InProgress'):
                x['status_InProgress'] = x['status_Done']
            x['count_days'] = networkdays(x['status_InProgress'], x['status_Done'])
            yield x
    
    def post_process(self, rows):
        rows = sorted(rows, key=itemgetter('status_Done'))
        rows = sorted(rows, key=itemgetter('status_InProgress'))
        return rows
            
