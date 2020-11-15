
from cpo import *

def test_init():
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

def test_process():
    v = 0
    @proc
    def pass_():
        nonlocal v
        v = 1
    pass_()
    assert v == 1

def test_process2():
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
    c1 = OneOne()
    c2 = OneOne()
    @proc
    def write():
        for x in range(500):
            c1 << x
        c1.close()
    @proc
    @repeat(guard=lambda: c2.close())
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
