
import operator
from typing import Generic, TypeVar

from . import semaphore

class Barrier:
    """A Barrier(n) supports the repeated synchronisation of n processes. If b
    is such a barrier then b.sync calls are stalled until n have been made. When
    n==1 then b.sync returns immediately: this is so multi-worker structures can
    be tested with only a single-worker. This implementation remains single
    minded."""

    def __init__(self, n: int, name: str = "") -> None:
        """

        Args:
            n: The number of processes to synchronise.
            name: The name of the barrier for debugging.
        """
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

    def sync(self) -> None:
        """Wait until all n processes have called sync

        Returns: None

        """
        self.enter.down()
        if self.waiting == self.n-1:  # the last process arrives
            self.wait.up()            # everyone can proceed
        else:                         # a process arrives that isnt the last
            self.waiting += 1
            self.enter.up()
            self.wait.down()          # make it wait
            self.waiting -= 1
            if self.waiting == 0:
                self.enter.up()       # the last waiting process awoke
            else:
                self.wait.up()        # pass the baton to another waiter

T = TypeVar('T')

class CombiningBarrier(Generic[T]):
    """A CombiningBarrier(n, e, op) supports the repeated synchronisation of n
    proceesses. If b is such a barrier then b.sync(x) calls are stalled until n
    have been made. We say that such a call contributes x. If the syncing calls
    contribute x1, x2, .., xn and op(a, b) = a @ b then the value they all
    return is e @ x1 @ x2 @ .. @ xn. The function op would ideally be
    associative, or else the return value will depend upon the order in which
    the processes arrive at the barrier.
    """

    def __init__(self, n: int, e: T, op, name: str = ""):
        """

        Args:
            n: The number of processes to wait on.
            e: The initial value of the barrier.
            op: The operation to apply between contributions.
            name: The name of the barrier for debugging.
        """
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
        """Wait until all n processes have called sync, then return the value
        calculated with op, and e from the individual processes' contributions.

        Args:
            t: The contribution of this process

        Returns:

        """
        self.enter.down()
        self.result = self.op(self.result, t)  # add the last contribution
        if self.waiting == self.n-1:           # the last process arrives
            try:
                return self.result
            finally:
                self.wait.up()                 # everyone can proceed
        else:                                  # a process arrives that isn't
            self.waiting += 1                  # the last
            self.enter.up()                    # another can enter
            self.wait.down()                   # the caller waits
            self.waiting -= 1                  # after the wait finishes
            try:
                return self.result             # return the result
            finally:
                if self.waiting == 0:
                    self.result = self.e
                    self.enter.up()
                else:
                    self.wait.up()


class OrBarrier(CombiningBarrier):
    """A combining barrier which is equivalent to any()"""

    def __init__(self, n: int, name: str = "OrBarrier"):
        CombiningBarrier.__init__(self, n, False, operator.or_, name)


class AndBarrier(CombiningBarrier):
    """A combining barrier which is equivalent to all()"""

    def __init__(self, n: int, name: str = "AndBarrier"):
        CombiningBarrier.__init__(self, n, True, operator.and_, name)
