
import operator
from typing import Generic, TypeVar

from . import semaphore

class Barrier:

    def __init__(self, n: int, name: str = "") -> None:
        assert n >= 1
        self.n = n
        self.name = name
        self.shared = n > 1
        self.waiting = 0
        self.wait = semaphore.BooleanSemaphore(
            available=False,
            name=f'{name}.wait',
        )
        self.enter = semaphore.BooleanSemaphore(
            available=True,
            name=f'{name}.enter'
        )

    def sync(self):
        self.enter.down()
        if self.waiting == self.n-1:
            self.wait.up()
        else:
            self.waiting += 1
            self.enter.up()
            self.wait.down()
            self.waiting -= 1
            if self.waiting == 0:
                self.enter.up()
            else:
                self.wait.up()

T = TypeVar('T')

class CombiningBarrier(Generic[T]):

    def __init__(self, n: int, e: T, op, name: str = ""):
        assert n > 1
        self.n = n
        self.e = e
        self.op = op
        self.name = name
        self.waiting = 0
        self.wait = semaphore.BooleanSemaphore(
            available=False,
            name=f'{name}.wait',
        )
        self.enter = semaphore.BooleanSemaphore(
            available=True,
            name=f'{name}.enter',
        )
        self.result = e

    def sync(self, t: T) -> T:
        self.enter.down()
        self.result = op(self.result, t)
        if self.waiting == n-1:
            try:
                return self.result
            finally:
                self.wait.up()
        else:
            self.waiting += 1
            self.enter.up()
            self.wait.down()
            self.waiting -= 1
            try:
                return self.result
            finally:
                if self.waiting == 0:
                    self.result = self.e
                    self.enter.up()
                else:
                    self.wait.up()


class OrBarrier(CombiningBarrier):

    def __init__(self, n: int, name: str = "OrBarrier"):
        CombiningBarrier.__init__(self, n, False, operator.or_, name)


class AndBarrier(CombiningBarrier):

    def __init__(self, n: int, name: str = "AndBarrier"):
        CombiningBarrier.__init__(self, n, True, operator.and_, name)
