
import collections
import time

from cpo import *

def test_semaphore_init():
    BooleanSemaphore()
    CountingSemaphore()

def test_bool_semaphore():
    s = BooleanSemaphore(available=True)
    s.acquire()
    c = N2NBuf(10, 10, 10)
    def worker(i):
        s.acquire()
        c << i
        s.release()
    for i in range(5):
        fork_proc(worker, i)
        time.sleep(0.2)
    assert c.is_empty()
    s.release()
    for i in range(5):
        assert ~c == i
    assert c.is_empty()

def test_bool_semaphore_try_acquire():
    s = BooleanSemaphore(available=False)
    assert not s.try_acquire(Nanoseconds.from_seconds(0.1))
    s = BooleanSemaphore(available=True)
    assert s.try_acquire(Nanoseconds.from_seconds(0.1))

def test_bool_semaphore_max():
    sem = BooleanSemaphore(available=True)
    vl = AtomicNum(0)
    @fork_procs(range(100))
    def worker(i):
        for _ in range(10000):
            with sem:
                vl.inc(1)
                assert vl.get() == 1
                vl.dec(1)
    time.sleep(0.5)

def test_count_semaphore_max():
    sem = CountingSemaphore(5)
    vl = AtomicNum(0)
    res = []
    @procs(range(100))
    def workers(i):
        for _ in range(50):
            with sem:
                vl.inc(1)
                v = vl.get()
                time.sleep(0.001)
                assert v <= 5
                res.append(v)
                vl.dec(1)
    workers()
    assert len(set(res)) == 5
