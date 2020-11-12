
import pytest

from cpo import channel, process

def test_process():
    v = 0
    def pass_():
        nonlocal v
        v = 1
    p = process.Simple(pass_)
    p()
    assert v == 1

def test_process2():
    c = channel.OneOne()
    result = 0
    def read():
        nonlocal result
        result += ~c
    def write():
        c << 123
    p1 = process.Simple(read)
    p2 = process.Simple(write)
    p = p1 | p2
    p()
    assert result == 123
