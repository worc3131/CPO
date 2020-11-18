
import time

from cpo import *

def run_demo(Solution):
    N_READERS = 20
    N_WRITERS = 20
    DATA_LEN = 1000
    RUN_TIME = 10  # seconds

    sol = Solution(DATA_LEN)
    sol.spawn_readers(N_READERS)
    sol.spawn_writers(N_WRITERS)
    time.sleep(RUN_TIME)
    sol.kill()
    return sol.get_result()

def main():
    Sols = [
        BadRWSolution,
        ReadFavouredRWSolution,
        WriteFavouredSolution,
        BalancedRWSolution,
    ]
    for Sol in Sols:
        res = run_demo(Sol)
        print(
            Sol.describe(),
            'We got...',
            res
        )

class RWSolution:

    def __init__(self, data_len):
        self.data = [0] * data_len
        self.n_reads = AtomicNum(0)
        self.n_writes = AtomicNum(0)
        self.n_corrupted = AtomicNum(0)
        self._kill = False

    def do_read(self, idx):
        val = self.data[0]
        for i in range(len(self.data)):
            if val != self.data[i]:
                self.n_corrupted.inc(1)
                break
        self.n_reads.inc(1)

    def do_write(self, idx):
        for i in range(len(self.data)):
            self.data[i] = idx
        self.n_writes.inc(1)

    def get_result(self):
        return {
            'writes': self.n_writes.get(),
            'reads': self.n_reads.get(),
            'corrupt reads': self.n_corrupted.get(),
        }

    def spawn_readers(self, num_readers):
        fork_procs(range(num_readers))(self.reader_work)

    def spawn_writers(self, num_writers):
        fork_procs(range(num_writers))(self.writer_work)

    def kill(self):
        self._kill = True

    @repeat
    def reader_work(self, idx):
        if self._kill:
            raise Stopped
        self.before_read(idx)
        self.do_read(idx)
        self.after_read(idx)

    @repeat
    def writer_work(self, idx):
        if self._kill:
            raise Stopped
        self.before_write(idx)
        self.do_write(idx)
        self.after_write(idx)

    @staticmethod
    def describe() -> str:
        raise NotImplementedError

    def before_read(self, idx):
        raise NotImplementedError

    def after_read(self, idx):
        raise NotImplementedError

    def before_write(self, idx):
        raise  NotImplementedError

    def after_write(self, idx):
        raise NotImplementedError

class BadRWSolution(RWSolution):

    def __init__(self, data_len):
        super().__init__(data_len)

    @staticmethod
    def describe() -> str:
        return "With no protection."

    def before_read(self, idx):
        pass

    def after_read(self, idx):
        pass

    def before_write(self, idx):
        pass

    def after_write(self, idx):
        pass


class ReadFavouredRWSolution(RWSolution):

    def __init__(self, data_len):
        super().__init__(data_len)
        self.read_count = 0
        self.read_semaphore = BooleanSemaphore(True)
        self.write_semaphore = BooleanSemaphore(True)

    @staticmethod
    def describe() -> str:
        return "Favouring reads."

    def before_read(self, idx):
        self.read_semaphore.acquire()
        self.read_count += 1
        if self.read_count == 1:
            self.write_semaphore.acquire()
        self.read_semaphore.release()

    def after_read(self, idx):
        self.read_semaphore.acquire()
        self.read_count -= 1
        if self.read_count == 0:
            self.write_semaphore.release()
        self.read_semaphore.release()

    def before_write(self, idx):
        self.write_semaphore.acquire()

    def after_write(self, idx):
        self.write_semaphore.release()


class WriteFavouredSolution(RWSolution):

    def __init__(self, data_len):
        super().__init__(data_len)
        self.read_count = 0
        self.write_count = 0
        self.read_semaphore = BooleanSemaphore(True)
        self.write_semaphore = BooleanSemaphore(True)
        self.read_try_semaphore = BooleanSemaphore(True)
        self.resource_semaphore = BooleanSemaphore(True)

    @staticmethod
    def describe() -> str:
        return "Favouring writes."

    def before_read(self, idx):
        self.read_try_semaphore.acquire()
        self.read_semaphore.acquire()
        self.read_count += 1
        if self.read_count == 1:
            self.resource_semaphore.acquire()
        self.read_semaphore.release()
        self.read_try_semaphore.release()

    def after_read(self, idx):
        self.read_semaphore.acquire()
        self.read_count -= 1
        if self.read_count == 0:
            self.resource_semaphore.release()
        self.read_semaphore.release()

    def before_write(self, idx):
        self.write_semaphore.acquire()
        self.write_count += 1
        if self.write_count == 1:
            self.read_try_semaphore.acquire()
        self.write_semaphore.release()
        self.resource_semaphore.acquire()

    def after_write(self, idx):
        self.resource_semaphore.release()
        self.write_semaphore.acquire()
        self.write_count -= 1
        if self.write_count == 0:
            self.read_try_semaphore.release()
        self.write_semaphore.release()


class BalancedRWSolution(RWSolution):

    def __init__(self, data_len):
        super().__init__(data_len)
        self.read_count = 0
        self.resource_semaphore = BooleanSemaphore(True)
        self.read_semaphore = BooleanSemaphore(True)
        self.queue_semaphore = BooleanSemaphore(True)

    @staticmethod
    def describe() -> str:
        return "With a balance."

    def before_read(self, idx):
        self.queue_semaphore.acquire()
        self.read_semaphore.acquire()
        self.read_count += 1
        if self.read_count == 1:
            self.resource_semaphore.acquire()
        self.queue_semaphore.release()
        self.read_semaphore.release()

    def after_read(self, idx):
        self.read_semaphore.acquire()
        self.read_count -= 1
        if self.read_count == 0:
            self.resource_semaphore.release()
        self.read_semaphore.release()

    def before_write(self, idx):
        self.queue_semaphore.acquire()
        self.resource_semaphore.acquire()
        self.queue_semaphore.release()

    def after_write(self, idx):
        self.resource_semaphore.release()


if __name__ == '__main__':
    main()

