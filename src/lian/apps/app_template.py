
import dataclasses
from types import SimpleNamespace
from lian.util import util

class EventData:
    def __init__(self, lang = "", event = -1, in_data = {}, out_data = {}):
        self.lang = lang
        self.event = event
        self.in_data = in_data
        if isinstance(in_data, dict):
            self.in_data = SimpleNamespace(**in_data)
        self.out_data = out_data

    def __repr__(self):
        return f"EventData(lang={self.lang}, event={self.event}, in_data={self.in_data}, out_data={self.out_data})"

@dataclasses.dataclass
class EventHandler:
    langs: str
    event: int
    handler: object

class AppSummary:
    def __init__(self, app_manager):
        self.app_manager = app_manager
        self.app_path = __file__

    def enable(self):
        # self.app_manager.register(event, None)
        pass
