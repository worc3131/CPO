
import time

from cpo import *

def test_barrier_init():
    Barrier(3)
    CombiningBarrier(3, 0, lambda x, y: x+y)
    OrBarrier(3)
    AndBarrier(3)

def test_barrier():
    b = Barrier(3)
    id_ = AtomicCounter(0)
    before, after = AtomicNum(0), AtomicNum(0)

    def launch(n):
        @fork_procs([next(id_) for _ in range(n)])
        def workers(i):
            before.inc(1)
            b.sync()
            after.inc(1)
        time.sleep(0.2)
        return workers

    def get():
        return before.get(), after.get()

    launch(2)
    assert get() == (2, 0)
    launch(2)
    assert get() == (4, 3)
    launch(2)
    assert get() == (6, 6)

def test_combining_barrier():
    b = CombiningBarrier(3, 0, lambda x, y: x+y)
    id_ = AtomicCounter(0)
    before, val, after = AtomicNum(0), Atomic(-1), AtomicNum(0)

    def launch(n):
        @fork_procs([next(id_) for _ in range(n)])
        def workers(i):
            before.inc(1)
            val.set(b.sync(i))
            after.inc(1)
        time.sleep(0.2)
        return workers

    def get():
        return before.get(), after.get(), val.get()

    launch(2)
    assert get() == (2, 0, -1)
    launch(1)
    assert get() == (4, 3, 1+2+3)
    launch(3)
    assert get() == (6, 6, 4+5+6)
