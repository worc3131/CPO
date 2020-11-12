
from abc import ABCMeta
import traceback

from .atomic import AtomicCounter
from . import conc
from . import util

Latch = conc.CountDownLatch

class PROC(metaclass=ABCMeta):
    def apply(self) -> None:


class Process:

    def __init__(self):
        self.process_count = AtomicCounter
        self.stopped = util.Stopped()

    def gen_name(self):
        return f'Proc-{next(self.process_count)}'

    def handle_exception(self, name, exc, tb):
        util.synced_print(f"Process {name} terminated by throwing {exc}")
        traceback.print_tb(tb)

class Simple:

    def __init__(self, body):
        pass



