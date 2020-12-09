
from threading import Lock
from typing import TypeVar, Generic

T = TypeVar('T')
class Atomic(Generic[T]):
    """A class providing a variable with atomic operations"""
    # these atomic operations can be implemented much more effectively
    # at the machine level by using opcodes XCHG etc.
    def __init__(self, value: T) -> None:
        """

        Args:
            value: The initial value of the atomic
        """
        self._value: T = value
        self._lock = Lock()

    def get(self) -> T:
        """

        Returns: The current value of the atomic

        """
        with self._lock:
            # is this lock needed?
            return self._value

    def set(self, v: T) -> None:
        """

        Args:
            v: The value to set for the atomic

        Returns: None

        """
        with self._lock:
            # is this lock needed?
            self._value = v

    def get_and_set(self, v: T):
        """Get the current value of the atomic and update the atomics value.

        Args:
            v: The value to set for the atomic

        Returns: The value of the atomic before we set v

        """
        with self._lock:
            result = self._value
            self._value = v
            return result

    def get_and_update(self, f):
        """Get the current value of the atomic and update the atomic according
        to a function.

        Args:
            f: The function to apply to the existing value of the atomic.

        Returns: The value of the atomic before we applied the function.

        """
        with self._lock:
            result = self._value
            self._value = f(self._value)
            return result

    def compare_and_set(self, expect: T, update: T) -> bool:
        """Update the atomic if and only if it's existing value is as expected.

        Args:
            expect: Only update the atomic if it's value equals expect
            update: The value to set for the atomic

        Returns: True if the atomic was updated otherwise False

        """
        with self._lock:
            if self._value == expect:
                self._value = update
                return True
            else:
                return False

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f'Atomic({repr(self._value)})'

TNum = TypeVar('TNum', int, float)
class AtomicNum(Atomic[TNum]):
    """A class providing a number with atomic operations"""

    def inc(self, d: TNum) -> TNum:
        """Increment the atomic number by d.

        Args:
            d: The amount to increment the atomic by.

        Returns: The new value of the atomic.

        """
        with self._lock:
            self._value += d
            return self._value

    def dec(self, d: TNum) -> TNum:
        """Decrement the atomic number by d.

        Args:
            d: The amount to decrement the atomic by.

        Returns: The new value of the atomic.

        """
        return self.inc(-d)


class AtomicCounter(AtomicNum):
    """A class which provides an atomic counter"""
    # while cpythons itertools.counter is atomic this is
    # an implementation details which isnt guaranteed to hold
    def __init__(self, value: int = 0):
        super().__init__(value)

    def __iter__(self):
        return self

    def __next__(self):
        return self.inc(1)
