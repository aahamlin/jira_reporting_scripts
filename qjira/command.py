""" Command base class for processing Jira issues"""

from .dataprocessor import DataProcessor
from .log import Log

class Command(object):

    def __init__(self, *args, **kwargs):
        self.processor = kwargs.get('processor', DataProcessor())

    @property
    def header(self):
        raise NotImplementedError()

    @property
    def query(self):
        raise NotImplementedError()
        
    def process(self, flat_list):
        """ Process a list of raw issues from Jira.
        Each item in the list could become 0..N rows of data, depending on
        how the DataProcessor settings, e.g. pivot='sprint' will explore the
        sprint array into 0..N rows per issue.
        """
        Log.debug('Transforming {0} issues', len(flat_list))
        rows = [row for item in flat_list for row in self.processor.transform(item)]
        Log.debug('Processing {} rows', len(rows))
        return self.post_process(rows)

    def post_process(self, rows):
        raise NotImplementedError()