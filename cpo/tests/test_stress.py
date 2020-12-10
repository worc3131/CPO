
from cpo import *

def test_stress_proc():
    N = 100
    channels = [OneOne(name=i) for i in range(N)]
    @procs(range(N))
    def workers(i):
        if i > 0:
            msg = ~channels[i-1]
        else:
            msg = 'hello'
        if i < N-1:
            channels[i] << msg
    workers()

def test_stress_lock():
    lock = SimpleLock()
    @procs(range(2000))
    def workers(i):
        for _ in range(100):
            with lock:
                pass
    workers()

def test_stress_channel():
    c = ManyMany()
    @procs(range(1000))
    def readers(i):
        for _ in range(100):
            ~c
    @procs(range(1000))
    def writers(i):
        for x in range(100):
            c << (i, x)
    p = readers | writers
    p()

def test_stress_queue():
    q = LockFreeQueue()
    @procs(range(1000))
    def readers(i):
        for _ in range(1000):
            q.dequeue()
    @procs(range(1000))
    def writers(i):
        for x in range(1000):
            q.enqueue((i, x))
    p = readers | writers
    p()

