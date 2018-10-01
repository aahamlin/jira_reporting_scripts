
'''data.py - process a jira issue'''
import re
from dateutil import parser as date_parser

from .text_utils import _generate_name
from .log import Log

re_prog = re.compile('[0-9]{4}\-[0-9]{2}\-[0-9]{2}T[0-9]{2}\:[0-9]{2}:[0-9]{2}\.[0-9]{3}\-[0-9]{4}')


def flatten_json_struct(data, count_fields=[], datetime_fields=[]):
    """data is a dict of nested JSON structures, returns a flattened array of tuples.

    Skips entry when value is None
    """
    for k,v in data.items():
        if v and type(v) != dict and type(v) != list:
            if k in datetime_fields and re_prog.match(v):
                #print('> yielding date {0}'.format(k))
                yield k, date_parser.parse(v).date()
            else:
                #print('> yielding value {0}: {1}'.format(k, v))
                yield k, v
        elif type(v) == list:
            if k in count_fields:
                #print('> yielding count of {0}'.format(k))
                yield k, len(v)
            else:
                new_data = { _generate_name(k,idx):val for idx,val in enumerate(v) }
                #print ('recursing %s' % new_data)
                for item in flatten_json_struct(new_data,
                                                count_fields=count_fields,
                                                datetime_fields=datetime_fields):
                    #print('> yielding {0}: {1}'.format(item, type(item)))
                    yield item[0], item[1]            
        elif type(v) == dict:
            new_data = { _generate_name(k, k1): v1 for k1, v1 in v.items()}
            #print ('recursing %s' % new_data)
            for item in flatten_json_struct(new_data,
                                            count_fields=count_fields,
                                            datetime_fields=datetime_fields):
                #print('> yielding {0}: {1}'.format(item, type(item)))
                yield item[0], item[1]
