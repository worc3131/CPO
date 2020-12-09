
import collections
import random
import time
from typing import List

from cpo import *

Message = collections.namedtuple('Message', ['frm', 'to', 'contents'])
Record = collections.namedtuple('Record', ['idx', 'vector', 'actual'])

def run_demo():
    """ A simulation of vector clocks """
    N_WORKERS = 20
    P_MSG = 0.05
    P_EVENT = 0.5
    P_SLEEP = 0.05
    RUN_TIME = 10  # seconds

    mailboxes = [LockFreeQueue() for i in range(N_WORKERS)]
    histories: List[List[Record]] = [[] for _ in range(N_WORKERS)]
    vectors = [[0]*N_WORKERS for _ in range(N_WORKERS)]
    actual = AtomicCounter()
    kill = False

    def update_history(idx):
        rec = Record(idx=idx, vector=vectors[idx], actual=next(actual))
        histories[idx].append(rec)

    @fork_procs(range(N_WORKERS))
    @repeat
    def workers(idx):
        if kill:
            stop()
        # read all our messages
        while mailboxes[idx].length() > 0:
            msg = mailboxes[idx].dequeue()
            assert msg.to == idx
            vectors[idx] = [max(curr, new) for curr, new
                            in zip(vectors[idx], msg.contents)]
        # maybe do an event
        if random.random() < P_EVENT:
            vectors[idx] = vectors[idx].copy()
            vectors[idx][idx] += 1
            update_history(idx)
            # maybe send some messages to communicate our event
            for oth in range(N_WORKERS):
                if oth != idx and random.random() < P_MSG:
                    msg = Message(frm=idx, to=oth, contents=vectors[idx])
                    mailboxes[oth].enqueue(msg)
        # maybe sleep
        if random.random() < P_SLEEP:
            time.sleep(RUN_TIME*0.01)

    time.sleep(RUN_TIME)
    kill = True
    # allow some time for things to die down
    time.sleep(0.1)

    return histories

def run_demo_and_check():
    hist = run_demo()
    flat_hist = [x for h in hist for x in h]
    flat_sorted_hist = sorted(flat_hist, key=lambda x: x.actual)

    for prv, nxt in zip(flat_sorted_hist, flat_sorted_hist[1:]):
        assert prv.vector[nxt.idx] < nxt.vector[nxt.idx]
    assert min(flat_sorted_hist[-1].vector) > 0

def main():
    run_demo_and_check()
    print('Tick-tock all good with the clock')

if __name__ == '__main__':
    main()
