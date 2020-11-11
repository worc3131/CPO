
import traceback

from .atomic import AtomicCounter

class Process:

    def __init__(self):
        self.process_count = AtomicCounter

    def gen_name(self):
        return f'Proc-{next(self.process_count)}'

    def handle_exception(self, name, exc, tb):
        print(f"Process {name} terminated by throwing {exc}")
        traceback.print_tb(tb)

