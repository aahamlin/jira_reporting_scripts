'''Executes simple queries of Jira Cloud REST API'''

import requests
import json

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from .log import Log

class Jira:

    # constants
    ISSUE_ENDPOINT='https://{}/rest/api/2/issue/{}?{}'

    ISSUE_SEARCH_ENDPOINT='https://{}/rest/api/2/search?{}'
    
    HEADERS = {'content-type': 'application/json'}

    # expands the changelog of each issue and hides all but essential fields
    # customfield 10109 is the 'story points' field (may be null)
    # customfield 10016 is the 'iteration' or 'sprint' field, an array
    # "customfield_11101" - ENG Design
    # "customfield_14300" - ENG Test Plan
    # "customfield_10017" -- Epic (issuekey)

    QUERY_STRING_DICT = {
        'expand': 'changelog',
        'fields': '-*navigable,project,issuetype,summary,fixVersions,customfield_10109,customfield_10016,customfield_11101,customfield_14300,customfield_10017'
    }
            
    def __init__ (self, baseUrl, username=None, password=None, auth=None, progress=None):
        ''' Construct new Jira client '''
        self.baseUrl = baseUrl
        self.username = username
        self.password = password
        self._progress = progress

    def get_project_issues (self, jql_query):
        '''Perform a JQL search across `projects` and return issues'''

        Log.debug('get_project_issues')
        search_args = Jira.QUERY_STRING_DICT.copy()
        search_args.update({'jql':jql_query})
        Log.debug(search_args['jql'])
        
        startAt = 0
        maxResults = 50
        total = maxResults

        all_issues = []
        
        while startAt < total:

            search_args.update({
                'startAt':startAt,
                'maxResults':maxResults
            })
        
            query_string = urlencode(search_args)

            url = Jira.ISSUE_SEARCH_ENDPOINT.format(self.baseUrl, query_string)
            Log.debug('url = ' + url)

            if self._progress:
                self._progress('Retrieving {} of {}...'.format(startAt, total))

            r = requests.get(url, auth=(self.username, self.password), headers=Jira.HEADERS)
            Log.verbose(r.text)
            Log.debug(r.status_code)
            r.raise_for_status()

            json = r.json()

            total = json['total']

            issues = json['issues']

            count = len(issues)

            startAt += count

            if self._progress:
                self._progress('Retrieved {} of {}'.format(startAt, total))
            
            all_issues.extend(issues)

        # would prefer to use a generator for memory management  but, for now, simplicity rules
        return all_issues

