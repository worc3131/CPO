
from abc import ABC
from typing import Optional

from .name import NameGenerator
from . import semaphore
from .util import Singleton

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

class _SimpleLock(Lock, semaphore._BooleanSemaphore):

    def lock(self) -> None:
        self.acquire()

    def unlock(self) -> None:
        self.release()

class _SimpleLockFactory(NameGenerator, metaclass=Singleton):

    def __init__(self):
        super().__init__('SimpleLock')

    def __call__(self, name: Optional[str] = None,
                 parent=None) -> _SimpleLock:
        if name is None:
            name = self._new_name()
        return _SimpleLock(True, name, False, parent, 200)

SimpleLock = _SimpleLockFactory()



