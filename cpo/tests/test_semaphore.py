
import pytest
import threading
import time

from cpo import channel, semaphore

def test_semaphore():
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
