
from __future__ import annotations

import threading
from typing import Generic, Optional, TypeVar

from .atomic import Atomic, AtomicNum
from . import conc
from .name import Named, NameGenerator
from .register import Debuggable
from . import util
from .util import Nanoseconds, Singleton, synced_print

class PortState(metaclass=Singleton):
    def __str__(self) -> str:
        raise NotImplementedError
    def to_state_string(self) -> str:
        raise NotImplementedError

class _CLOSEDSTATE(PortState):
    def __str__(self):
        return "CLS"
    def to_state_string(self) -> str:
        return "CLS: "
CLOSEDSTATE = _CLOSEDSTATE()

class _UNKNOWNSTATE(PortState):
    def __str__(self):
        return "UNK"
    def to_state_string(self) -> str:
        return ""
UNKNOWNSTATE = _UNKNOWNSTATE()

class _READYSTATE(PortState):
    def __str__(self):
        return "RDY"
    def to_state_string(self) -> str:
        return "RDY: "
READYSTATE = _READYSTATE()

TI = TypeVar('TI')
class InPort(Generic[TI]):

    def __invert__(self) -> TI:
        raise NotImplementedError

    def read_before(self, ns: Nanoseconds) -> Optional[TI]:
        raise NotImplementedError

    def __call__(self, func) -> InPortFunc[TI]:
        return InPortFunc(self, func)

    def extended_rendezvous(self, func):
        raise NotImplementedError

    def close_in(self):
        raise NotImplementedError

    def can_input(self) -> bool:
        raise NotImplementedError

    @property
    def nothing(self) -> Optional[TI]:
        return None

    def name(self) -> str:
        raise NotImplementedError

    def in_port_state(self) -> PortState:
        raise NotImplementedError


class InPortFunc(Generic[TI]):

    def __init__(self, port: InPort, func):
        self.port = port
        self.func = func

    def __invert__(self):
        self.port.extended_rendezvous(self.func)

TO = TypeVar('TO')
class OutPort(Generic[TO]):

    def __lshift__(self, val: TO) -> None:
        raise NotImplementedError

    def write_before(self, nswait: Nanoseconds, value: TO) -> bool:
        raise NotImplementedError

    def close_out(self) -> None:
        raise NotImplementedError

    def can_output(self) -> bool:
        raise NotImplementedError

    def name(self) -> str:
        raise NotImplementedError

    def out_port_state(self) -> PortState:
        raise NotImplementedError

T = TypeVar('T')
class Chan(InPort[T], OutPort[T], Named, Debuggable):

    def close(self) -> None:
        raise NotImplementedError

    def out_port_event(self, port_state: PortState) -> None:
        pass

    def in_port_event(self, port_state: PortState) -> None:
        pass

class SyncChan(Chan[T]):
    pass

