from nose.tools import *
import blg

_log = [[]]

def log(msg = None):
    if msg is None:
        return _log[0]
    _log[0].append(msg)

def setup():
    _log[0] = []

def teardown():
    pass

def test_log():
    log("foo")
    log("bar")

    assert log() == ["foo", "bar"]
