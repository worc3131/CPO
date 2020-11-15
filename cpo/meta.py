
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

def attempt(body: Callable[[], None],
            alt: Optional[Callable[[], None]] = None) \
        -> Callable[[], None]:
    """ A decorater to attempt an action """
    def inner() -> None:
        try:
            body()
        except Stopped:
            if alt is not None:
                alt()
        except Exception:
            raise
    return inner

def repeat(body: Callable[[],  None],
           guard: Optional[Callable[[], bool]] = None) \
        -> Callable[[], None]:
    """ A decorator to repeat an action """
    def inner() -> None:
        nonlocal guard
        if guard is None:
            guard = lambda: True
        go = guard()
        while go:
            try:
                body()
                go = guard()
            except Stopped:
                go = False
            except Exception:
                raise
    return inner

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
