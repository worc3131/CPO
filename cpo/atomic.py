
from threading import Lock
from typing import TypeVar, Generic

T = TypeVar('T')
class Atomic(Generic[T]):
    # these atomic operations can be implemented much more effectively
    # at the machine level by using opcodes XCHG etc.
    def __init__(self, value: T) -> None:
        self._value: T = value
        self._lock = Lock()

    def get(self) -> T:
        with self._lock:
            return self._value

    def set(self, v: T):
        with self._lock:
            self._value = v

    def get_and_set(self, v: T):
        with self._lock:
            result = self._value
            self._value = v
            return result

    def get_and_update(self, f):
        with self._lock:
            result = self._value
            self._value = f(self._value)
            return result

    def compare_and_set(self, expect: T, update: T) -> bool:
        with self._lock:
            if self._value == expect:
                self._value = update
                return True
            else:
                return False

    def __str__(self):
        return str(self._value)

TNum = TypeVar('TNum', int, float)
class AtomicNum(Atomic[TNum]):

    def inc(self, d: TNum) -> TNum:
        with self._lock:
            self._value += d
            return self._value

    def dec(self, d: TNum) -> TNum:
        return self.inc(-d)


class AtomicCounter(AtomicNum):
    # while cpythons itertools.counter is atomic this is
    # an implementation details which isnt guaranteed to hold
    def __init__(self, value: int = 0):
        super().__init__(value)

    def __iter__(self):
        return self

    def __next__(self):
        return self.inc(1)