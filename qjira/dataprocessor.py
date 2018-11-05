
'''data.py - process a jira issue'''
import re
from dateutil import parser as date_parser

from .text_utils import _generate_name, _isstring
from .log import Log

re_prog = re.compile('[0-9]{4}\-[0-9]{2}\-[0-9]{2}T[0-9]{2}\:[0-9]{2}:[0-9]{2}\.[0-9]{3}\-[0-9]{4}')

def flatten_json_struct(data, count_fields=[], datetime_fields=[]):
    """data is a dict of nested JSON structures, returns a flattened array of tuples.

    Skips entry when value is None
    """
    #print('flatten_json_struct: ', data)
    for k,v in data.items():
        if v and type(v) != dict and type(v) != list:
            if k in datetime_fields and re_prog.match(v):
                #print('> yielding date {0}'.format(k))
                yield k, date_parser.parse(v).date()
            elif _isstring(v):
                #print('> yielding value {0}: {1}'.format(k, repr(v)))
                yield k, v.replace('\r', '').replace('\n', ' ')
            else:
                #print('> yielding value {0}: {1}'.format(k, repr(v)))
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



def load_changelog(data):
    update_data_history(data, _create_history)

def load_transitions(data):
    histories = sorted(data['_changelog']['histories'], key=lambda x: x['created'])
    transitions = [_transition(dict(item, created=h['created']))
                   for h in histories for item in h['items']
                   if item['field'] == 'status']
    #print('>> transitions', transitions)
    data.update({'transitions': transitions})
    
def update_data_history(data, callback):
    if data.get('_changelog'):
        histories = sorted(data['_changelog']['histories'], key=lambda x: x['created'])
        #print('load_changelog found {} history entries'.format(len(histories)))
        change_history = dict([callback(dict(item, created=h['created']))
                               for h in histories for item in h['items']])
        data.update(change_history)

def _create_history(history):
    '''Create a tuple of important info from a changelog history.'''
    if history['field'] == 'status' and history['toString']:
        field_name = history['field'].replace(' ', '')
        normalized_string = history['toString'].replace(' ', '')
    else:
        field_name = history['field'].replace(' ', '_').lower()
        normalized_string = 'changed'
    created_date = date_parser.parse(history['created']).date()
    entry = _generate_name(field_name,normalized_string), created_date
    #print ('Entry;',entry)
    return entry

def _transition(history):
    '''Create a tuple of important info from a changelog history.'''
    normalized_from_string = history.get('fromString', 'New')
    normalized_to_string = history.get('toString', 'Open')
    field_name = 'from_{0}'.format(normalized_from_string).replace(' ', '')
    normalized_string = 'to_{0}'.format(normalized_to_string).replace(' ', '')
    created_date = date_parser.parse(history['created']).date()
    name = _generate_name(field_name,normalized_string)
    #print ('Entry;',entry)
    return {
        'name': name,
        'change_date': created_date
    }

