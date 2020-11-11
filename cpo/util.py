
import threading
from typing import Dict, Optional

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
