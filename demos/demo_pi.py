
import math
import random
import statistics

from cpo import *

def run_demo(num_drops=1e7):
    """ Estimate pi by dropping needles onto a surface """
    NUM_WORKERS = 40
    DROPS_PER_TASK = 10000
    SCALE = 100000

    output = ManyOne()

    def drop_needle() -> bool:
        """ drop a needle and see whether it crosses a line """
        x = random.randrange(SCALE, (4 * SCALE)) / SCALE
        theta = random.randrange(0, 360 * SCALE) / SCALE
        x_end = x + math.sin(math.radians(theta))  # use pi to calculate pi!
        return abs(int(x) - int(x_end)) == 1

    @fork_procs(range(NUM_WORKERS))
    @repeat
    def workers(i):
        hits = sum(drop_needle() for _ in range(DROPS_PER_TASK))
        prob = hits / DROPS_PER_TASK
        estimate = 2 / prob
        output << estimate

    num_outputs = int(num_drops // DROPS_PER_TASK)
    estimates = [~output for _ in range(num_outputs)]

    output.close()

    return statistics.mean(estimates)

def main():
    print(
        'Pi has been calculated as: ',
        run_demo(),
        ' we will have to learn to live with it...'
    )

if __name__ == '__main__':
    main()