
from __future__ import annotations

from abc import ABC
import queue
import random
import threading
from typing import Generic, List, Optional, TypeVar, Callable

from .atomic import Atomic, AtomicNum
from . import conc
from .name import Named, NameGenerator
from .register import Debuggable
from . import threads
from . import util
from .util import Nanoseconds, Singleton, synced_print

class PortState(metaclass=Singleton):
    """A type denoting the state of readiness/commitment of a port. Used in the
    implementation of alternations"""
    def __str__(self) -> str:
        raise NotImplementedError
    def to_state_string(self) -> str:
        raise NotImplementedError

class _CLOSEDSTATE(PortState):
    """The port is closed"""
    def __str__(self):
        return "CLS"
    def to_state_string(self) -> str:
        return "CLS: "
CLOSEDSTATE = _CLOSEDSTATE()

class _UNKNOWNSTATE(PortState):
    """The readiness of the port is unknown"""
    def __str__(self):
        return "UNK"
    def to_state_string(self) -> str:
        return ""
UNKNOWNSTATE = _UNKNOWNSTATE()

class _READYSTATE(PortState):
    """The port's channel is in a state that guarantees the next unconditional
    input/output action on the port can be invoked with no danger of an
    unbounded wait."""
    def __str__(self):
        return "RDY"
    def to_state_string(self) -> str:
        return "RDY: "
READYSTATE = _READYSTATE()


TI = TypeVar('TI')
O = TypeVar('O')
class InPort(Generic[TI]):

    def __invert__(self) -> Optional[TI]:
        """ Block until a value is available for input, then read and return it.

        Returns: The value from the channel.

        """
        raise NotImplementedError

    def read_before(self, ns: Nanoseconds) -> Optional[TI]:
        """ Block until either a value is available or ns nanseconds have
        passed. Then return the available value or None.

        Args:
            ns: The number of nanoseconds to wait.

        Returns: A value from the channel if one was available with the time
        limit else None.

        """
        raise NotImplementedError

    def __call__(self, func) -> InPortFunc[TI]:
        """Block until a value t is available, then return f(t).
        If our channel is c and our function is f, the full syntax is ~c(f).
        """
        return InPortFunc(self, func)

    def extended_rendezvous(self, func: Callable[[TI], O]) -> O:
        """Block until a value t is available for input then return f(t)"""
        raise NotImplementedError

    def close_in(self):
        """Signal that no further attempt will be made to input from the
        invoking thread. This is idempotent."""
        raise NotImplementedError

    def can_input(self) -> bool:
        """Returns False if no further input will be supplied by this port.
        Returning true is not a guarantee that further input will supplied."""
        raise NotImplementedError

    @property
    def nothing(self) -> Optional[TI]:
        """The null value for this port"""
        return None

    def in_port_state(self) -> PortState:
        """The current state of this port for alternation implementations"""
        raise NotImplementedError

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self.__invert__()
        except util.Stopped:
            raise StopIteration


class InPortFunc(Generic[TI]):

    def __init__(self, port: InPort, func):
        self.port = port
        self.func = func

    def __invert__(self):
        """Get from the port and apply the function"""
        return self.port.extended_rendezvous(self.func)

TO = TypeVar('TO')
class OutPort(Generic[TO]):

    def __lshift__(self, value: TO) -> Optional[TO]:
        """Output value to the port's channel"""
        raise NotImplementedError

    def write_before(self, nswait: Nanoseconds, value: TO) -> bool:
        """Output value to the port's channel before nswait has elapsed and return
        true, or else false.


        Args:
            nswait: The number of nanoseconds to wait.
            value: The value to write.

        Returns: Whether the write was successful.

        """
        raise NotImplementedError

    def close_out(self) -> None:
        """Signal that no further values will be output from the invoking
        thread. This is idempotent."""
        raise NotImplementedError

    def can_output(self) -> bool:
        """Returns false if no further output can be accepted by this port.
        Returning true is not a guarantee that further output will be accepted"""
        raise NotImplementedError

    def out_port_state(self) -> PortState:
        """Current state of this port for use in alternation implementations"""
        raise NotImplementedError

