
import collections
from dataclasses import dataclass
import inspect
import threading
import types
from typing import Deque, Optional

from . import config
from .register import Debuggable
from . import threads
from . import util
from .util import Nanoseconds

@dataclass
class Event:
    timestamp: Nanoseconds
    thread_id: str
    tb: Optional[inspect.Traceback]
    text: str

    def __str__(self):
        fn: str = "unknown" if self.tb is None else str(self.tb.function)
        return f'{self.timestamp}:: {self.thread_id}@{fn}: {self.text}'

class Logger(Debuggable):

    def __init__(self, name: str, log_size: int, mask: int = 0xFFFFFFFF):
        super().__init__()
        self.name = name
        self.log_size = log_size
        self.mask = mask
        self.entries: Deque[Event] = collections.deque()
        self.events: Deque[Event] = self.entries
        self.lock = threading.Lock()
        self.register()

    def log(self, text, bits: Optional[int] = None):
        if bits is None or self.mask & bits != bits:
            with self.lock:
                frame: Optional[types.FrameType] = inspect.currentframe()
                if frame is None:
                    tb = None
                else:
                    tb = inspect.getframeinfo(frame)
                message = Event(
                    util.nano_time(),
                    threads.get_thread_identity(threading.current_thread()),
                    tb,
                    text
                )
                self.entries.append(message)
                if len(self.entries) > self.log_size:
                    self.entries.popleft()

    __call__ = log

    def show_state(self, file):
        util.synced_print(f'{str(self)} Log', *self.entries, file=file)

    print_state = show_state

log = Logger("Logging", config.log_size, config.logging)
