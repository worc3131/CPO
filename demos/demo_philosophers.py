
import random
import time

from cpo import *

def run_demo():
    """ Dining philosophers """
    # our philosophers use chopsticks so as to not
    # confuse their forks and their forks
    N = 20
    RUN_FOR = 1.0  # seconds

    chopsticks = [SimpleLock(True, f'chopstick {i}') for i in range(N)]

    kill = False
    times_ate = [0]*N
    @fork_procs(range(N))
    @repeat
    def philosopher(i):
        if kill:
            stop()
        l, r = i, (i+1) % N
        if random.random() < 0.5:
            l, r = r, l
        chopsticks[l].lock()
        chopsticks[r].lock()
        times_ate[i] += 1
        chopsticks[r].unlock()
        chopsticks[l].unlock()

    time.sleep(RUN_FOR)

    kill = True
    for c in chopsticks:
        c.cancel()

    return times_ate

def main():
    print(
        'Here is the spaghetti bill from the philosophers: ',
        run_demo(),
        '. Descarte looks like he is still hungry',
    )

if __name__ == '__main__':
    main()
