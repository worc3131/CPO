
import threading
import time

import pytest

from cpo import channel, process

@pytest.fixture
def oneone():
    return channel.OneOne('oneone_channel')

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

def test_oneone_multiple(oneone):
    c = oneone
    l = [x*(x-20) for x in range(100)]
    def write():
        for x in l:
            c << x
    threading.Thread(target=write).start()
    for x in l:
        assert ~c == x

def test_oneone_strings(oneone):
    c = oneone
    def write():
        c << "hello world"
    threading.Thread(target=write).start()
    assert ~c == "hello world"

def test_manymany():
    return  # TODO
    c = channel._N2N(5, 5, "", False, False)

    def write(i):
        def f():
            for j in range(500):
                c << i + j
        return f
    result = [[] for _ in range(5)]

    def read(i):
        def f():
            while True:
                result[i].append(~c)
        return f

    def kill():
        time.sleep(3)
        c.close()

    p = process.ParSyntax([process.Simple(kill)])
    p = p | process.ParSyntax([process.Simple(write(i*1000)) for i in range(5)])
    p = p | process.ParSyntax([process.Simple(read(i))       for i in range(5)])
    p()
    import pdb; pdb.set_trace()  # TODO - add asserts


