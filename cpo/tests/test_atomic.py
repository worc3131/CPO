
from cpo import *

def test_atomic_init():
    Atomic("hello")
    AtomicNum(0)
    AtomicCounter(2)

def test_atomic():
    c = Atomic("a")
    assert c.get_and_set("b") == "a"
    assert c.get() == "b"
    c.set("c")
    assert c.get() == "c"
    assert c.get_and_update(lambda x: 2*x) == "c"
    assert c.get() == "cc"
    assert not c.compare_and_set("dd", "ee")
    assert c.compare_and_set("cc", "ee")
    assert c.get() == "ee"

def test_atomic_num():
    c = AtomicNum(0)
    @procs(range(1000))
    def workers(i):
        for _ in range(1000):
            c.inc(3)
            c.dec(1)
    workers()
    assert c.get() == 2 * 1000 * 1000

def test_atomic_counter():
    c = AtomicCounter(0)
    @procs(range(1000))
    def workers(i):
        for _ in range(1000):
            next(c)
    workers()
    assert c.get() == 1000*1000


