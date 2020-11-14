
import collections
import pytest
import threading
import time

from cpo import atomic, channel, semaphore

def test_bool_semaphore():
    s = semaphore.BooleanSemaphore(available=True)
    c = channel.N2NBuf(10, 10, 10)
    def worker(i):
        s.acquire()
        c << i
        s.release()
    s.acquire()
    for i in range(5):
        threading.Thread(target=worker, args=(i,)).start()
        time.sleep(0.2)
    assert c.is_empty()
    s.release()
    for i in range(5):
        assert ~c == i
    assert c.is_empty()

def test_bool_semaphore_max():
    sem = semaphore.BooleanSemaphore(available=True)
    vl = atomic.AtomicNum(0)
    def worker():
        for _ in range(10000):
            with sem:
                vl.inc(1)
                assert vl.get() == 1
                vl.dec(1)
    for _ in range(100):
        threading.Thread(target=worker).start()

def test_count_semaphore_max():
    sem = semaphore.CountingSemaphore(5)
    vl = atomic.AtomicNum(0)
    res = []
    def worker():
        for _ in range(50):
            with sem:
                vl.inc(1)
                v = vl.get()
                time.sleep(0.001)
                assert v <= 5
                res.append(v)
                vl.dec(1)
    for _ in range(100):
        threading.Thread(target=worker).start()
    time.sleep(0.2)
    print(collections.Counter(res))
    assert len(set(res)) == 5
