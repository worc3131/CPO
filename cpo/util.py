
from abc import ABCMeta

import threading
from typing import Dict, Optional


class Runnable(metaclass=ABCMeta):
    def run(self) -> None:
        raise NotImplemented


class Singleton(type):
    _instances: Dict[type, type] = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Nanoseconds(int):
    pass

class Milliseconds(int):
    pass

class Stopped(Exception):
    pass

class Closed(Stopped):
    def __init__(self, name):
        super().__init__(f'Closed({name})')

def get_prop_else(name, orelse, coerce=None):
    raise NotImplementedError

_print_lock = threading.Lock()
def synced_print(*args, **kwargs):
    # this would deadlock all threads if it was passed an infinite
    # iterator, generator etc. s.t. print() never returned
    kwargs['flush'] = True
    with _print_lock:
        print(*args, **kwargs)
