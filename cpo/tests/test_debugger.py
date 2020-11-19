
import time

from cpo import *

def test_debugger_init():
    d = DEBUGGER()
    d.show_cso_state()

def test_debugger_runs():
    N = 5
    chan = N2N(N, N)
    forks = [OneOne() for i in range(N)]
    def deadlocked(i):
        def f():
            forks[(i+1)%N] << ~forks[i]
            chan << ~chan
        return f
    philosophers = [Simple(deadlocked(i)) for i in range(N)]
    d = DEBUGGER()
    def hello():
        return 'hello from test_debugger'
    d.monitor('test', hello)
    def solve():
        time.sleep(1)
        d.show_cso_state()
        forks[0] << -1
        ~forks[0]
        chan << -1
        ~chan
    solver = Simple(solve)
    p = ParSyntax(philosophers + [solver])
    p()
