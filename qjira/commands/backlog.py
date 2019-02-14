"""
Class encapsulating Backlog calculations. This will 
pivot the issues on fixVersion fields for sorting
between future unreleased versions and dev_backlog,
for example.
"""

from ..config import settings
from .base_command import BaseCommand
from ..log import Log

class BacklogCommand(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(BacklogCommand, self).__init__('backlog', pivot_field='fixVersions', *args, **kwargs)
    
    @property
    def count_fields(self):
        return ['customer']

