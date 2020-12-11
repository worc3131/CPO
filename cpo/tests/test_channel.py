
import pytest
import time

from cpo import *
from cpo.channel import CLOSEDSTATE, _N2NBuf

ALL_CHANNELS = [
    OneOne,
    N2N,
    ManyOne,
    OneMany,
    ManyMany,
    OneOneBuf,
    N2NBuf,
]

def test_channel_init():
    for Channel in ALL_CHANNELS:
        Channel()

def test_channel_str():
    for Channel in ALL_CHANNELS:
        c = Channel()
        assert isinstance(str(c), str)
        assert isinstance(repr(c), str)

def test_channel_close():
    for Channel in ALL_CHANNELS:
        c = Channel()
        assert c.can_input
        assert c.can_output
        c.close()
        assert not c.can_input
        assert not c.can_output
        assert c.in_port_state is CLOSEDSTATE
        assert c.out_port_state is CLOSEDSTATE

def test_channel_timeout():
    for Channel in ALL_CHANNELS:
        c = Channel()
        assert c.read_before(Nanoseconds.from_seconds(0.01)) is None
        expected = isinstance(c, _N2NBuf)
        assert c.write_before(Nanoseconds.from_seconds(0.01), 0) == expected
        c.close()
        # read / write should not attempt because channel is closed
        with pytest.raises(util.Closed):
            c.read_before(Nanoseconds.from_seconds(1))
        with pytest.raises(util.Closed):
            c.write_before(Nanoseconds.from_seconds(1), 0)

def test_oneone():
    c = OneOne()
    @fork_proc
    def write():
        c << 2
    assert ~c == 2

def test_oneone_write_waits():
    c = OneOne()
    @fork_proc
    def write():
        c << 3
    time.sleep(0.1)
    assert write.is_alive()
    assert ~c == 3
    time.sleep(0.1)
    assert not write.is_alive()

def test_oneone_read_waits():
    c = OneOne()
    @fork_proc
    def read():
        ~c
    time.sleep(0.1)
    assert read.is_alive()
    c << 3
    time.sleep(0.1)
    assert not read.is_alive()

def test_oneone_multiple():
    c = OneOne()
    l = [x*(x-20) for x in range(100)]
    @fork_proc
    def write():
        for x in l:
            c << x
    for x in l:
        assert ~c == x

def test_oneone_strings():
    c = OneOne()
    @fork_proc
    def write():
        c << "hello world"
    assert ~c == "hello world"

def test_oneone_close():
    c = OneOne()
    c.close()
    with pytest.raises(Closed):
        ~c

def test_oneone_extended_rendezvous1():
    c = OneOne()
    @fork_proc
    def write_5():
        c << 5
    assert ~c(lambda x: 2*x) == 10

def test_oneone_extended_rendezvous2():
    c = OneOne()
    @fork_proc
    def write_7():
        c << 7
    @c
    def er(x):
        return 3*x
    assert ~er == 21

def test_oneone_extended_rendezvous3():
    c = OneOne()
    x = 0
    @proc
    def counter():
        nonlocal x
        for _ in range(100):
            c << x
            x += 1
        c.close()
    @proc
    @repeat
    def checker():
        nonlocal x
        assert ~c(lambda v: v == x)
    (counter | checker)()
    assert x == 100

def test_oneone_read_before():
    c = OneOne()
    assert c.read_before(Nanoseconds(1)) is None
    fork_proc(lambda: c << 2)
    assert c.read_before(Nanoseconds.from_seconds(1)) == 2
    @fork_proc
    def p():
        time.sleep(0.2)
        c << 5
    assert c.read_before(Nanoseconds.from_seconds(0.15)) is None
    assert c.read_before(Nanoseconds.from_seconds(0.15)) == 5

def test_oneone_write_before():
    c = OneOne()
    assert not c.write_before(Nanoseconds(1), 0)
    @fork_proc
    def p():
        assert ~c == 1
    assert c.write_before(Nanoseconds.from_seconds(0.1), 1)
    assert not c.write_before(Nanoseconds.from_seconds(0.1), 2)
    @fork_proc
    def p():
        time.sleep(0.2)
        assert ~c == 4
    assert not c.write_before(Nanoseconds.from_seconds(0.15), 3)
    assert c.write_before(Nanoseconds.from_seconds(0.15), 4)

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
    time.sleep(0.2)
    assert write.is_alive()
    assert ~c == 2
    time.sleep(0.2)
    assert not write.is_alive()
    assert ~c == 3
    @fork_proc
    def read():
        assert ~c == 4
        assert ~c == 5
    time.sleep(0.2)
    assert read.is_alive()
    c << 4
    time.sleep(0.2)
    assert read.is_alive()
    c << 5
    time.sleep(0.2)
    assert not read.is_alive()

def test_n2nbuf():
    c = N2NBuf(size=2, writers=3, readers=2)
    num_written = AtomicNum(0)
    @fork_procs(range(3))
    def writers(i):
        c << i
        num_written.inc(1)
    time.sleep(0.2)
    assert num_written.get() == 2
    res = [~c]
    time.sleep(0.2)
    assert num_written.get() == 3
    res += [~c, ~c]
    assert(sorted(res) == [0, 1, 2])
    read = [0]*2
    @fork_procs(range(2))
    def reader(i):
        read[i] = ~c
    time.sleep(0.2)
    assert sorted(read) == [0, 0]
    c << 10
    time.sleep(0.2)
    assert sorted(read) == [0, 10]
    c << 20
    time.sleep(0.2)
    assert sorted(read) == [10, 20]

def test_faultyoneone():
    c = FaultyOneOne(prob_loss=1-0.36)
    N = 100000
    total = 0
    @proc
    @repeat
    def reader():
        nonlocal total
        total += ~c
    @proc
    def writer():
        for i in range(N):
            if i % 2:  # alternate between the two methods
                c << 1
            else:
                c.write_before(Nanoseconds.from_seconds(0.0001), 1)
        c.close()
    (reader | writer)()
    # could fail probabilistically (unlikely ~6 std)
    assert 0.35*N < total < 0.37*N
