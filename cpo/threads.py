
import threading
import time
from typing import Callable, Optional, Sequence

from . import util
from .util import Nanoseconds

main_thread = threading.current_thread()

def get_active_threads() -> Sequence[threading.Thread]:
    return threading.enumerate()

def get_thread_identity(thread: Optional[threading.Thread]):
    if thread is None:
        return "?"
    daemon = '_D'[thread.daemon]
    alive = '_A'[thread.is_alive()]
    status = daemon + alive
    return f'{thread.getName()}#{status}#{thread.ident}'

# python doesnt allow us to park threads, so this is a hack for now
# the use of concurrency primitives will mean that the parking and
# unparking is handled at the kernel level and so is slow.
# otherwise we would def park(blocker: Optional[Thread])

parking_lot = {}

def park_current_thread(timeout: Optional[Nanoseconds] = None):
    timeout_sec = None if timeout is None else timeout.to_seconds()
    ident = threading.get_ident()
    assert not ident in parking_lot
    parking_lot[ident] = threading.Event()
    parking_lot[ident].wait(timeout=timeout_sec)
    parking_lot[ident].clear()
    del parking_lot[ident]  # TODO remove this safety check and the assert above


def unpark(blocker: Optional[threading.Thread]):
    if blocker is None:
        return
    unpark_ident(blocker.ident)

def unpark_ident(ident: Optional[int]):
    if ident is None:
        return
    pl = parking_lot.get(ident)
    if pl is not None:
        pl.set()

def park_current_thread_until_deadline_or(deadline: Nanoseconds, condition: Callable[[],bool]) -> Nanoseconds:
    left = deadline - util.nano_time()
    while left > 0 and not condition():
        park_current_thread(timeout=left)
        left = deadline - util.nano_time()
    return left

def park_current_thread_until_elapsed_or(timeout: Nanoseconds, condition: Callable[[],bool]) -> Nanoseconds:
    deadline = timeout + util.nano_time()
    left = timeout
    while left > 0 and not condition():
        park_current_thread(timeout=left)
        left = deadline - util.nano_time()
    return left

class StackSize:

    def __init__(self, stack_size: int):
        self.stack_size = stack_size
        self.prev_size = None

    def __enter__(self):
        self.prev_size = threading.stack_size()
        if self.stack_size is not None:
            threading.stack_size(self.stack_size)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.prev_size is not None:
            threading.stack_size(self.prev_size)
            self.prev_size = None
