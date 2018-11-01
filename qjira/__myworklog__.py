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

from .text_utils import _encode
from .commands import WorklogCommand

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

def create_parser(settings):

    base_url = settings.get('jira','base_url')
    
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

    parser.add_argument('--delimiter',
        metavar='CHAR',
        default=',',
        help='Specify a CSV delimiter [default: comma].\nFor bash support escape the character with $, such as $\'\\t\'')

    parser.add_argument('-o', '--outfile',
        metavar='FILENAME',
        nargs='?',
        default=None,
        help='Output file (.csv) [default: stdout]')

    parser.set_defaults(func=WorklogCommand)
    
    return parser


def main(args=None):
    
    parser = create_parser(settings)
    my_args = parser.parse_args(args)

    if not my_args.func:
        parser.print_usage()
        raise SystemExit()
    
    if my_args.debugLevel:
        Log.debugLevel = my_args.debugLevel

    func_args = {k:v for k,v in vars(my_args).items()
                 if k not in ['func', 'user', 'password', 'debugLevel', 'encoding', 'outfile', 'delimiter']}
        
    # get/store user private Jira credentials from OS keyring
    username, password = creds.get_credentials(my_args.user,
                                               my_args.password)

    func_args.update({
        'username': username,
        'password': password,
        'restrict_to_username': True
    })

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