T = TypeVar('T')
class Chan(InPort[T], OutPort[T], Named, Debuggable, ABC):
    """A channel with an in and out port"""

    def __init__(self):
        Debuggable.__init__(self)

    def close(self) -> None:
        """Signal that the channel is to be closed forthwith"""
        raise NotImplementedError

    def out_port_event(self, port_state: PortState) -> None:
        """The channel has just changd its state in a way that will affect
        out_port_state()"""
        pass

    def in_port_event(self, port_state: PortState) -> None:
        """The channel has just changd its state in a way that will affect
          in_port_state()"""
        pass

class SyncChan(Chan[T], ABC):
    """A channel which is guaranteed to be synchronous."""

    def __init__(self):
        Chan.__init__(self)

class SharedChan(Chan[T], ABC):
    """A channel whose input and output ports may be shared."""
    pass

class _OneOne(SyncChan[T]):
    """A synchronised channel to be used by at most one reader and at most one
     writer process simultaneously."""

    def __init__(self, name):
        """

        Args:
            name: The name of the channel for debugging.
        """
        SyncChan.__init__(self)
        self.set_name(name)
        self.reader: Atomic[Optional[threading.Thread]] = Atomic(None)
        self.writer: Atomic[Optional[threading.Thread]] = Atomic(None)
        self.closed, self.full = Atomic(False), Atomic(False)
        self.buffer = None
        self.reads = AtomicNum(0)
        self.writes = AtomicNum(0)
        self.register()

    def _finished_read(self) -> int:
        """Increment the count of finished reads"""
        return self.reads.inc(1)

    def _finished_write(self) -> int:
        """Increment the count of finished writes"""
        return self.writes.inc(1)

    def finished_rw(self) -> str:
        """Get a string repr of the number of finished reads and writes"""
        return f'(READ {self.reads}, WRITTEN {self.writes})'

    @property
    def in_port_state(self) -> PortState:
        """READY if not closed and a writer is waiting to sync (else CLOSED or
         UNKNOWN). Used by alternation implementations."""
        if self.closed.get():
            return CLOSEDSTATE
        if self.full.get():
            return READYSTATE
        return UNKNOWNSTATE

    @property
    def out_port_state(self) -> PortState:
        """READY if not closed and a reader is waiting to sync (else CLOSED or
         UNKNOWN). Used by alternation implementations."""
        if self.closed.get():
            return CLOSEDSTATE
        if self.reader.get() is not None and not self.full.get():
            return READYSTATE
        return UNKNOWNSTATE

    @property
    def name_generator(self) -> NameGenerator:
        return OneOne

    def current_state(self) -> str:
        """Return a string giving the current state of the channel"""
        wr = self.reader.get()
        ww = self.writer.get()
        if ww is None and wr is None:
            result = "idle"
        else:
            if ww is not None:
                if self.full.get():
                    result = f'write ({self.buffer}) from' \
                             f' {threads.get_thread_identity(ww)}'
                else:
                    result = f'write from {threads.get_thread_identity(ww)}'
            else:
                result = f'read from {threads.get_thread_identity(wr)}'
        return result + self.finished_rw()

    def __str__(self) -> str:
        closed = "(CLOSED)" if self.closed.get() else ""
        return f'{self.name}: {closed} {self.current_state}'

    def show_state(self, file) -> None:
        """Print the current state of the channel to file"""
        synced_print(f"CHANNEL {self.name}: {self.name_generator._kind} ",
                     end='', file=file)
        if self.closed.get(): synced_print('(CLOSED) ', end='', file=file)
        synced_print(self.current_state(), end='', file=file)

    def __lshift__(self, value: T) -> T:
        self.check_open()
        current = threading.current_thread()
        last_writer: threading.Thread = self.writer.get_and_set(current)
        assert last_writer is None, f'c << {value} overtaking ' \
                                f'[{threads.get_thread_identity(last_writer)}]' \
                                f' in {threads.get_thread_identity(current)}'
        self.buffer = value
        self.full.set(True)
        self.in_port_event(READYSTATE)
        threads.unpark(self.reader.get())
        while not self.closed.get() and self.full.get():
            threads.park_current_thread()
        if self.full.get():
            self.check_open()
        self.writer.set(None)
        self._finished_write()
        return value

    def __invert__(self) -> T:
        return self.do_read(util.identity_fn)

    def extended_rendezvous(self, func: Callable[[T], O]) -> O:
        return self.do_read(func)

    def do_read(self, fn: Optional[Callable]):
        self.check_open()
        current = threading.current_thread()
        last_reader: threading.Thread = self.reader.get_and_set(current)
        assert last_reader is None, f'~c({"f" if fn else ""}) overtaking ' \
                                  f'[{threads.get_thread_identity(last_reader)}]' \
                                  f' in {threads.get_thread_identity(current)}'
        self.out_port_event(READYSTATE)
        while not self.closed.get() and not self.full.get():
            threads.park_current_thread()
        self.check_open()
        result = fn(self.buffer)
        self.buffer = None
        self.full.set(False)
        threads.unpark(self.writer.get_and_set(None))
        self.reader.set(None)
        self._finished_read()
        return result

    def close(self):
        if not self.closed.get_and_set(True):
            self.out_port_event(CLOSEDSTATE)
            self.in_port_event(CLOSEDSTATE)
            threads.unpark(self.reader.get_and_set(None))
            threads.unpark(self.writer.get_and_set(None))
            self.unregister()

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

    def read_before(self, timeout: Nanoseconds) -> Optional[T]:
        assert self.reader.get() is None, f"~c() overtaking " \
                                          f"[{threads.get_thread_identity(self.reader.get())}]" \
                                          f" in {threads.get_thread_identity(threading.current_thread())}"
        self.check_open()
        curr = threading.current_thread()
        self.reader.set(curr)
        self.out_port_event(READYSTATE)
        success = 0 < threads.park_current_thread_until_elapsed_or(
            timeout,
            lambda: self.closed.get() or self.full.get(),
        )
        self.check_open()
        result = self.buffer
        self.buffer = None
        self.full.set(False)
        threads.unpark(self.writer.get_and_set(None))
        self.reader.set(None)
        self._finished_read()
        return result if success else None

    def write_before(self, timeout: Nanoseconds, value: T) -> bool:
        assert self.writer.get() is None, f"c << {value} in " \
                                          f"{threads.get_thread_identity(threading.current_thread())}" \
                                          f" overtaking <<{self.buffer} " \
                                          f"[{threads.get_thread_identity(self.writer.get())}]"
        self.check_open()
        self.buffer = value
        curr = threading.current_thread()
        self.writer.set(curr)
        self.full.set(True)
        self.in_port_event(READYSTATE)
        threads.unpark(self.reader.get_and_set(None))
        success = 0 < threads.park_current_thread_until_elapsed_or(
            timeout,
            lambda: self.closed.get() or not self.full.get(),
        )
        if not success:
            self.full.set(False)
        self.writer.set(None)
        self.check_open()
        self._finished_write()
        return success

