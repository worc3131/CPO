
import threading
import time

import pytest

from cpo import channel, debugger, process, util

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
    c = channel._N2N(5, 5, "", False, False)

    def write(i):
        def f():
            for j in range(500):
                c << i + j
        return f
    result = [[] for _ in range(5)]

    def read(i):
        def f():
            try:
                while True:
                    result[i].append(~c)
            except util.Closed:
                pass
        return f

    def kill():
        time.sleep(1)
        c.close()

    p = process.ParSyntax([process.Simple(kill)])
    p = p | process.ParSyntax([process.Simple(write(i*1000)) for i in range(5)])
    p = p | process.ParSyntax([process.Simple(read(i))       for i in range(5)])
    p()
    # the below tests could fail as a result of random chance
    # none lost
    flat = [y for x in result for y in x]
    assert len(flat) == 2500
    assert len(set(flat)) == 2500
    # none starved
    assert not any(len(x) == 0 for x in result)
    # not all equal length
    assert not all(len(x) == 500 for x in result)
    # not a sorted output
    assert not any(x == sorted(x) for x in result)
    # not just from one inputter
    assert not any(len({y//1000 for y in x}) == 1 for x in result)

def test_oneonebuf():
    c = channel.OneOneBuf(1)
    c << 1
    assert ~c == 1
    write_done = False
    def write():
        nonlocal write_done
        c << 2
        c << 3
        write_done = True
    t = threading.Thread(target=write)
    t.start()
    time.sleep(0.5)
    assert not write_done
    assert ~c == 2
    time.sleep(0.5)
    assert write_done
    assert ~c == 3
    read_done = False
    def read():
        nonlocal read_done
        assert ~c == 4
        assert ~c == 5
        read_done = True
    t = threading.Thread(target=read)
    t.start()
    time.sleep(0.5)
    assert not read_done
    c << 4
    time.sleep(0.5)
    assert not read_done
    c << 5
    time.sleep(0.5)
    assert read_done

