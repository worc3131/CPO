
from abc import ABC

from . import semaphore

class Lock(ABC):

    def lock(self) -> None:
        raise NotImplementedError

    def unlock(self) -> None:
        raise NotImplementedError

    def __enter__(self):
        self.lock()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unlock()

    def with_lock(self, f):
        with self:
            f()

class SimpleLock(Lock, semaphore._BooleanSemaphore):

    def lock(self) -> None:
        self.acquire()

    def unlock(self) -> None:
        self.release()

