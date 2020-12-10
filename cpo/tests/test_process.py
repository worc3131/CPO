
from cpo import *

def test_process__init():
    c = OneOne()
    def work():
        pass
    p = Simple(work)
    IterToChannel([], c)
    Par("", [p])
    ParSyntax([p])
    @proc
    def work():
        pass
    @procs([1, 2, 3])
    def work(i):
        pass

def test_iter_to_channel():
    c = OneOne()
    vals = [1, 42, 123]
    @proc
    def read():
        for v in vals:
            assert ~c == v
    pw = IterToChannel(vals, c)
    p = pw | read
    p()

def test_process_wo_channel():
    v = 0
    @proc
    def pass_():
        nonlocal v
        v = 1
    pass_()
    assert v == 1

def test_process_with_channel():
    c = OneOne()
    result = 0
    @proc
    def read():
        nonlocal result
        result += ~c
        result += ~c
    @proc
    def write():
        c << 123
        c << 111
    p = read | write
    p()
    assert result == 234

def test_close_channel():
    c1 = OneOne('write_to_square')
    c2 = OneOne('square_to_read')
    @proc
    def write():
        for x in range(500):
            c1 << x
        c1.close()
    @proc
    @repeat(finally_=lambda: c2.close())
    def square():
        c2 << (~c1)**2
    result = 0
    @proc
    @repeat
    def read():
        nonlocal result
        result += ~c2
    p = write | square | read
    p()
    assert result == sum(x*x for x in range(500))

def test_ordered_procs():
    N = 100000
    order = []
    @ordered_procs(range(N))
    def workers(i):
        order.append(i)
    workers()
    assert order == list(range(N))

def test_unordered_procs():
    # this could fail by chance
    N = 100000
    order = []
    @procs(range(N))
    def workers(i):
        order.append(i)
    workers()
    assert order != list(range(N))

def test_ordered_concurrent_procs():
    N = 1000
    order = []
    @procs(range(N))
    def workers_1(i):
        order.append(i)
    @procs(range(N))
    def workers_2(i):
        order.append(i+N)
    p = workers_1 >> workers_2
    p()
    assert sorted(order[:N]) == list(range(0,   N))
    assert sorted(order[N:]) == list(range(N, 2*N))

def test_repeated_procs():
    N = 1000
    M = 100
    order = []
    @procs(range(N))
    def workers(i):
        order.append(i)
    n_runs = 0
    @proc
    def checker():
        nonlocal order, n_runs
        assert sorted(order) == list(range(N))
        order = []
        n_runs += 1
    p = workers >> checker
    for _ in range(M):
        p()
    assert n_runs == M
