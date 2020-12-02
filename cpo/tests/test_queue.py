
import pytest

from cpo import *

def test_queue_init():
    LockFreeQueue()

def test_lockfreequeue_endequeue():
    q = LockFreeQueue()
    q.enqueue(42)
    assert q.dequeue(42) == 42
    assert q.dequeue() is None

def test_lockfreequeue_peek():
    q = LockFreeQueue()
    assert q.peek() is None
    q.enqueue(123)
    assert q.peek() == 123
    assert q.dequeue() == 123

def test_lockfreequeue_remove_first():
    q = LockFreeQueue()
    q.enqueue(1)
    assert q.remove_first() == 1
    with pytest.raises(ValueError):
        q.remove_first()

def test_lockfreequeue_length():
    q = LockFreeQueue()
    assert q.length() == 0
    q.enqueue(1)
    assert q.length() == 1
    q.enqueue(1)
    assert q.length() == 2
    q.dequeue()
    assert q.length() == 1
    q.dequeue()
    assert q.length() == 0

def test_lockfreequeue_elements():
    q = LockFreeQueue()
    for x in range(3):
        q.enqueue(x)
    assert q.elements() == [0, 1, 2]
    assert q.length() == 3
    assert q.dequeue() == 0

def test_lockfreequeue_for_each():
    q = LockFreeQueue()
    for x in range(5):
        q.enqueue(x)
    v = []
    q.for_each(lambda x: v.append(x))
    assert v == [0, 1, 2, 3, 4]
    assert q.length() == 5
    assert q.dequeue() == 0

