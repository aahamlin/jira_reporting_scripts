'''Class encapsulating cycle time of an issue. This class will
   calculate the days from being moved to In Progress by devs
   to being Closed by testers.

   Limitations: 

   This does not subtract time for an issue
   moved from In Progress back to Open. 

   This does not record separate values for bugs being dev
   complete Resolved and being test complete Closed.
'''
import dateutil.parser
import datetime

from .log import Log
from .data import calculate_rows

class CycleTime:

    def __init__(self):
        # stories and bugs have different status for the endDate: Donen ahd Closed, respectively
        self._header = ['project_key','fixVersions_0_name','issuetype_name','issue_key','story_points','status_InProgress','status_Done', 'status_Closed']
        self._query = '((issuetype = Story AND status in (Done, Accepted)) OR (issuetype = Bug AND status = Closed))'
        
    @property
    def header(self):
        return self._header

    @property
    def query(self):
        return self._query
        
    def process(self, issues):
        #Log.debug('process ', len(issues))
        results = [row for iss in issues for row in calculate_rows(iss)]
        return results