class _OneOne(SyncChan[T]):

    def __init__(self, name):
        self.set_name(name)
        self.reader: Atomic[Optional[threading.Thread]] = Atomic(None)
        self.writer: Atomic[Optional[threading.Thread]] = Atomic(None)
        self.closed, self.full = Atomic(False), Atomic(False)
        self.buffer = None
        self.reads = AtomicNum(0)
        self.writes = AtomicNum(0)
        self.register()

    def finished_read(self) -> int:
        return self.reads.inc(1)

    def finished_write(self) -> int:
        return self.writes.inc(1)

    def finished_rw(self) -> str:
        return f'(READ {self.reads}, WRITTEN {self.writes})'

    @property
    def in_port_state(self):
        if self.closed.get():
            return CLOSEDSTATE
        if self.full.get():
            return READYSTATE
        return UNKNOWNSTATE

    @property
    def out_port_state(self):
        if self.closed.get():
            return CLOSEDSTATE
        if self.reader.get() is not None and not self.full.get():
            return READYSTATE
        return UNKNOWNSTATE

    @property
    def name_generator(self) -> NameGenerator:
        return OneOne

    def current_state(self) -> str:
        wr = self.reader.get()
        ww = self.writer.get()
        if ww is None and wr is None:
            result = "idle"
        else:
            if ww is not None:
                if self.full.get():
                    result = f'!{self.buffer} from {conc.get_thread_identity(ww)}'
                else:
                    result = f'! from {conc.get_thread_identity(ww)}'
            else:
                result = f'? from {conc.get_thread_identity(wr)}'
        return result + self.finished_rw()

    def __str__(self) -> str:
        closed = "(CLOSED)" if self.closed.get() else ""
        return f'{self.name}: {closed} {self.current_state}'

    def show_state(self) -> None:
        synced_print(f"CHANNEL {self.name}: {self.name_generator._kind} ", end='')
        if self.closed.get(): synced_print('(CLOSED) ', end='')
        synced_print(self.current_state(), end='')

    def __lshift__(self, value) -> None:
        self.check_open()
        current = threading.current_thread()
        last_writer: threading.Thread = self.writer.get_and_set(current)
        assert last_writer is None, f'c << {value} overtaking ' \
                                f'[{conc.get_thread_identity(last_writer)}]' \
                                f' in {conc.get_thread_identity(current)}'
        self.buffer = value
        self.full.set(True)
        self.in_port_event(READYSTATE)
        conc.unpark(self.reader.get())
        while not self.closed.get() and self.full.get():
            conc.park_current_thread()
        if self.full.get():
            self.check_open()
        self.writer.set(None)
        self.finished_write()

    def __invert__(self):
        self.check_open()
        current = threading.current_thread()
        last_reader: threading.Thread = self.reader.get_and_set(current)
        assert last_reader is None, f'~c() overtaking ' \
                                  f'[{util.get_thread_identity(last_reader)}]' \
                                  f' in {util.get_thread_identity(current)}'
        self.out_port_event(READYSTATE)
        while not self.closed.get() and not self.full.get():
            conc.park_current_thread()
        self.check_open()
        result = self.buffer
        self.buffer = None
        self.full.set(False)
        conc.unpark(self.writer.get_and_set(None))
        self.reader.set(None)
        self.finished_read()
        return result

    def close(self):
        if not self.closed.get_and_set(True):
            self.out_port_event(CLOSEDSTATE)
            self.in_port_event(CLOSEDSTATE)
            unpark(self.reader.get_and_set(null))
            unpark(self.writer.get_and_set(null))
            self.unregister()

    def extended_rendezvous(self, func):
        self.check_open()
        current = threading.current_thread()
        last_reader: threading.Thread = self.reader.get_and_set(current)
        assert last_reader is None, f'~c(f) overtaking ' \
                                  f'[{util.get_thread_identity(last_reader)}]' \
                                  f' in {util.get_thread_identity(current)}'
        self.out_port_event(READYSTATE)
        while not self.closed.get() and not self.full.get():
            util.park_current_thread()
        self.check_open()
        result = func(self.buffer)
        self.buffer = None
        self.full.set(False)
        util.unpark(self.writer.get_and_set(null))
        self.reader.set(None)
        self.finished_read()
        return result

    @property
    def can_input(self) -> bool:
        return not self.closed.get()

    def close_in(self) -> None:
        self.close()

    @property
    def can_output(self) -> bool:
        return not self.closed.get()

    def close_out(self):
        self.close()

    def check_open(self) -> None:
        if self.closed.get():
            self.writer.set(None)
            self.reader.set(None)
            raise util.Closed(self.name)

    def read_before(self, ns: Nanoseconds) -> Optional[T]:
        raise NotImplementedError

    def write_before(self, ns: Nanoseconds, val: T) -> bool:
        raise NotImplementedError


class _OneOneGenerator(NameGenerator, metaclass=Singleton):

    def __init__(self):
        super().__init__('OneOne')

    def __call__(self, name: Optional[str] = None) -> _OneOne:
        if name is None:
            name = self._new_name()
        return _OneOne(name)

OneOne = _OneOneGenerator()
