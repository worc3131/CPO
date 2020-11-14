
from abc import ABC
import threading
import dummy_threading
from typing import List, Optional, Type

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

NoLock = dummy_threading.Lock

# TODO find a better (but still safe) way of doing this
NoLockClass: Type[NoLock] = util.get_ultimate_type(NoLock)
RLockClass: Type[threading.RLock] = util.get_ultimate_type(threading.RLock)

class Lock:
    # we wrap threading.Lock as it is non inheritable

    def __init__(self):
        self._lock = threading.Lock()

    def acquire(self, blocking: bool) -> None:
        return self._lock.acquire(blocking)

    def release(self) -> None:
        return self._lock.release()

    def locked(self) -> bool:
        return self._lock.locked()

    def __enter__(self):
        return self._lock.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._lock.__exit__()

    def __repr__(self) -> str:
        return self._lock.__repr__()

    def get_underlying_lock(self):
        return self._lock

class FairRLock(RLockClass):
    # TODO
    pass

class Tracked:

    def get_waiting(self, cond=None) -> List[threading.Thread]:
        raise NotImplementedError

    def num_waiting(self, cond=None) -> int:
        return len(self.get_waiting(cond))

    def latest_owners(self):
        raise NotImplementedError

class TrackedMixin(Tracked):

    def __init__(self):
        super().__init__()
        self._waiters = set()
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

    def latest_owners(self):
        return [self._last_owner]

class TrackedNoLock(TrackedMixin, NoLockClass):
    pass

class TrackedLock(TrackedMixin, Lock):
    pass

class TrackedRLock(TrackedMixin, RLockClass):
    pass

class TrackedFairRLock(TrackedMixin, FairRLock):
    pass
