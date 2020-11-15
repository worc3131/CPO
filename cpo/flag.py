
import threading
from typing import Optional

from .atomic import Atomic
from .name import NameGenerator
from . import semaphore
from . import threads
from . import util
from .util import Singleton, Nanoseconds

class _Flag(semaphore.Semaphore):

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = Flag._gen_name(name)
        self._available = Atomic(False)
        self._waiting: Atomic[Optional[threading.Thread]] = Atomic(None)
        self._interrupted = False

    def __str__(self):
        nm = self.name
        av = ["unavailable", "available"][self._available.get()]
        itr = ["", "[cancelled]"][self._interrupted]
        wtr = threads.get_thread_identity(self._waiting.get())
        return f'FLAG {nm}: {av} {itr} [waiter: {wtr}]'

    def cancel(self) -> None:
        self._interrupted = True
        stalled = self._waiting.get_and_set(None)
        if stalled is not None:
            threads.unpark(stalled)
        self._available.set(True)

    def acquire(self) -> None:
        if self._available.get():
            return
        current = threading.current_thread()
        if not self._waiting.compare_and_set(None, current):
            raise Exception(f"Logic Error: cannot wait already awaited: {self}")
        while not self._available.get():
            threads.park_current_thread()

    def cancelled(self) -> bool:
        return self._interrupted

    def try_acquire(self, timeout: Nanoseconds) -> bool:
        if self._available.get():
            return True
        current = threading.current_thread()
        deadline = util.nano_time() + timeout
        waiting, outcome = True, True
        if not self._waiting.compare_and_set(None, current):
            raise Exception(f"Logic Error: {current} cannot await "
                            f"already awaited: {self} ")
        while waiting:
            if self._available.get():
                waiting = False
            else:
                left = deadline - util.nano_time()
                if left <= 0:
                    outcome, waiting = False, False
                else:
                    threads.park_current_threads_nanos(left)
                    if deadline < util.nano_time():
                        outcome, waiting = False, False
        return outcome

    def _get_waiting(self) -> threading.Thread:
        return self._waiting.get()

    def release(self) -> None:
        if self._available.compare_and_set(False, True):
            threads.unpark(self._waiting.get())
        else:
            raise Exception(f"Logic Error: Flag already released: {self}")

class _FlagFactory(NameGenerator, metaclass=Singleton):

    def __init__(self):
        super().__init__('Flag')

    def __call__(self, name: Optional[str] = None) -> _Flag:
        if name is None:
            name = self._new_name()
        return _Flag(name)

Flag = _FlagFactory()
