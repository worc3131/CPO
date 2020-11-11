
import threading
from typing import Optional

from .atomic import AtomicNum
from .util import Nanoseconds

class CountDownLatch:
    def __init__(self, count: int):
        self._event = threading.Event()
        self._count = AtomicNum(count)
        if count <= 0:
            self._event.set()

    def count_down(self):
        if self._count.dec(1) <= 0:
            self._event.set()

    def wait(self):
        self._event.wait()

def get_thread_identity(thread: Optional[threading.Thread]):
    if thread is None:
        return "?"
    return f'{thread.getName()}#{thread.ident}'

# python doesnt allow us to park threads, so this is a hack for now
# the use of concurrency primitives will mean that the parking and
# unparking is handled at the kernel level and so is slow.
# otherwise we would def park(blocker: Optional[Thread])

parking_lot = {}

def park_current_thread():
    ident = threading.get_ident()
    assert not ident in parking_lot
    parking_lot[ident] = threading.Event()
    parking_lot[ident].wait()
    parking_lot[ident].clear()
    del parking_lot[ident]  # TODO remove this safety check and the assert above

def unpark(blocker: Optional[threading.Thread]):
    if blocker is None:
        return
    ident = blocker.ident
    assert ident in parking_lot  # TODO remove assert
    parking_lot[ident].set()

def park_until_deadline_or(blocker, deadline: Nanoseconds, condition) -> Nanoseconds:
    raise NotImplementedError

def park_until_elapsed_or(blocker, timeout: Nanoseconds, condition) -> Nanoseconds:
    raise NotImplementedError
