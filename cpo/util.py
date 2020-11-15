
from abc import ABCMeta
import time

import inspect
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
    def to_seconds(self) -> float:
        return self*1e-9

class Milliseconds(int):
    pass

def nano_time():
    return time.time_ns()

class Stopped(Exception):
    pass

class Closed(Stopped):
    def __init__(self, name):
        super().__init__(f'Closed({name})')

def get_prop_else(name, orelse, coerce=None):
    raise NotImplementedError

def get_ultimate_type(fn):
    # for library objects which use a factory find out
    # the actual underlying class, by creating a base instance
    # and getting its type
    while inspect.isfunction(fn) or inspect.isbuiltin(fn):
        fn = fn()
    return type(fn)

_print_lock = threading.Lock()
def synced_print(*args, **kwargs):
    # this would deadlock all threads if it was passed an infinite
    # iterator, generator etc. s.t. print() never returned
    kwargs['flush'] = True
    with _print_lock:
        print(*args, **kwargs)
