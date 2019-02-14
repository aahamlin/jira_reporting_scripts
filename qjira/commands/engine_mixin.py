from ..config import settings
from .. import jira

class EngineMixin(object):

    def __init__(self, *args, **kwargs):
        effort_engine_name = settings.get('jira','default_effort_engine')
        self._effort_field = settings.get(effort_engine_name, 'effort_field')

    @property
    def effort_field(self):
        return self._effort_field

    def request_fields(self):
        fields = []
        fields.append(jira.customfield_value(self.effort_field))
        return fields
