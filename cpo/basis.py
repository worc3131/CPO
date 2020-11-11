
from abc import ABC
from threading import Lock
from typing import Optional, TypeVar, Generic

T = TypeVar('T')

class Atomic(Generic[T]):
    def __init__(self, value: T) -> None:
        self._value = T(value)
        self._lock = Lock()

    def inc(self, d: T) -> T:
        with self._lock:
            self._value += T(d)
            return self._value

    def dec(self, d: T) -> T:
        return self.inc(-d)

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, v: T) -> T:
        with self._lock:
            self._value = T(v)
            return self._value

class AtomicCounter(Atomic):
    # while cpythons itertools.counter is atomic this is
    # an implementation details which isnt guaranteed to hold
    def __init__(self, value: int = 0):
        super().__init__(value)

    def next(self):
        return self.inc(1)


class NameGenerator:

    def __init__(self, _kind: str) -> None:
        self._kind = _kind
        self._occurs = AtomicCounter()

    def _gen_name(self, name: str) -> str:
        if name is None:
            return f'{self._kind}-{self._occurs.next()}'
        return name

    def _new_name(self, kind: Optional[str] = None) -> str:
        if kind is None:
            kind = self._kind
        return f'{kind}-{self._occurs.next()}'

class Named(ABC):

    def __init__(self):
        self._name: str = "<anonymous>"
        self._name_generator: Optional[NameGenerator] = None

    @property
    def name(self) -> str:
        return self._name

    def with_name(self, __name: str) -> str:
        self._name = __name
        return self._name

    @property
    def name_generator(self) -> NameGenerator:
        if self._name_generator is None:
            self._name_generator = NameGenerator('!?!?')
        return self._name_generator

    def set_name(self, name: str):
        self._name = self.name_generator._gen_name(name)

    def __str__(self) -> str:
        return self.name

def get_prop_else(name, orelse, coerce = None):
    raise NotImplementedError

class Nanoseconds(int):
    pass

class Milliseconds(int):
    pass

def get_thread_identity(thread):
    if thread is None:
        return "?"
    raise NotImplementedError

def park_until_deadline_or(blocker, deadline: Nanoseconds, condition) -> Nanoseconds:
    raise NotImplementedError

def park_until_elapsed_or(blocker, timeout: Nanoseconds, condition) -> Nanoseconds:
    raise NotImplementedError


