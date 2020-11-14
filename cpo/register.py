
from __future__ import annotations

import collections
import threading
from typing import Dict, List, Optional, Sequence
import weakref

from .atomic import AtomicCounter
from . import conc
from . import util

class StateKey(int):
    pass

stateKey = AtomicCounter()

NONEWAITING: List[threading.Thread] = []

registered: Dict[int, weakref.ReferenceType[Debuggable]] = {}

def register(obj: Debuggable) -> StateKey:
    key = next(stateKey)
    registered[key] = weakref.ref(obj)
    return key

class Debuggable:

    def __init__(self):
        self._key: StateKey = -1

    def register(self):
        if self._key < 0:
            self._key = register(self)

    def unregister(self):
        if self._key > 0:
            del registered[self._key]
            self._key = -1

    def show_state(self, file):
        raise NotImplementedError

    def get_waiting(self) -> List[threading.Thread]:
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
    result = collections.defaultdict(list)
    for _, ref in registered.items():
        obj: Optional[Debuggable] = ref()
        if obj is not None:
            for thread in obj.get_waiting():
                if thread is not None:
                    result[thread].append(obj)
    return result

def show_threads(file, caption: str, threads: Sequence[threading.Thread]):
    if len(threads) > 0:
        c = ""
        util.synced_print(caption, file=file, end='')
        for thread in threads:
            util.synced_print(
                f'{c} {conc.get_thread_identity(thread)}',
                file=file, end='')
            c = ","
