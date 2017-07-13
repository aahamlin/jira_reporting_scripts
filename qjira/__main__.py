#!python
'''
main.py
Author: Andrew Hamlin
Description: script to execute commands against jira
'''

import sys
import argparse
import getpass
import csv

import keyring
import locale
from requests.exceptions import HTTPError

from .velocity import Velocity
from .cycletime import CycleTime
from .summary import Summary
from .jira import Jira
from .log import Log

def _progress (start, total):
    msg = '\rRetrieving {} of {}...'.format(start, total)
    if start >= total:
        msg = ' ' * len(msg)
        sys.stderr.write('\r' + msg)
        sys.stderr.flush()
        msg += '\rRetrieved {} issues\n'.format(start, total)
    sys.stderr.write(msg)
    sys.stderr.flush()

def _get_credentials (username, password):
    if not username:
        username = getpass.getuser()

    _needs_storage = True
    
    if not password:
        # retrieve password from system storage
        if keyring.get_keyring():
            password = keyring.get_password('qjira-sp', username)
            if password:
                _needs_storage = False

    if not password:
        password = getpass.getpass('Enter password for {}: '.format(username))
        
    if _needs_storage and keyring.get_keyring():
        keyring.set_password('qjira-sp', username, password)
        
    return username, password

def _clear_credentials(username):
    if username and keyring.get_keyring():
        keyring.delete_password('qjira-sp', username)

def _create_parser():
    
    # process command line arguments
    parser_common = argparse.ArgumentParser(add_help=False)
    
    parser_common.add_argument('-p', '--project',
                        metavar='project',
                        action='append',
                        required=True,
                        help='Project name')
    parser_common.add_argument('-F', '--fix-version',
                        dest='fixversion',
                        metavar='fixVersion',
                        action='append',
                        help='Restrict search to fixVersion(s)')
    parser_common.add_argument('-o', '--outfile',
                        metavar='file',
                        nargs='?',
                        default=sys.stdout,
                        help='Output file (.csv) [default: stdout]')
    parser_common.add_argument('--no-progress',
                        action='store_true',
                        dest='suppress_progress',
                        help='Hide data download progress')       
    parser_common.add_argument('-b', '--base',
                        dest='base_url',
                        metavar='url',
                        help='Jira Cloud base URL [default: sailpoint.atlassian.net]',
                        default='sailpoint.atlassian.net')
    parser_common.add_argument('-u', '--user',
                        metavar='user',
                        help='Username [default: %s]' % getpass.getuser(),
                        default=None)
    parser_common.add_argument('-w', '--password',
                        metavar='pwd',
                        help='Password (insecure), if blank will prommpt',
                        default=None)
    parser_common.add_argument('-d',
                        dest='debugLevel',
                        action='count',
                        help='Debug level')
    parser_common.add_argument('-1', '--one-shot',
                        action='store_true',
                        help='Exit after 1 HTTP request (for debug purpose only)')
    parser_common.add_argument('-A', '--all-fields',
                        action='store_true',
                        help='Extract all available fields')

    parser = argparse.ArgumentParser(prog='qjira', description='Export data from Jira to CSV format')

    # sub-commands: velocity, cycletimes, summary

    subparsers = parser.add_subparsers(title='Available commands', dest='subparser_name', help='Available commands to process data')

    parser_cycletime = subparsers.add_parser('c',
                                             parents=[parser_common],
                                             help='Produce [c]ycletime data')
    parser_cycletime.set_defaults(func=CycleTime)

    parser_velocity = subparsers.add_parser('v',
                                            parents=[parser_common],
                                            help='Produce [v]elocity data')
    parser_velocity.set_defaults(func=Velocity)

    parser_summary = subparsers.add_parser('s',
                                           parents=[parser_common],
                                           help='Produce [s]ummary report')
    parser_summary.set_defaults(func=Summary)

    return parser

def _create_outfile(out):

    if out is sys.stdout:
        return out

    try:
        outfile = open(out, 'w', newline='')
    except TypeError:
        outfile = open(out, 'wb')

    return outfile


def _validate_args(parser, args):
    if not args.subparser_name:
        parser.print_usage()
        raise SystemExit()
   
def _create_service(args, username, password):
        
    func_progress = None if args.suppress_progress else _progress

    return Jira(args.base_url, username=username, password=password, one_shot=args.one_shot, all_fields=args.all_fields, progress=func_progress)
    
def _create_query_string(args, processor):
            
    query = []
    if args.fixversion:
        query.append('fixVersion in ({})'.format(','.join(args.fixversion)))
    if args.project:
        query.append('project in ({})'.format(','.join(args.project)))
    if processor.query:
        query.append(processor.query)

    return ' AND '.join(query)

def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]
    
    parser = _create_parser()
    
    args = parser.parse_args(argv)

    _validate_args(parser, args)
    
    if args.debugLevel:
        Log.debugLevel = args.debugLevel

    # handle username/password input
    username, password = _get_credentials(args.user, args.password)        

    service = _create_service(args, username, password)

    processor = args.func(service)

    query_string = _create_query_string(args, processor)

    try:
        issues = service.get_project_issues(query_string)
    except HTTPError as err:
        if 401 == err.response.status_code:
            _clear_credentials(username)
        raise err

    with _create_outfile(out=args.outfile) as outfile:
        entries = processor.process(issues)
        fieldnames = processor.header
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)

if __name__ == "__main__":

    locale.setlocale(locale.LC_TIME, 'en_US')
    
    main()