class _OneOneFactory(NameGenerator, metaclass=Singleton):

    def __init__(self):
        super().__init__('OneOne')

    def __call__(self, name: Optional[str] = None) -> _OneOne:
        """
        Args:
            name: The name for the channel.

        Returns: A new OneOne channel
        """
        if name is None:
            name = self._new_name()
        return _OneOne(name)

OneOne = _OneOneFactory()

class _N2N(SharedChan[T], _OneOne[T]):
    """"""

    def __init__(self, writers: int, readers: int,
                 name: str, fair_out: bool, fair_in: bool) -> None:
        super().__init__(name)
        self.ws = AtomicNum(writers)
        self.rs = AtomicNum(readers)
        self.wm = conc.TrackedFairRLock() if fair_out else conc.TrackedRLock()
        self.rm = conc.TrackedFairRLock() if fair_in else conc.TrackedRLock()

    def close_out(self):
        if self.ws.dec(1) == 0:
            self.close()

    def close_in(self):
        if self.rs.dec(1) == 0:
            self.close()

    def __lshift__(self, value: T) -> T:
        with self.wm:
            super().__lshift__(value)
        return value

    def write_before(self, ns: Nanoseconds, val: T) -> bool:
        deadline = util.nano_time() + ns
        if self.wm.acquire(timeout=float(ns)):
            try:
                remaining = deadline - util.nano_time()
                if remaining > 0:
                    return super().write_before(remaining, val)
                else:
                    return False
            finally:
                self.wm.release()
        else:
            return False

    def __invert__(self) -> T:
        with self.rm:
            return super().__invert__()

    def extended_rendezvous(self, func):
        with self.rm:
            super().extended_rendezvous(func)

    def read_before(self, ns: Nanoseconds) -> Optional[T]:
        deadline = util.nano_time() + ns
        if self.rm.acquire(timeout=float(ns)):
            try:
                remaining = deadline - util.nano_time()
                if remaining > 0:
                    return super().read_before(ns)
                else:
                    return None
            finally:
                self.rm.release()
        else:
            return None

    def get_waiting(self) -> List[threading.Thread]:
        return super().get_waiting() + \
               self.wm.get_waiting() + \
               self.rm.get_waiting()

    def show_state(self, file) -> None:
        ww = self.wm.num_waiting()
        rw = self.rm.num_waiting()
        super().show_state(file)
        print(f'\n\t({self.ws} writers and'
              f' {self.rs} readers remaining)', file=file)
        if rw > 0:
            ids = ', '.join(threads.get_thread_identity(t)
                            for t in self.rm.get_waiting())
            print(f'\n\tInPort queue: [{ids}]')
        if ww > 0:
            ids = ', '.join(threads.get_thread_identity(t)
                            for t in self.wm.get_waiting())
            print(f'\n\tOutPort queue: [{ids}]')


