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

@task
def make_foofoo():
    foo1 = yield make_foo()
    foo2 = yield make_foo()
    yield foo1 + foo2

def test_dont_run_twice():
    res = make_foofoo.run()

    assert res == "foofoo"
    assert log() == ["foo"]

@task
def make_num(num):
    log(num)
    yield num

@task
def make_123():
    v1 = yield num(1)
    v2 = yield num(2)
    v3 = yield num(3)
    yield "%d%d%d" % (v1, v2, v3)

def test_with_params():
    res = make_123.run()

    assert res == "123"
    assert log() ==  [1,2,3]

@task
def make_111():
    v1 = yield num(1)
    v2 = yield num(1)
    v3 = yield num(1)
    yield "%d%d%d" % (v1, v2, v3)

def test_dont_run_twice_with_params():
    res = make_111.run()

    assert res == "111"
    assert log() == [1]

@task
def make_foobar_par():
    foo, bar = yield (foo(), bar())
    log(foo + bar)
    yield foo + bar

def test_run_par():
    res = make_foobar_par.run()

    assert res == "foobar"
    assert log() == ["foo", "bar", "foobar"]

@task
def make_123_par():
    v1,v2,v3 = yield (num(1), num(2), num(3))
    yield "%d%d%d" % (v1, v2, v3)

def test_run_par_with_params():
    res = make_123_par.run()

    assert res == "123"
    assert log() ==  [1,2,3]

@task
def make_barfoobar():
    bar = yield make_bar()
    foobar = yield make_foobar()
    yield bar + foobar

def test_run_nested():
    res = make_barfoobar.run()

    assert res == "barfoobar"
    assert log() == ["bar", "foo", "foobar"] 

@task
def make_loop():
    l = yield make_loop()
    yield "res"

def test_detect_loops():
    try:
        make_loop.run()
        assert False
    except LoopError:
        pass

def test_props():
    assert make_loop.__name__ == "make_loop"
