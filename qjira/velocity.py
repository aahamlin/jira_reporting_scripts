'''Class encapsulating Velocity processing'''
import datetime

from .log import Log
from .util import sprint_info

class Velocity:
    def __init__(self, project=[]):
        self._header = 'project,issue,points,carried,sprint,startDate,endDate'
        self._projects = project

    @property
    def header(self):
        return self._header

    def query(self, callback):
        Log.debug('query')
        callback('project in ({}) AND issuetype = Story'.format(','.join(self._projects)))
    
    def process(self, issues):
        #Log.debug('process ', len(issues))
        for issue in issues:
            for sprint in self._process_story_sprints(issue):
                yield sprint
        
    def _process_story_sprints (self, story):
        '''Extract tuple containing sprint, issuekey, and story points from Story'''
        issuekey = story['key']
        fields = story['fields']
        points = fields['customfield_10109']
        project = fields['project']['key']
        
        if not points:
            points = 0.0

        sprints = story['fields'].get('customfield_10016')
        if sprints is None:
            yield (project,issuekey, points, 0, '', '', '')
            return
        infos = sorted([sprint_info(sprint) for sprint in sprints], key=lambda k: k['startDate'])
        # find carry-over points from previous sprint
        for idx,info in enumerate(infos):
            carried = points if idx > 0 else 0
            name = info['name'] if info['name'] else ''
            startDate = info['startDate'].date() if info['startDate'] else ''
            endDate = info['endDate'].date() if info['endDate'] else ''
            yield (project,issuekey, points, carried, name, startDate, endDate)
            

