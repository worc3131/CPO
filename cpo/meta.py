
from typing import Any, Callable, Iterable, List, Optional, Sequence, TypeVar

from . import process
from .util import Closed, Stopped

def proc(fn: Callable, *args) -> process.PROC:
    """A decorator to create a process"""
    def proc_():
        fn(*args)
    return process.Simple(proc_)

T = TypeVar('T')
def procs(variant_arg: Optional[Iterable[T]] = None,
          variant_args: Optional[Iterable[Sequence]] = None) \
        -> Callable[[Callable], process.PROC]:
    """A decorator to create multiple processes"""
    def decorator(fn: Callable) -> process.PROC:
        if variant_arg is not None:
            return process.ParSyntax([proc(fn, arg) for arg in variant_arg])
        if variant_args is not None:
            return process.ParSyntax([proc(fn, *args) for args in variant_args])
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
           guard: Optional[Callable[[], bool]] = None) \
        -> Callable:
    """ A decorator to repeat an action """
    def decorator(body):
        def inner(*args) -> None:
            nonlocal guard
            if guard is None:
                guard = lambda *args: True
            go = guard(*args)
            while go:
                try:
                    body(*args)
                    go = guard(*args)
                except Stopped:
                    go = False
                except Exception:
                    raise
        return inner
    if body is None:
        return decorator
    else:
        return decorator(body)

def fork(proc: process.PROC) -> process.Handle:
    """ A decorator to fork a process """
    return proc.fork()

def fork_proc(fn: Callable, *args) -> process.Handle:
    """ A decorate to create and fork a process """
    return fork(proc(fn, *args))

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
