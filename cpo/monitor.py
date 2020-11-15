
from abc import ABC
import threading
from typing import List, Optional

from . import conc
from .register import Debuggable
from . import util
from .util import Nanoseconds

class Monitor(Debuggable, ABC):

    def __init__(self, name: Optional[str] = None) -> None:
        self.lock = conc.TrackedRLock()
        if name is None:
            name = repr(self)
        self.name = name

    def get_waiting(self, cond=None) -> List[threading.Thread]:
        if cond is None:
            raise NotImplementedError
        return self.lock.get_waiting(cond)

    def __str__(self) -> str:
        own = self.lock.latest_owners()
        w = self.get_waiting()
        if len(own) == 0 and len(w) == 0:
            return f'Monitor({self.name})'
        o = ', '.join(map(str, own))
        return f'Monitor({self.name}) owned by {o} awaited by {w}'

    def show_state(self, file):
        own = self.lock.latest_owners()
        w = self.get_waiting()
        if not(own == [] and len(w) == 0):
            util.synced_print(str(self), file=file)

    def has_state(self) -> bool:
        own = self.lock.latest_owners()
        w = self.get_waiting()
        return not (own == [] and len(w) == 0)

    new_condition = threading.Condition

    def with_lock(self, body):
        self.lock.acquire()
        try:
            body()
        finally:
            self.lock.release()

    def try_lock_for(self, ns: Nanoseconds, body, otherwise):
        if self.lock.acquire(timeout=ns.to_seconds()):
            try:
                body()
            finally:
                self.lock.release()
        else:
            otherwise()

    def waiting_for(self, cond) -> bool:
        if self.lock.acquire(blocking=False):
            try:
                return self.lock.has_waiters(cond)
            finally:
                self.lock.release()
        return False
