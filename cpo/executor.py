
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import List, Optional

from . import atomic
from . import config
from . import threads
from . import util

class CPOExecutor(ABC):

    def execute(self, runnable: util.Runnable, stack_size: int) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        raise NotImplementedError

class UnpooledExecutor(CPOExecutor):

    def __init__(self) -> None:
        self.thread_count = atomic.AtomicCounter()

    def execute(self, runnable: util.Runnable, stack_size: int) -> None:
        with threads.StackSize(stack_size):
            thread = threading.Thread(
                target=runnable.run,
                name='cpo-unpooled-%d' % self.thread_count.inc(1),
                daemon=True,
            )
        thread.start()

    def shutdown(self) -> None:
        pass

class ThreadPooledExecutor(CPOExecutor):

    def __init__(self, report: bool, pool: ThreadPoolExecutor, stack_size: int = 0) -> None:
        self.report = report
        self.pool = pool
        self.stack_size = stack_size
        self.was_active = False

    def execute(self, runnable: util.Runnable, stack_size: int) -> None:
        with threads.StackSize(stack_size):
            self.pool.submit(runnable.run)
        self.was_active = True

    def shutdown(self) -> None:
        self.pool.shutdown()
        if self.report and self.was_active:
            raise NotImplementedError

class SizePooledExecutor(CPOExecutor):

    def __init__(self, make_pool, report: bool) -> None:
        self.make_pool = make_pool
        self.report = report
        self.SIZES = [1 << x for x in [8, 10, 12, 14, 16]]
        self.N = len(self.SIZES)
        self.pools: List[ThreadPooledExecutor] = [
            make_pool(s) for s in self.SIZES]
        self.other: ThreadPooledExecutor = make_pool(0)

    def execute(self, runnable: util.Runnable, stack_size: int) -> None:
        i = 0
        if stack_size == 0:
            self.other.execute(runnable, 0)
        else:
            while i < self.N and stack_size > self.SIZES[i]:
                i += 1
            if i == self.N:
                self.other.execute(runnable, 0)
            else:
                self.pools[i].execute(runnable, stack_size)

    def shutdown(self) -> None:
        if self.report:
            for pool in self.pools:
                pool.shutdown()
            self.other.shutdown()


poolKIND = config.get('poolKIND', 'ADAPTIVE').upper()
poolMAX = config.get('poolMAX', None)
poolREPORT = config.get('poolREPORT', False)
poolG = config.get('poolG', 0)
poolM = config.get('poolM', 0)
poolK = config.get('poolK', 0)
poolSTACKSIZE = 1024 * (1024 * (1024 * poolG + poolM) + poolK)  # horners method

def size_pooled_cpo_executor(stack_size: int):

    pool = ThreadPoolExecutor(
        max_workers=poolMAX,
        thread_name_prefix='cpo-pool[%d]' % stack_size,
    )
    return ThreadPooledExecutor(poolREPORT, pool, stack_size)

executor: Optional[CPOExecutor] = None
if poolKIND == 'SIZED':
    executor = SizePooledExecutor(
        size_pooled_cpo_executor,
        poolREPORT,
    )
elif poolKIND == 'ADAPTIVE':
    executor = size_pooled_cpo_executor(poolSTACKSIZE)
elif poolKIND == 'CACHED':
    raise NotImplementedError
elif poolKIND == 'UNPOOLED':
    executor = UnpooledExecutor()
else:
    raise ValueError('poolKIND should be SIZED, ADAPTIVE, CACHED or UNPOOLED. '
                     f'Not {poolKIND}')

