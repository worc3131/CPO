
import time

from cpo import channel, process, debugger

def test_runs():
    N = 5
    chan = channel.N2N(N, N)
    forks = [channel.OneOne() for i in range(N)]
    def deadlocked(i):
        def f():
            forks[(i+1)%N] << ~forks[i]
            chan << ~chan
        return f
    philosophers = [process.Simple(deadlocked(i)) for i in range(N)]
    d = debugger.DEBUGGER()
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
    solver = process.Simple(solve)
    p = process.ParSyntax(philosophers + [solver])
    p()
