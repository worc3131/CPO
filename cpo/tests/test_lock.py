
from cpo import *

def test_lock_init():
    SimpleLock()


def test_simplelock_acq():
    lock = SimpleLock()
    val = 0
    @procs(range(1000))
    def workers(i):
        nonlocal val
        for _ in range(100):
            lock.lock()
            val += 1
            lock.unlock()
    workers()
    DEBUGGER()
    assert val == 1000 * 100

def test_simplelock_with():
    lock = SimpleLock()
    val = 0

    @procs(range(1000))
    def workers(i):
        nonlocal val
        for _ in range(100):
            with lock:
                val += 1

    workers()
    assert val == 1000 * 100

def test_simplelock_withf():
    lock = SimpleLock()
    val = 0
    def f():
        val += 1

    @procs(range(1000))
    def workers(i):
        nonlocal val
        for _ in range(100):
            lock.with_lock(f)
    workers()
    assert val == 1000 * 100

