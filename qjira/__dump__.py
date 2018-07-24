import sys
import io
import os
import argparse
import locale
import six

from requests.exceptions import HTTPError
from dateutil import parser as date_parser

from .config import settings
from . import Log
from . import credential_store as creds

from .encoder import _encode
from .commands import JQLCommand

def dump_command(command, encoding):
    headers = dict(settings['headers'].items())
    Log.debug(headers)
    issue = next(command.execute())
    Log.debug('Retrieved {}'.format(issue))
    for k in sorted(issue):
        print('{} ({}):\t{}'.format(k, headers.get(k.lower()), issue[k]))

def create_parser(settings):

    base_url = settings['jira']['base_url']
    
    parser = argparse.ArgumentParser(
        prog='qjira_dump',
        description='Dump content of a single issuekey')

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

    parser.add_argument('--encoding',
        metavar='ENC',
        default='ASCII',
        help='Specify an output encoding. In Python 2.x, only default ASCII is supported.')

    parser.add_argument('-A', '--all-fields',
        action='store_true',
        help='Extract all "navigable" fields in Jira, [fields=*navigable]')

    
    parser.add_argument('--add-field', '-f',
        action='append',
        metavar='NAME',
        help='Add field(s) to Jira request')

    parser.add_argument('--add-column', '-c',
        action='append',
        metavar='NAME',
        help='Add column(s) to CSV output')

    parser.add_argument('issuekey',
        help='Provide an issuekey value.')

    parser.set_defaults(func=JQLCommand)
    
    return parser


def main(args=None):
    
    parser = create_parser(settings)
    my_args = parser.parse_args(args)

    if not my_args.func:
        parser.print_usage()
        raise SystemExit()

    if not my_args.issuekey:
        parser.print_usage()
        raise SystemExit()
    
    if my_args.debugLevel:
        Log.debugLevel = my_args.debugLevel

    func_args = {k:v for k,v in vars(my_args).items()
                 if k not in ['func', 'user', 'password', 'debugLevel', 'encoding', 'issuekey']}
        
    # get/store user private Jira credentials from OS keyring
    username, password = creds.get_credentials(my_args.user,
                                               my_args.password)

    func_args.update({
        'username': username,
        'password': password,
        'jql': 'issuekey = %s' % my_args.issuekey
    })

    command = my_args.func(**func_args)
    
    try:
        dump_command(command, my_args.encoding)
    except HTTPError as err:
        if err.response.status_code == 401:
            creds.clear_credentials(username)
        raise err

if __name__ == "__main__":
    locale.setlocale(locale.LC_TIME, 'en_US')
    main(args=sys.argv[1:])
