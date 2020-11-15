
from cpo import *

def test_init():
    Barrier(3)
    CombiningBarrier(3, 0, lambda x, y: x+y)
    OrBarrier(3)
    AndBarrier(3)
