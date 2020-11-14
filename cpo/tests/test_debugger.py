
import sys
import time

from cpo import channel, process, debugger

def test_runs():
    N = 5
    forks = [channel.OneOne() for i in range(N)]
    def deadlocked(i):
        def f():
            forks[(i+1)%N] << ~forks[i]
        return f
    philosophers = [process.Simple(deadlocked(i)) for i in range(N)]
    d = debugger.DEBUGGER()
    def solve():
        time.sleep(2)
        d.show_cso_state(sys.stdout)
        forks[0] << 1
        ~forks[0]
    solver = process.Simple(solve)
    p = process.ParSyntax(philosophers + [solver])
    p()
