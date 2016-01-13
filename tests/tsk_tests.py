from tsk import * 

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

@task
def make_foobar():
    foo = yield make_foo()
    bar = yield make_bar()
    log(foo + bar)
    yield foo + bar

@task
def make_foo():
    log("foo")
    yield "foo"

@task
def make_bar():
    log("bar")
    yield "bar"

def test_make_foobar():
    res = make_foobar.run()

    assert res == "foobar"
    assert log() == ["foo", "bar", "foobar"]
