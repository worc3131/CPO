
import time

from cpo import *

def run_demo():
    N_READERS = 20
    N_WRITERS = 5
    DATA_LEN = 100
    RUN_TIME = 5  # seconds

    n_reads, n_writes = AtomicNum(0), AtomicNum(0)
    data = [0] * DATA_LEN

    def do_read(idx):
        val = data[0]
        for i in range(DATA_LEN):
            assert val == data[i], "data corrupted"
        n_reads.inc(1)

    def do_write(idx):
        for i in range(DATA_LEN):
            data[i] = idx
        n_writes.inc(1)

    kill = False
    read_count = 0
    resource_semaphore = BooleanSemaphore(True)
    read_semaphore = BooleanSemaphore(True)
    queue_semaphore = BooleanSemaphore(True)

    @fork_procs(range(N_READERS))
    @repeat
    def readers(idx):
        nonlocal read_count
        if kill:
            stop()
        queue_semaphore.acquire()
        read_semaphore.acquire()
        read_count += 1
        if read_count == 1:
            resource_semaphore.acquire()
        queue_semaphore.release()
        read_semaphore.release()

        do_read(idx)

        read_semaphore.acquire()
        read_count -= 1
        if read_count == 0:
            resource_semaphore.release()
        read_semaphore.release()

    @fork_procs(range(N_WRITERS))
    @repeat
    def writers(idx):
        if kill:
            stop()
        queue_semaphore.acquire()
        resource_semaphore.acquire()
        queue_semaphore.release()

        do_write(idx)

        resource_semaphore.release()

    time.sleep(RUN_TIME)
    kill = True

    return n_reads.get(), n_writes.get()

def main():
    nr, nw = run_demo()
    print(f'We managed {nr} reads and {nw} writes')

if __name__ == '__main__':
    main()
