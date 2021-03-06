'''Executes simple queries of Jira Cloud REST API'''
#from __future__ import unicode_literals
import requests
import datetime
import json
import re
from dateutil import parser as date_parser

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from .config import settings
from .log import Log

CUSTOM_NAME_MAP = dict(settings.items('custom_fields'))

CUSTOM_FIELD_MAP = {v:k for k,v in CUSTOM_NAME_MAP.items()}

ISSUE_ENDPOINT='{}/rest/api/2/issue/{}'

ISSUE_WORKLOG_ENDPOINT=ISSUE_ENDPOINT + '/worklog'

ISSUE_SEARCH_ENDPOINT='{}/rest/api/2/search?{}'

ISSUE_BROWSE='{}/browse/{}'
    
HEADERS = {'content-type': 'application/json'}

DEFAULT_FIELDS = settings.get('jira','default_fields').split(',')

DEFAULT_EXPANDS = settings.get('jira','default_expands').split(',')

def extract_sprint(sprint):
    '''Return a dict object containing sprint details.'''
    m = re.search('\[(.+)\]', sprint)
    if m:
        d = dict(e.split('=') for e in m.group(1).split(','))
        for n in ('startDate','endDate','completeDate'):
            try:
                the_date = date_parser.parse(d[n]).date()
                d[n]= the_date
            except ValueError:
                d[n] = None
        #print('> extract_sprint returns: {0}'.format(d))
        return d
    raise ValueError

def customfield_value(name):
    '''Lookup a Jira customfield_xxxxx value from the map.
    Default return the name provided. So that standard Jira fields, such as 'priority'
    can be added without additional configuration.'''
    return CUSTOM_NAME_MAP.get(name, name)

def _get_json(url, username=None, password=None, headers=HEADERS):
    r = requests.get(url, auth=(username, password), headers=headers)
    Log.debug(r.status_code)
    r.raise_for_status()        
    return r.json()

def _as_data(issue, reverse_sprints=False):
    """
    Manipulate the default JSON structure for customized JIRA installs.
    Such as, mapping customfield_* entries to user-defined names and
    transforming the changelog history entries to permit tracing of events
    over time.
    """
    if Log.isVerboseEnabled():
        Log.verbose('jira json format: {0}'.format(
            json.dumps(issue, sort_keys=True, indent=4, separators=(',', ': '))))
        
    data = {
        'issue_key':issue['key']
    }
    #copy in fields, replacing custom fields with mapped names
    data.update({CUSTOM_FIELD_MAP.get(k, k):v for k, v in issue['fields'].items() if k is not 'sprint'})
    # find key corresponds to sprint
    sprint_field = customfield_value('sprint')
    #copy in sprints
    if issue['fields'].get(sprint_field):
        sprints_encoded = issue['fields'][sprint_field]
        if sprints_encoded:
            #print('> as_data sprints_encoded: {0}'.format(sprints_encoded))
            data['sprint'] = [
                sprint for sprint in sorted(
                    map(extract_sprint, sprints_encoded),
                    key=lambda x: x['startDate'] or datetime.date.max,
                    reverse=reverse_sprints)
            ]
            #print('> as_data sprints sorted: {0}'.format(data['sprint']))
        
    #copy in changelog
    if issue.get('changelog'):
        data.update({'_changelog': issue['changelog']})

    if Log.isVerboseEnabled():
        Log.verbose('qjira json format: {0}'.format(
            json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))))

    return data

def default_fields():
    '''Return fields to retrieve from Jira'''
    fields = DEFAULT_FIELDS[:]
    return fields

def get_worklog(baseUrl, issuekey, username=None, password=None):
    """Retrieve the worklog history for an issue."""
    url = ISSUE_WORKLOG_ENDPOINT.format(baseUrl, issuekey)
    Log.debug('url = ' + url)
    return _get_json(url, username=username, password=password)

def get_browse_url(baseUrl, issuekey):
    if not issuekey:
        raise ValueError
    return ISSUE_BROWSE.format(baseUrl, issuekey)

def get_issue(baseUrl, issuekey, username=None, password=None):
    # this does not pass in the query string
    url = ISSUE_ENDPOINT.format(baseUrl, issuekey)
    Log.debug('url = ' + url)
    return _as_data(_get_json(url, username=username, password=password))

def all_issues(baseUrl, jql,
               username=None,
               password=None,
               progress_cb=None,
               continue_cb=None,
               reverse_sprints=False,
               fields=DEFAULT_FIELDS,
               expands=DEFAULT_EXPANDS):
    '''Generator yielding a partially normalized structure from JSON'''
    Log.debug('all_issues')
    search_args = {
        'expand': ','.join(expands),
        'fields': ','.join(fields),
        'jql': jql
    }
    Log.debug('jql: ' + search_args['jql'])

    startAt = 0
    maxResults = 50
    total = maxResults
        
    while startAt < total:
        search_args.update({
            'startAt':startAt,
            'maxResults':maxResults
        })
        query_string = urlencode(search_args)
        url = ISSUE_SEARCH_ENDPOINT.format(baseUrl, query_string)
        Log.debug('url = ' + url)
        if progress_cb:
            progress_cb(startAt, total)
        payload = _get_json(url, username=username, password=password)
        #print('> payload {0}'.format(type(payload)))
        total = payload['total']
        issues = payload['issues']
        count = len(issues)
        startAt += count
        for issue in issues:
            yield _as_data(issue, reverse_sprints=reverse_sprints)
            if continue_cb and not continue_cb():
                return

    if progress_cb:
        progress_cb(startAt, total)
