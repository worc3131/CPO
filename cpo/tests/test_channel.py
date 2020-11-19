
import threading
import time

from cpo import *

def test_channel_init():
    OneOne()
    N2N()
    ManyOne()
    OneMany()
    ManyMany()
    OneOneBuf(1)
    N2NBuf()

def test_oneone():
    c = OneOne('oneone_channel')
    @fork_proc
    def write():
        c << 2
    assert ~c == 2

def test_oneone_write_waits():
    c = OneOne('oneone_channel')
    @fork_proc
    def write():
        c << 3
    time.sleep(0.1)
    assert write.is_alive()
    assert ~c == 3
    time.sleep(0.1)
    assert not write.is_alive()

def test_oneone_read_waits():
    c = OneOne('oneone_channel')
    @fork_proc
    def read():
        ~c
    time.sleep(0.1)
    assert read.is_alive()
    c << 3
    time.sleep(0.1)
    assert not read.is_alive()

def test_oneone_multiple():
    c = OneOne('oneone_channel')
    l = [x*(x-20) for x in range(100)]
    @fork_proc
    def write():
        for x in l:
            c << x
    for x in l:
        assert ~c == x

def test_oneone_strings():
    c = OneOne('oneone_channel')
    @fork_proc
    def write():
        c << "hello world"
    assert ~c == "hello world"

def test_manymany():
    c = N2N(5, 5, "", False, False)

    @procs([i*1000 for i in range(5)])
    def writers(i):
        for j in range(500):
            c << i + j
    result = [[] for _ in range(5)]

    @procs([i for i in range(5)])
    @repeat
    def readers(i):
        result[i].append(~c)

    @proc
    def kill():
        time.sleep(1)
        c.close()

    p = readers | writers | kill
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
    c = OneOneBuf(1)
    c << 1
    assert ~c == 1
    @fork_proc
    def write():
        c << 2
        c << 3
    time.sleep(0.5)
    assert write.is_alive()
    assert ~c == 2
    time.sleep(0.5)
    assert not write.is_alive()
    assert ~c == 3
    @fork_proc
    def read():
        assert ~c == 4
        assert ~c == 5
    time.sleep(0.5)
    assert read.is_alive()
    c << 4
    time.sleep(0.5)
    assert read.is_alive()
    c << 5
    time.sleep(0.5)
    assert not read.is_alive()

def test_n2nbuf():
    c = N2NBuf(size=2, writers=3, readers=2)
    num_written = AtomicNum(0)
    @fork_procs(range(3))
    def writers(i):
        c << i
        num_written.inc(1)
    time.sleep(0.5)
    assert num_written.get() == 2
    res = [~c]
    time.sleep(0.5)
    assert num_written.get() == 3
    res += [~c, ~c]
    assert(sorted(res) == [0, 1, 2])
    read = [0]*2
    @fork_procs(range(2))
    def reader(i):
        read[i] = ~c
    time.sleep(0.5)
    assert sorted(read) == [0, 0]
    c << 10
    time.sleep(0.5)
    assert sorted(read) == [0, 10]
    c << 20
    time.sleep(0.5)
    assert sorted(read) == [10, 20]
