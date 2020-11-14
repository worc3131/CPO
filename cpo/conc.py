
import threading
import dummy_threading
from typing import Optional, Type

from .atomic import AtomicNum
from . import util
from .util import Nanoseconds

class CountDownLatch:
    def __init__(self, count: int = 1):
        self._event = threading.Event()
        self._count = AtomicNum(count)
        if count <= 0:
            self._event.set()

    def count_down(self):
        if self._count.dec(1) <= 0:
            self._event.set()

    def wait(self):
        self._event.wait()

# TODO find a better (but still safe) way of doing this
RLockClass: Type[threading.RLock] = util.get_ultimate_type(threading.RLock)
class XRLock(RLockClass):

    def __init__(self):
        self._waiters = set()
        # last but maybe not current owner (if there is no owner)
        self._last_owner = None

    def acquire(self, *args, **kwargs) -> bool:
        t = threading.current_thread()
        self._waiters.add(t)
        result = super().acquire(*args, **kwargs)
        self._last_owner = t
        self._waiters.remove(t)
        return result

    def get_waiting(self, cond=None):
        if cond is None:
            return list(self._waiters)
        else:
            return [x for x in self._waiters if cond(x)]

    def last_owner(self):
        return self._last_owner

NoLock = dummy_threading.Lock

