
from __future__ import annotations

from abc import ABCMeta
import threading
import traceback
from typing import List, Optional, Sequence, Union

from .atomic import AtomicCounter
from . import channel
from . import conc
from . import executor
from . import util

Latch = conc.CountDownLatch

class Handle(util.Runnable):
    # Handle on a CSO process

    def __init__(self, name: str, body,
                 latch: Optional[Latch], stack_size: int = 0):
        self.name = name
        self.body = body
        self.latch = latch
        self.stack_size = stack_size
        self.exc: Optional[Exception] = None
        self.thread: Optional[threading.Thread] = None

    def __repr__(self) -> str:
        return f'Handle({self.name}, ..., {self.latch}, {self.stack_size})'

    def __str__(self) -> str:
        return f'{repr(self)} thread={self.thread}, ' \
               f'exc={self.exc}, tb={self.exc.__traceback__ if self.exc else ""}'

    def is_alive(self) -> bool:
        if self.thread is None:
            return False
        return self.thread.is_alive()

    def interrupt(self) -> None:
        #if thread is not None: thread.interrupt()
        raise Exception('Not possible in python..')

    def start(self) -> None:
        assert executor.executor is not None
        # widgeter.widgetfactory(widget).widget(widget=Widget(widget=foo))
        executor.executor.execute(self, self.stack_size)

    def join(self) -> None:
        if self.latch is not None:
            self.latch.wait()

    def run(self) -> None:
        orig_name = ""
        try:
            self.thread = threading.current_thread()
            orig_name = self.thread.getName()
            self.thread.setName(self.name)
            self.body()
        except util.Stopped as e:
            self.exc = e
        except Exception as e:
            if Process.handle_exception is not None:
                Process.handle_exception(self.name, e)
            self.exc = e
        finally:
            if self.thread is not None:
                self.thread.setName(orig_name)
            self.thread = None

        if self.latch is not None:
            self.latch.count_down()


class PROC(metaclass=ABCMeta):

    def __init__(self):
        self._name: Optional[str] = None
        self._stack_size: Optional[int] = None

    def __call__(self) -> None:
        raise NotImplementedError

    def fork(self) -> Handle:
        raise NotImplementedError

    def __str__(self):
        return self.name

    def with_stack_size(self, stack_size: int) -> PROC:
        self._stack_size = stack_size
        return self

    @property
    def stack_size(self) -> Optional[int]:
        return self._stack_size

    @property
    def name(self) -> Optional[str]:
        return self._name

    def with_name(self, _name: str) -> PROC:
        self._name = _name
        return self

    def __or__(self, other: PROC) -> PROC:
        return ParSyntax([self, other])

    def __rshift__(self, other: PROC):
        return OrderedSyntax([self, other])


# lock for printing exceptions, to stop lots of exceptions being
# overwritten on touch of each other
_exception_lock = threading.Lock()
class Process:
    # NOTE confusingly we will refer to processes when these are actually run
    # as threads. Process refers to a CSO process.

    def __init__(self):
        self.process_count = AtomicCounter
        self.stopped = util.Stopped()

    def gen_name(self):
        return f'Proc-{next(self.process_count)}'

    @staticmethod
    def handle_exception(name, exc):
        with _exception_lock:
            util.synced_print(f"Process {name} terminated by throwing {exc}")
            traceback.print_tb(exc.__traceback__)


class Simple(PROC):

    def __init__(self, body, name=None):
        super().__init__()
        self.body = body
        self._stack_size = 0
        if name is None:
            name = "<anonymous>"
        self._name = name

    def fork(self) -> Handle:
        assert self.name is not None
        handle = Handle(self.name, self.body, conc.CountDownLatch())
        handle.start()
        return handle

    def __call__(self) -> None:
        self.body()


class IterToChannel(Simple):

    def __init__(self, iter_, channel_: channel.OutPort, name=None):
        if not hasattr(iter_, '__next__'):
            iter_ = iter(iter_)
        self.iter_ = iter_
        self.channel_ = channel_
        super().__init__(self.iter_to_channel, name)

    def iter_to_channel(self):
        try:
            while True:
                self.channel_ << next(self.iter_)
        except StopIteration:
            pass
        except util.Closed:
            pass
        finally:
            self.channel_.close_out()


class _SKIP(Simple):

    def __init__(self):
        def pass_():
            pass
        super().__init__(pass_)

    name = 'SKIP'

    def __or__(self, other: PROC) -> PROC:
        return other

SKIP = _SKIP()


class Par(PROC):

    def __init__(self, name: str, procs: Sequence[PROC]) -> None:
        super().__init__()
        self.procs = procs
        self._stack_size = 0
        self._name = name

    def __call__(self):
        procs = self.procs
        latch = conc.CountDownLatch(len(procs)-1)
        peer_handles = [
            Handle(proc.name, proc, latch, proc.stack_size)
            for proc in procs[1:]
        ]
        first_handle = Handle(procs[0].name, procs[0], None, procs[0].stack_size)
        for handle in peer_handles:
            handle.start()
        first_handle.run()
        latch.wait()

        # termination state
        exc = first_handle.exc
        for handle in peer_handles:
            hexc = handle.exc
            if exc is None and hexc is None:
                pass
            elif isinstance(exc, util.Stopped):
                pass  #exc = exc
            elif isinstance(hexc, util.Stopped):
                exc = hexc
            else:
                raise ParException([first_handle.exc] +
                                   [h.exc for h in peer_handles])
        if exc is not None:
            raise exc

    def fork(self) -> Handle:
        assert self.name is not None
        handle = Handle(self.name, self.__call__, conc.CountDownLatch())
        handle.start()
        return handle


class OrderedProcs(PROC):

    def __init__(self, name: str, procs: Sequence[PROC]) -> None:
        super().__init__()
        self.procs = procs
        self._stack_size = 0
        self._name = name

    def fork(self) -> Handle:
        assert self.name is not None
        handle = Handle(self.name, self.__call__, conc.CountDownLatch())
        handle.start()
        return handle

    def __call__(self) -> None:
        for p in self.procs:
            p()

class ParException(Exception):

    def __init__(self, exceptions: Sequence[Exception]):
        self.exceptions = exceptions

    def __repr__(self):
        return f'ParException({", ".join(self.exceptions)})'


class ParSyntax(PROC):

    def __init__(self, _procs: List[PROC]):
        self.procs = _procs
        self._stack_size = 0

    @property
    def compiled(self):
        return Par(self.name, self.procs)

    def __call__(self):
        return self.compiled()

    def fork(self):
        return self.compiled.fork()

    @property
    def name(self):
        return "|".join(str(x.name) for x in self.procs)

    def __or__(self, other: Union[PROC, ParSyntax]):
        if isinstance(other, ParSyntax):
            return ParSyntax(self.procs + other.procs)
        else:
            # PROC
            return ParSyntax(self.procs + [other])


class OrderedSyntax(PROC):

    def __init__(self, _procs: List[PROC]):
        self.procs = _procs
        self._stack_size = 0

    @property
    def compiled(self):
        return OrderedProcs(self.name, self.procs)

    def __call__(self):
        return self.compiled()

    def fork(self):
        return self.compiled.fork()

    @property
    def name(self):
        return ">>".join(str(x.name) for x in self.procs)

    def __rshift__(self, other: Union[PROC, OrderedSyntax]):
        if isinstance(other, OrderedSyntax):
            return OrderedSyntax(self.procs + other.procs)
        else:
            # PROC
            return OrderedSyntax(self.procs + [other])