class _N2NFactory(NameGenerator, metaclass=Singleton):

    def __init__(self):
        super().__init__('N2N')

    def __call__(self, writers: int = 0, readers: int = 0, name: Optional[str] = None,
                 fair_out: bool = False, fair_in: bool = False) -> _N2N:
        if name is None:
            name = self._new_name()
        return _N2N(writers, readers, name, fair_out, fair_in)

N2N = _N2NFactory()

def ManyOne(writers: int = 0, name: Optional[str] = None):
    if name is None:
        name = N2N._new_name('ManyOne')
    return N2N(writers=writers, readers=1, name=name)

def OneMany(readers: int = 0, name: Optional[str] = None):
    if name is None:
        name = N2N._new_name('OneMany')
    return N2N(writers=1, readers=readers, name=name)

def ManyMany(name: Optional[str] = None):
    if name is None:
        name = N2N._new_name('ManyMany')
    return N2N(name=name)

class _N2NBuf(SharedChan[T]):

    def __init__(self, size: int, writers: int, readers: int, name: str):
        SharedChan.__init__(self)
        self.set_name(name)
        self.size = size
        self.ws = AtomicNum(writers)
        self.rs = AtomicNum(readers)
        self.input_closed = Atomic(False)
        self.output_closed = Atomic(False)
        self.reads = AtomicNum(0)
        self.writes = AtomicNum(0)
        self.queue: queue.Queue = queue.Queue(maxsize=size)
        self.register()

    @property
    def in_port_state(self) -> PortState:
        if self.input_closed.get():
            return CLOSEDSTATE
        if self.is_empty():
            return UNKNOWNSTATE
        return READYSTATE

    @property
    def out_port_state(self) -> PortState:
        if self.output_closed.get():
            return CLOSEDSTATE
        if self.is_full():
            return UNKNOWNSTATE
        return READYSTATE

    @property
    def name_generator(self) -> NameGenerator:
        return N2NBuf

    def _finished_read(self):
        return self.reads.inc(1)

    def _finished_write(self):
        return self.writes.inc(1)

    def finished_rw(self):
        return f'(READ {self.reads.get()}, WRITTEN {self.writes.get()})'

    def state(self, port: str, closed: bool) -> str:
        return f'{port} (CLOSED), ' if closed else ''

    def __str__(self):
        return f"CHANNEL {self.name}: {self.name_generator._kind} " \
               f"{self.state('OutPort', self.output_closed.get())} " \
               f"{self.state('InPort', self.input_closed.get())}" \
               f"(writers={self.ws.get()}, readers={self.rs.get()}) " \
               f"size={self.size}, length={self.queue.qsize()}) " \
               f"{self.finished_rw()}"

    def show_state(self, file) -> None:
        print(str(self), end='', file=file)

    def close(self) -> None:
        self.output_closed.set(True)
        self.input_closed.set(True)
        self.out_port_event(CLOSEDSTATE)
        self.in_port_event(CLOSEDSTATE)
        # clear the queue
        try:
            while True:
                self.queue.get_nowait()
        except queue.Empty:
            pass
        self.unregister()

    def close_out(self) -> None:
        if self.ws.dec(1) == 0:
            self.output_closed.set(True)
            if self.is_empty:
                self.close()

    def close_in(self):
        if self.rs.dec(1) == 0:
            self.input_closed.set(True)
            self.out_port_event(CLOSEDSTATE)
            self.close()

    @property
    def can_input(self) -> bool:
        return not (self.output_closed.get() and self.is_empty())

    @property
    def can_output(self) -> bool:
        return not self.input_closed.get()

    def is_empty(self) -> bool:
        return self.queue.empty()

    def is_full(self) -> bool:
        return self.queue.full()

    def __invert__(self) -> Optional[T]:
        if self.input_closed.get():
            raise util.Closed(self.name)
        if self.output_closed.get() and self.is_empty():
            self.close()
            raise util.Closed(self.name)
        try:
            self.out_port_event(READYSTATE)
            r = self.queue.get()
            self._finished_read()
            return r
        except queue.Empty:
            return None
        except InterruptedError:
            raise util.Closed(self.name)

    def read_before(self, ns: Nanoseconds) -> Optional[T]:
        if self.input_closed.get():
            raise util.Closed(self.name)
        if self.output_closed.get() and self.is_empty():
            self.close()
            raise util.Closed(self.name)
        self.out_port_event(READYSTATE)
        try:
            return self.queue.get(timeout=ns.to_seconds())
        except queue.Empty:
            return None

    def __lshift__(self, value: T) -> T:
        if self.output_closed.get() or self.input_closed.get():
            raise util.Closed(self)
        try:
            self.queue.put(value)
            self.in_port_event(READYSTATE)
            self._finished_write()
        except InterruptedError:
            raise util.Closed(self.name)
        if self.input_closed.get():
            raise util.Closed(self.name)
        return value

    def write_before(self, ns: Nanoseconds, value: T) -> bool:
        if self.output_closed.get() or self.input_closed.get():
            raise util.Closed(self.name)
        try:
            self.queue.put(value, timeout=ns.to_seconds())
            return True
        except queue.Full:
            return False

