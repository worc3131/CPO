
import pytest
import time

from cpo import *

def test_flag_init():
    Flag()

def test_flag():
    f = Flag()
    done = False
    @fork_proc
    def p():
        nonlocal done
        f.acquire()
        done = True
    time.sleep(0.1)
    assert not done
    f.release()
    time.sleep(0.1)
    assert done

def test_flag_acquire_once():
    f = Flag()
    @fork_proc
    def worker():
        f.acquire()
    with pytest.raises(Exception):
        f.acquire()
    with pytest.raises(Exception):
        f.try_acquire(Nanoseconds.from_seconds(1))
    f.release()

def test_flag_release_once():
    f = Flag()
    f.release()
    with pytest.raises(Exception):
        f.release()

def test_flag_stays_released():
    f = Flag()
    f.release()
    f.acquire()
    f.acquire()
    f.acquire()
    @procs(range(5))
    def workers(i):
        f.acquire()
    workers()

def test_flag_try_acquire():
    f = Flag()
    assert not f.try_acquire(Nanoseconds.from_seconds(0.01))
    assert not f.try_acquire(Nanoseconds.from_seconds(0.01))
    @fork_proc
    def p():
        time.sleep(0.2)
        f.release()
    assert not f.try_acquire(Nanoseconds.from_seconds(0.15))
    assert f.try_acquire(Nanoseconds.from_seconds(0.15))
    assert f.try_acquire(Nanoseconds.from_seconds(0.15))
    f.acquire()
