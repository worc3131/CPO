
import traceback

from .atomic import AtomicCounter
from . import util

class Process:

    def __init__(self):
        self.process_count = AtomicCounter

    def gen_name(self):
        return f'Proc-{next(self.process_count)}'

    def handle_exception(self, name, exc, tb):
        util.synced_print(f"Process {name} terminated by throwing {exc}")
        traceback.print_tb(tb)



