#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
main.py
Author: Andrew Hamlin
Description: script to execute commands against jira
'''
import sys
import io
import os
import argparse
import locale

from requests.exceptions import HTTPError
from dateutil import parser as date_parser

from .config import settings
from . import Log
from . import credential_store as creds

from .commands import *

PY3 = sys.version_info > (3,)

def _print(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()

def _progress(start, total):
    msg = '\rRetrieving {} of {}...'.format(start, total)
    if start >= total:
        msg = ' ' * len(msg)
        _print('\r' + msg)
        msg += '\rRetrieved {} issues\n'.format(start, total)
    _print(msg)    
    
def _open(filepath, encoding):
    '''Open the file with given encoding.

    If the filepath is the default sys.stdout, just return it.
    '''
    if not filepath:
        return sys.stdout
    elif PY3:
        return io.open(filepath, 'wt',
                       encoding=encoding,
                       newline='')
    else:
        return io.open(filepath, 'wb')

def date_string(string):
    '''Convert supplied string to a datetime.date() object.'''
    try:
        value = date_parser.parse(string)
    except ValueError as ve:
        raise argparse.ArgumentTypeError(ve)
    return value.date()


def create_parser(settings):

    base_url = settings.get('jira', 'base_url')
    
    parser = argparse.ArgumentParser(
        prog='qjira',
        description='Exports data from Jira to CSV format')

    parser.add_argument('-b', '--base',
        dest='base_url',
        metavar='URL',
        help='Jira Cloud base URL [default: %s]'%base_url,
        default=base_url)

    parser.add_argument('-u', '--user',
        metavar='USER',
        help='Username, if blank will use logged on user',
        default=None)

    parser.add_argument('-w', '--password',
        metavar='PWD',
        help='Password (insecure), if blank will prommpt',
        default=None)

    parser.add_argument('-d', '--debug',
        dest='debugLevel',
        action='count',
        help='Debug level')

    parser.add_argument('-1', '--one-shot',
        dest='oneShot',
        action='store_true',
        help='Process single record only')                

    parser.set_defaults(func=None)

    # sub-commands: velocity, cycletimes, summary, techdebt
    subparsers = parser.add_subparsers(
        title='Available commands',
        dest='subparser_name',
        help='Available commands to process data')

    # Note: may want to move output related options to the common set
    parser_common = argparse.ArgumentParser(add_help=False)
        
    parser_common.add_argument('-o', '--outfile',
        metavar='FILENAME',
        nargs='?',
        default=None,
        help='Output file (.csv) [default: stdout]')

    parser_common.add_argument('--no-progress',
        action='store_true',
        dest='suppress_progress',
        help='Hide data download progress')       

    parser_common.add_argument('--encoding',
        metavar='ENC',
        default='ASCII',
        help='Specify an output encoding. In Python 2.x, only default ASCII is supported.')
    
    parser_common.add_argument('--delimiter',
        metavar='CHAR',
        default=',',
        help='Specify a CSV delimiter [default: comma].\nFor bash support escape the character with $, such as $\'\\t\'')

    
    parser_common.add_argument('-A', '--all-fields',
        action='store_true',
        help='Extract all "navigable" fields in Jira, [fields=*navigable]')

    parser_command_options = argparse.ArgumentParser(
        add_help=False,
        parents=[parser_common])
        
    parser_command_options.add_argument('-f', '--fix-version',
        dest='fixversion',
        metavar='VERSION',
        action='append',
        help='Restrict search to fixVersion(s)')

    parser_command_options.add_argument('project',
        nargs='+',
        metavar='project',
        help='Project name')

    # TODO add an arbitrary query option, mutually exclusive to fixversion & projects
    
    parser_cycletime = subparsers.add_parser('cycletime',
        parents=[parser_command_options],
        help='Produce cycletime data')

    parser_cycletime.set_defaults(func=CycleTimeCommand)

    parser_velocity = subparsers.add_parser('velocity',
        parents=[parser_command_options],
        help='Produce velocity data')

    parser_velocity.add_argument('--include-bugs', '-B',
        action='store_true',
        help='Include bugs in velocity calculation')

    parser_velocity.add_argument('--forecast', '-F',
        action='store_true',
        help='Include future sprints in velocity calculation')

    parser_velocity.add_argument('--filter-by-date',
        type=date_string,
        metavar='START',
        default=None,
        help='Filter sprints starting earlier than START date.')

    parser_velocity.set_defaults(func=VelocityCommand)

    parser_summary = subparsers.add_parser('summary',
        parents=[parser_command_options],
        help='Produce summary report')

    parser_summary.add_argument('--mark-new', '-N',
        action='store_true',
        dest='mark_if_new',
        help='Mark docs linked within past 2 weeks')

    parser_summary.add_argument('--csv',
        action='store_true',
        dest='use_csv_formatter',
        help='Output CSV rather than HTML Fragments')
    
    parser_summary.set_defaults(func=SummaryCommand)

    parser_techdebt = subparsers.add_parser('debt',
        parents=[parser_command_options],
        help='Produce tech debt report')

    parser_techdebt.set_defaults(func=TechDebtCommand)

    parser_backlog = subparsers.add_parser('backlog',
        parents=[parser_command_options],
        help='Query bug backlog by fixVersion')

    parser_backlog.set_defaults(func=BacklogCommand)

    parser_worklog = subparsers.add_parser('worklog',
        parents=[parser_common],
        help='Query worklog entries')

    parser_worklog.add_argument('author',
        metavar='AUTHOR',
        nargs='*',
        help='Author name(s)')

    parser_worklog.add_argument('-S', '--start-date',
        type=date_string,
        metavar='yyyy/mm/dd',
        default=None,
        help='Exclude worklogDate before start date')

    parser_worklog.add_argument('-E', '--end-date',
        type=date_string,
        metavar='yyyy/mm/dd',
        default=None,
        help='Exclude worklogDate after end date')

    parser_worklog.add_argument('--authors-only',
        dest='restrict_to_username',
        action='store_true',
        help='Restrict listings to authors provided.')

    parser_worklog.add_argument('--total',
        dest='total_by_username',
        action='store_true',
        help='Include total days per author')

#    parser_worklog.add_argument('-G', '--group-by',
#        help='Group results by an arbitrary (existing) column, e.g. project_name.')

    parser_worklog.set_defaults(func=WorklogCommand)
    
    parser_jql = subparsers.add_parser('jql',
        parents=[parser_common],
        help='Query using JQL')

    parser_jql.add_argument('jql',
        help='JQL statement')

    parser_jql.add_argument('--add-field', '-f',
        action='append',
        metavar='NAME',
        help='Add field(s) to Jira request')

    parser_jql.add_argument('--add-column', '-c',
        action='append',
        metavar='NAME',
        help='Add column(s) to CSV output')

    parser_jql.add_argument('-p', '--pivot-field',
        nargs='?',
        help='Define a pivot field, e.g. fixVersions')
    
    parser_jql.set_defaults(func=JQLCommand)
    
    return parser

def main(args=None):
    
    parser = create_parser(settings)
    my_args = parser.parse_args(args)

    if not my_args.func:
         parser.print_usage()
         raise SystemExit()

    if my_args.debugLevel:
        Log.debugLevel = my_args.debugLevel
    
    # filter out arguments commands do not need to understand
    func_args = {k:v for k,v in vars(my_args).items()
                 if k not in ['func', 'subparser_name', 'outfile', 'debugLevel',
                              'suppress_progress', 'user', 'password',
                              'delimiter', 'encoding', 'oneShot']}

    # build up some additional keyword args for the commands
    if not my_args.suppress_progress:
        func_args.update({'progress_cb': _progress})

    if my_args.oneShot:
        func_args.update({'continue_cb': lambda: False})

    # get/store user private Jira credentials from OS keyring
    username, password = creds.get_credentials(my_args.user,
                                               my_args.password)
    func_args.update({
        'username': username,
        'password': password
    })

    Log.debug('Args: {0}'.format(func_args))
    command = my_args.func(**func_args)
    output_writer = command.writer
    try:
        with _open(my_args.outfile, my_args.encoding) as f:
            output_writer.write(f, command, my_args.encoding,
                                     delimiter=my_args.delimiter)
    except HTTPError as err:
        if err.response.status_code == 401:
            creds.clear_credentials(username)
        raise err

if __name__ == "__main__":
    locale.setlocale(locale.LC_TIME, 'en_US')
    main(args=sys.argv[1:])

