
import queue as _queue

from typing import Generic, List, Optional, TypeVar

T = TypeVar('T')

class Queue(Generic[T]):

    def enqueue(self, value: T) -> None:
        raise NotImplementedError

    def enqueue_first(self, value: T) -> None:
        raise NotImplementedError

    def dequeue(self) -> Optional[T]:
        raise NotImplementedError

    def peek(self) -> Optional[T]:
        raise NotImplementedError

    def remove_first(self) -> None:
        raise NotImplementedError

    def length(self) -> int:
        raise NotImplementedError

    def elements(self) -> List[T]:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def for_each(self, f) -> None:
        raise NotImplementedError

class LockFreeQueue(Queue[T]):

    def __init__(self):
        self.queue = _queue.Queue()

    def length(self) -> int:
        return self.queue.qsize()

    def enqueue(self, value: T) -> None:
        self.queue.put(value, block=False)

    enqueue_first = enqueue

    def dequeue(self) -> Optional[T]:
        return self.queue.get(block=False)

    def peek(self) -> Optional[T]:
        with self.queue.mutex:
            # forgive me
            return next(iter(self.queue.queue), None)


    def remove_first(self) -> None:
        v = self.dequeue()
        if v is None:
            raise ValueError

    def elements(self) -> List[T]:
        with self.queue.mutex:
            return list(self.queue.queue)

    def for_each(self, f) -> None:
        for e in self.elements():
            f(e)

class LockFreeDequeue(Queue[T]):
    # not implemented
    pass
