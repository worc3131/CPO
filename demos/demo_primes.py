
import itertools

from cpo import *

def run_demo(num_primes=30):
    """ Calculate primes by recursive filtering """

    input = OneOne()
    output = ManyOne()

    @fork_proc
    def source():
        for n in itertools.count(start=2):
            input << n

    def worker(port_in, port_out):
        prime = ~port_in
        port_out << prime
        c = OneOne()
        fork_proc(lambda: worker(c, port_out))
        try:
            while True:
                val = ~port_in
                if val % prime != 0:
                    c << val
        finally:
            c.close()
    fork_proc(lambda: worker(input, output))

    result = [~output for _ in range(num_primes)]

    input.close()
    output.close()
    return result

def main():
    print('We have found the following primes: ', run_demo())

if __name__ == '__main__':
    main()
