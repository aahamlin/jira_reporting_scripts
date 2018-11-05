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

    @property
    def pivot_field(self):
        return 'transitions'
