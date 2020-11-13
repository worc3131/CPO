
import collections
from dataclasses import dataclass
import inspect
import threading
from typing import Deque

from . import conc
from . import config
from .register import Debuggable
from . import util
from .util import Nanoseconds

@dataclass
class Event:
    timestamp: Nanoseconds
    thread_id: str
    tb: inspect.Traceback
    text: str

    def __str__(self):
        return f'{self.timestamp}:: {self.thread_id}@{self.tb.function}: {self.text}'

class Logger(Debuggable):

    def __init__(self, name: str, log_size: int, mask: int = 0xFFFFFFFF):
        self.name = name
        self.log_size = log_size
        self.mask = mask
        self.entries: Deque[Event] = collections.deque()
        self.events: Deque[Event] = self.entries
        self.lock = threading.Lock()
        self.register()

    def log(self, bits: int, text):
        if self.mask & bits != bits:
            with self.lock:
                frame = inspect.currentframe()
                tb: inspect.Traceback = inspect.getframeinfo(frame)
                message = Event(
                    util.nano_time(),
                    conc.get_thread_identity(threading.current_thread()),
                    tb,
                    text()
                )
                self.entries.append(message)
                if len(self.entries) > self.log_size:
                    self.entries.popleft()

    __call__ = log

    def show_state(self, file):
        util.synced_print(f'{str(self)} Log', *self.entries, file=file)

    print_state = show_state

log = Logger("Logging", config.log_size, config.logging)
