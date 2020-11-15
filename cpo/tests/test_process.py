
from cpo import *

def test_process():
    v = 0
    def pass_():
        nonlocal v
        v = 1
    p = Simple(pass_)
    p()
    assert v == 1

def test_process2():
    c = OneOne()
    result = 0
    def read():
        nonlocal result
        result += ~c
        result += ~c
    def write():
        c << 123
        c << 111
    p1 = Simple(read)
    p2 = Simple(write)
    p = p1 | p2
    p()
    assert result == 234

def test_close_channel():
    c1 = OneOne()
    c2 = OneOne()
    def write():
        for x in range(500):
            c1 << x
        c1.close()
    def square():
        try:
            while True:
                c2 << (~c1)**2
        except util.Closed:
            c2.close()
    result = 0
    def read():
        nonlocal result
        try:
            while True:
                result += ~c2
        except Closed:
            pass
    p1 = Simple(write)
    p2 = Simple(square)
    p3 = Simple(read)
    p = p1 | p2 | p3
    p()
    assert result == sum(x*x for x in range(500))
