
from abc import ABC
from concurrent.futures import ThreadPoolExecutor

from . import process
from . import util

class CPOExecutor(ABC):

    def execute(self, runnable: util.Runnable, stack_size: int) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        raise NotImplementedError

class ThreadPooledExecutor(CPOExecutor):

    def __init__(self, report: bool, pool: ThreadPoolExecutor, stack_size: int = 0) -> None:
        self.report = report
        self.pool = pool
        self.stack_size = stack_size
        self.was_active = False

    def execute(self, runnable: util.Runnable, stack_size: int) -> None:
        self.pool.submit(runnable.run)
        self.was_active = True

    def shutdown(self) -> None:
        self.pool.shutdown()
        if self.report and self.was_active:
            raise NotImplementedError

