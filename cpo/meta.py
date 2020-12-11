
import inspect
import random
from typing import Callable, Iterable, Optional, Sequence, TypeVar

from . import process
from .util import Closed, Crashed, Stopped

def proc(fn: Optional[Callable] = None, *args, **kwargs):
    """A decorator to create a process"""
    def decorator(fn):
        def proc_():
            fn(*args, **kwargs)
        return process.Simple(proc_, name=fn)
    if fn is None:
        return decorator
    else:
        return decorator(fn)

T = TypeVar('T')
def procs(variant_arg: Optional[Iterable[T]] = None,
          variant_args: Optional[Iterable[Sequence]] = None):
    """ A decorator to create multiple concurrent processes """
    def decorator(fn: Callable) -> process.PROC:
        if variant_arg is not None and variant_args is None:
            return process.ParSyntax([proc(fn, arg) for arg in variant_arg])
        if variant_arg is None and variant_args is not None:
            return process.ParSyntax([proc(fn, *args) for args in variant_args])
        raise ValueError("Must set one of variant_arg and "
                         "variant_args but not both")
    return decorator

def ordered_procs(variant_arg: Optional[Iterable[T]] = None,
          variant_args: Optional[Iterable[Sequence]] = None):
    """ A decorator to create multiple ordered processes """
    def decorator(fn: Callable) -> process.PROC:
        if variant_arg is not None and variant_args is None:
            return process.OrderedSyntax([proc(fn, arg)
                                          for arg in variant_arg])
        if variant_arg is None and variant_args is not None:
            return process.OrderedSyntax([proc(fn, *args)
                                          for args in variant_args])
        raise ValueError("Must set one of variant_arg and "
                         "variant_args but not both")
    return decorator

def attempt(body: Optional[Callable] = None,
            alt: Optional[Callable[[], None]] = None) \
        -> Callable:
    """ A decorater to attempt an action """
    def decorator(body):
        def inner(*args) -> None:
            try:
                body(*args)
            except Stopped:
                if alt is not None:
                    alt(*args)
            except Exception:
                raise
        return inner
    if body is None:
        return decorator
    else:
        return decorator(body)

def repeat(body: Optional[Callable] = None,
           guard: Optional[Callable[[], bool]] = None,
           finally_: Optional[Callable[[], None]] = None,
           prob_crash: float = 0) \
        -> Callable:
    """ A decorator to repeat an action """
    def decorator(body):
        def inner(*args) -> None:
            nonlocal guard
            if guard is None:
                guard = lambda *args: True
            go = guard(*args)
            while go:
                if prob_crash > 0 and random.random() < prob_crash:
                    raise Crashed
                try:
                    body(*args)
                    go = guard(*args)
                except Stopped:
                    go = False
                except Exception:
                    if finally_ is not None:
                        finally_()
                    raise
            if finally_ is not None:
                finally_()
        return inner
    if body is None:
        return decorator
    else:
        return decorator(body)

def fork(proc: process.PROC) -> process.Handle:
    """ A decorator to fork a process """
    return proc.fork()

def fork_proc(fn: Optional[Callable] = None, *args, **kwargs):
    """ A decorate to create and fork a process """
    def decorator(fn):
        return fork(proc(fn, *args, **kwargs))
    if fn is None:
        return decorator
    else:
        return decorator(fn)

def fork_procs(variant_arg: Optional[Iterable[T]] = None,
          variant_args: Optional[Iterable[Sequence]] = None) \
        -> Callable[[Callable], process.Handle]:
    """ A decorate to create and fork multiple processes """
    procs_dec = procs(variant_arg, variant_args)
    def decorator(fn: Callable) -> process.Handle:
        procs = procs_dec(fn)
        return procs.fork()
    return decorator

def run(proc: process.PROC) -> None:
    proc()

def stop() -> None:
    raise Stopped

def gen_proc(gen=None, in_channel=None, out_channel=None):
    def decorator(gen):
        if inspect.isgeneratorfunction(gen):
            gen = gen()
        processes = []
        if in_channel is not None:
            @proc
            @repeat
            def read():
                try:
                    gen.send(~in_channel)
                except StopIteration:
                    raise Stopped
            processes.append(read)
        if out_channel is not None:
            @proc
            @repeat
            def write():
                try:
                    out_channel << next(gen)
                except StopIteration:
                    out_channel.close()
                    raise Stopped
            processes.append(write)
        return process.ParSyntax(processes)
    if gen is None:
        return decorator
    else:
        return decorator(gen)

def fork_gen_proc(gen=None, in_channel=None, out_channel=None):
    def decorator(gen):
        return fork(gen_proc(gen, in_channel, out_channel))
    if gen is None:
        return decorator
    else:
        return decorator(gen)

