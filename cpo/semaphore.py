
from abc import ABC
import queue
import threading
from typing import List, Optional, Sequence

from .atomic import Atomic, AtomicNum
from .name import NameGenerator
from .queue import LockFreeQueue
from . import threads
from . import util
from .util import Nanoseconds, Singleton


class Semaphore(ABC):

    def acquire(self) -> None:
        raise NotImplementedError

    def release(self) -> None:
        raise NotImplementedError

    def down(self) -> None:
        self.acquire()

    def up(self) -> None:
        self.release()

    def try_acquire(self, timeout: Nanoseconds) -> bool:
        raise NotImplementedError

    def get_waiting(self) -> List[threading.Thread]:
        raise NotImplementedError

    def remaining(self) -> int:
        return 0

    def cancel(self) -> None:
        raise NotImplementedError

    def cancelled(self) -> bool:
        raise NotImplementedError

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class _BooleanSemaphore(Semaphore):

    def __init__(self, available: bool, name: str,
                 fair: bool, parent, spin: int = 5) -> None:
        self.name = BooleanSemaphore._gen_name(name)
        self.fair = fair
        self.spin = spin
        self._owner = Atomic(None if available else threading.current_thread())
        self._waiting: LockFreeQueue[threading.Thread] = LockFreeQueue()
        self._behalf = self if parent is None else parent
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True
        n = self._waiting.length()
        while n > 0:
            n -= 1
            self.release()

    def __str__(self):
        nm = self.name
        owner = self._owner.get()
        ow = "available" if owner is None \
            else threads.get_thread_identity(owner)
        can = "[cancelled]" if self._cancelled else ""
        ln = self._waiting.length()
        id = ", ".join(threads.get_thread_identity(t)
                       for t in self._waiting.elements())
        return f'{nm}: {ow} {can} [{ln} {id}]'

    def acquire_fast(self, owner: threading.Thread) -> bool:
        for _ in range(self.spin):
            if self._owner.compare_and_set(None, owner):
                return True
        return False

    def throw_interrupt(self):
        raise InterruptedError(
            f"Semaphore Interrupted: {self} for {self._behalf}"
        )

    def acquire(self) -> None:
        if self._cancelled:
            return
        current = threading.current_thread()
        if self.acquire_fast(current):
            return
        self._waiting.enqueue(current)
        while self._waiting.peek() != current or \
                not self._owner.compare_and_set(None, current):
            threads.park_current_thread()
        self._waiting.remove_first()

    def cancelled(self) -> bool:
        return self._cancelled

    def release(self) -> None:
        self._owner.set(None)
        waiter = self._waiting.peek()
        threads.unpark(waiter)

    def try_acquire(self, timeout: Nanoseconds) -> bool:
        if self._cancelled:
            return False
        current = threading.current_thread()
        if self.acquire_fast(current):
            return True
        if self._cancelled:
            return False
        deadline = util.nano_time() + timeout
        left = timeout
        trying = True
        outcome = False
        self._waiting.enqueue_first(current)
        while trying:
            if self._waiting.peek() == current and \
                    self._owner.compare_and_set(None, current):
                trying = False
                outcome = True
            else:
                threads.park_current_thread_nanos(left)
                left = deadline - util.nano_time()
                trying = left > 0
        self._waiting.remove_first()
        return outcome

    def get_waiting(self) -> List[threading.Thread]:
        return self._waiting.elements()

    def remaining(self) -> int:
        return 0 if self._owner.get() is not None else 1

class _BooleanSemaphoreFactory(NameGenerator, metaclass=Singleton):

    def __init__(self):
        super().__init__('BooleanSemaphore')

    def __call__(self, available: bool = False,
                 name: Optional[str] = None,
                 fair: bool = False,
                 parent=None,
                 spin: int = 5) -> _BooleanSemaphore:
        if name is None:
            name = self._new_name()
        if fair:
            raise NotImplementedError
        return _BooleanSemaphore(available, name, fair, parent, spin)

BooleanSemaphore = _BooleanSemaphoreFactory()

class _CountingSemaphore(Semaphore):

    def __init__(self, available: int, name: str,
                 fair: bool, parent, spin: int = 5) -> None:
        self.name = CountingSemaphore._gen_name(name)
        self.fair = fair
        self.spin = spin
        self._count = AtomicNum(available)
        self._waiting: LockFreeQueue[threading.Thread] = LockFreeQueue()
        self._behalf = self if parent is None else parent
        self._cancelled = False

    def __str__(self) -> str:
        nm = self.name
        cnt = self._count.get()
        can = "[cancelled]" if self._cancelled else ""
        ln = self._waiting.length()
        id = ", ".join(threads.get_thread_identity(t)
                       for t in self._waiting.elements())
        return f'{nm}: {cnt} available [{ln} {id}]'

    def cancel(self) -> None:
        self._cancelled = True
        for _ in range(self._waiting.length()):
            self.release()

    def acquire_fast(self) -> bool:
        for _ in range(self.spin):
            if self.atomic_dec():
                return True
        return False

    def throw_interrupt(self):
        raise InterruptedError(
            f"Semaphore Interrupted: {self} for {self._behalf}"
        )

    def acquire(self) -> None:
        if self._cancelled:
            return
        if self.acquire_fast():
            return
        current = threading.current_thread()
        self._waiting.enqueue(current)
        while self._waiting.peek() != current or \
            not self.atomic_dec():
            threads.park_current_thread()
        self._waiting.remove_first()
        if self._count.get() > 0:
            self.signal()

    def atomic_dec(self) -> bool:
        return 0 < self._count.get_and_update(
            lambda x: x-1 if x > 0 else x
        )

    def signal(self) -> None:
        threads.unpark(self._waiting.peek())

    def release(self) -> None:
        if self._count.inc(1) > 0:
            self.signal()

    def reinitialize(self) -> None:
        assert self._waiting.length() > 0
        self._count.set(0)
        self._waiting.clear()

    def cancelled(self) -> bool:
        return self._cancelled

    def try_acquire(self, timeout: Nanoseconds) -> bool:
        if self._cancelled:
            return False
        if self.acquire_fast():
            return True
        current = threading.current_thread()
        deadline = util.nano_time() + timeout
        left = timeout
        trying = True
        outcome = False
        self._waiting.enqueue_first(current)
        while trying and not self._cancelled:
            if self._waiting.peek() == current and \
                    self.atomic_dec():
                trying = False
                outcome = True
            else:
                threads.park_current_thread_nanos(left)
                left = deadline - util.nano_time()
                trying = left > 0
        self._waiting.remove_first()
        if self._count.get() > 0:
            self.signal()
        return outcome


    def get_waiting(self) -> List[threading.Thread]:
        return self._waiting.elements()

    def remaining(self) -> int:
        return self._count.get()


class _CountingSemaphoreFactory(NameGenerator, metaclass=Singleton):

    def __init__(self):
        super().__init__('CountingSemaphore')

    def __call__(self, available: int = 0,
                 name: Optional[str] = None,
                 fair: bool = False,
                 parent=None,
                 spin: int = 5) -> _CountingSemaphore:
        if name is None:
            name = self._new_name()
        if fair:
            raise NotImplementedError
        return _CountingSemaphore(available, name, fair, parent, spin)

CountingSemaphore = _CountingSemaphoreFactory()
