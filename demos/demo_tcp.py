
from cpo import *

class Packet:
    pass

class SYN(Packet):
    pass

class SYNACK(Packet):
    pass

def run_demo():
    RUNS = 1000
    TIMEOUT = Nanoseconds.from_seconds(0.01)
    PROB_LOSS = 0.8

    DEBUGGER()

    num_timeouts = 0
    for _ in range(RUNS):
        cl_to_sv = FaultyOneOne(prob_loss=PROB_LOSS)
        sv_to_cl = FaultyOneOne(prob_loss=PROB_LOSS)
        # dont return whether the send was successful we have to figure
        # that out ourselves through ACKs etc.
        send_sv = lambda v: sv_to_cl.write_before(TIMEOUT, v) or True
        send_cl = lambda v: cl_to_sv.write_before(TIMEOUT, v) or True
        recv_sv = lambda  : cl_to_sv.read_before(TIMEOUT)
        recv_cl = lambda  : sv_to_cl.read_before(TIMEOUT)

        @proc
        def client():
            nonlocal num_timeouts
            send_cl(SYN())
            p = None
            while p is None:
                p = recv_cl()
                num_timeouts += p is None
            assert isinstance(p, SYNACK)
        @proc
        def server():
            nonlocal num_timeouts
            p = None
            while p is None:
                p = recv_sv()
                num_timeouts += p is None
            assert isinstance(p, SYN)
            send_sv(SYNACK())
        (client | server)()

    return RUNS, num_timeouts

def main():
    num_runs, num_timeouts = run_demo()
    timeouts_per_run = num_timeouts / num_runs
    print(f'Established {num_runs} TCP handshakes with '
          f'{timeouts_per_run} timeouts per run')

if __name__ == '__main__':
    main()
