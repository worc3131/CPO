
import threading
import time

import pytest

import cpo.channel

@pytest.fixture
def oneone():
    return cpo.channel.OneOne('oneone_channel')

def test_oneone(oneone):
    c = oneone
    def write():
        c << 2
    threading.Thread(target=write).start()
    assert ~c == 2

def test_oneone_write_waits(oneone):
    c = oneone
    def write():
        c << 3
    t = threading.Thread(target=write)
    t.start()
    time.sleep(0.1)
    assert t.is_alive()
    assert ~c == 3
    time.sleep(0.1)
    assert not t.is_alive()

def test_oneone_read_waits(oneone):
    c = oneone
    def read():
        ~c
    t = threading.Thread(target=read)
    t.start()
    time.sleep(0.1)
    assert t.is_alive()
    c << 3
    time.sleep(0.1)
    assert not t.is_alive()


