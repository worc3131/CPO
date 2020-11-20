
import io

from cpo import *

def test_logger_init():
    Logger("", 0)

def test_logger():
    logger = Logger("my_logger", log_size=5)
    my_special_string = 'beepboopbopbip'
    logger.log(my_special_string)
    debug = DEBUGGER()
    f = io.StringIO()
    debug.show_cso_state(file=f)
    assert my_special_string in f.getvalue()

def test_logger_bits():
    logger = Logger("my_logger", log_size=5, mask=4)
    special_string1 = "abcdefghij"
    special_string2 = "qwertyuiop"
    logger.log(special_string1, bits=1)
    logger.log(special_string2, bits=4)
    debug = DEBUGGER()
    f = io.StringIO()
    debug.show_cso_state(file=f)
    assert special_string1 in f.getvalue()
    assert not special_string2 in f.getvalue()

def test_logger_size():
    logger = Logger("my_logger", log_size=5)
    for i in range(10):
        assert logger.num_entries == min(i, 5)
        logger.log("howdy")

def test_logger_zerosize():
    # zero means infinite
    logger = Logger("my_logger", log_size=0)
    for _ in range(5):
        logger.log("hello")
    assert logger.num_entries == 5