class _N2NBufFactory(NameGenerator, metaclass=Singleton):

    def __init__(self):
        super().__init__('N2NBuf')

    def __call__(self, size: int = 0, writers: int = 0, readers: int = 0,
                 name: Optional[str] = None) -> _N2NBuf:
        if name is None:
            name = self._new_name()
        return _N2NBuf(size, writers, readers, name)

N2NBuf = _N2NBufFactory()

def OneOneBuf(size: int = 0, name: Optional[str] = None):
    if name is None:
        name = N2N._new_name('OneOneBuf')
    return N2NBuf(size=size, writers=1, readers=1, name=name)

class FaultyMixin:

    def __init__(self, *args, prob_loss=0, **kwargs):
        self.prob_loss = prob_loss
        super().__init__(*args, **kwargs)

    def __lshift__(self, value):
        if random.random() > self.prob_loss:
            return super().__lshift__(value)

    def write_before(self, timeout: Nanoseconds, value) -> bool:
        if random.random() > self.prob_loss:
            return super().write_before(timeout, value)

class _FaultyOneOne(FaultyMixin, _OneOne):
    pass

class _FaultyOneOneFactory(NameGenerator, metaclass=Singleton):

    def __init__(self):
        super().__init__('FaultyOneOne')

    def __call__(self, prob_loss: float, name: Optional[str] = None) -> _OneOne:
        """
        Args:
            name: The name for the channel.

        Returns: A new FaultyOneOne channel
        """
        if name is None:
            name = self._new_name()
        return _FaultyOneOne(name, prob_loss=prob_loss)

FaultyOneOne = _FaultyOneOneFactory()
