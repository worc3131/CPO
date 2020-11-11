
from __future__ import annotations

import threading
from typing import Dict, List, Sequence
import weakref

from .atomic import AtomicCounter
from . import conc

class StateKey(int):
    pass

stateKey = AtomicCounter()

NONEWAITING: List[threading.Thread] = []

registered = {}

def register(obj: Debuggable) -> StateKey:
    key = next(stateKey)
    registered[key] = weakref.ref(obj)
    return key

class Debuggable:

    def __new__(cls, self):
        instance = super().__new__(cls)
        instance._key: StateKey = -1
        return instance

    def register(self):
        if self._key < 0:
            self._key = register(self)

    def unregister(self):
        if self._key > 0:
            del registered[self._key]
            self._key = -1

    def show_state(self):
        raise NotImplementedError

    def get_waiting(self) -> Sequence[threading.Thread]:
        return NONEWAITING.copy()

    def with_debugger(self, condition, func):
        if condition:
            self.register()
            try:
                func()
            finally:
                self.unregister()
        else:
            func()

    @property
    def has_state(self):
        return True

def waiting() -> Dict[threading.Thread, List[Debuggable]]:
    raise NotImplemented

def show_threads(caption: str, threads: Sequence[threading.Thread]):
    if len(threads)>0:
        c = ""
        print(caption, end='')
        for thread in threads:
            print(f'{c} {conc.get_thread_identity(thread)}', end='')
            c = ","
