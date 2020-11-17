
from cpo import *

def run_demo():
    N_WORKERS = 1000
    N_ITERS = 1000

    unsafe = 0
    safe = AtomicNum(0)

    @procs(range(N_WORKERS))
    def unsafe_workers(i):
        nonlocal unsafe
        for _ in range(N_ITERS):
            unsafe += 1

    @procs(range(N_WORKERS))
    def safe_workers(i):
        for _ in range(N_ITERS):
            safe.inc(1)

    unsafe_workers()
    safe_workers()

    return unsafe, safe


def main():
    unsafe, safe = run_demo()
    print('Unsafe incrementing gave us', unsafe,
          ',safe incrementing gave us', safe)

if __name__ == '__main__':
    main()
