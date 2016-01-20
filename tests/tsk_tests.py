#
# Define tasks depending on each other and execute them.
#
# Copyright (c) 2015 Richard Klees <richard.klees@rwth-aachen.de>
#
# This software is licensed under The MIT License. You should have
# received a copy of the LICENSE with the code.
#

from nose.tools import with_setup
from tsk.tsk import *

_log = [["foo"]]

def log(msg = None):
    if msg is None:
        return _log[0]
    _log[0].append(msg)

def setup_function():
    _log[0] = []

@with_setup(setup_function)
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

@with_setup(setup_function)
def test_make_foo():
    res = make_foo().run()

    assert res == "foo"
    assert log() == ["foo"]

@with_setup(setup_function)
def test_make_foobar():
    res = make_foobar().run()

    assert res == "foobar"
    assert log() == ["foo", "bar", "foobar"]

@task
def make_foofoo():
    foo1 = yield make_foo()
    foo2 = yield make_foo()
    yield foo1 + foo2

@with_setup(setup_function)
def test_dont_run_twice():
    res = make_foofoo().run()

    assert res == "foofoo"
    assert log() == ["foo"]

@task
def make_num(num):
    log(num)
    yield num

@task
def make_123():
    v1 = yield make_num(1)
    v2 = yield make_num(2)
    v3 = yield make_num(3)
    yield "%d%d%d" % (v1, v2, v3)

@with_setup(setup_function)
def test_with_params():
    res = make_123().run()

    assert res == "123"
    assert log() ==  [1,2,3]

@task
def make_111():
    v1 = yield make_num(1)
    v2 = yield make_num(1)
    v3 = yield make_num(1)
    yield "%d%d%d" % (v1, v2, v3)

@with_setup(setup_function)
def test_dont_run_twice_with_params():
    res = make_111().run()

    assert res == "111"
    assert log() == [1]

@task
def make_foobar_par():
    foo, bar = yield (make_foo(), make_bar())
    log(foo + bar)
    yield foo + bar

@with_setup(setup_function)
def test_run_par():
    res = make_foobar_par().run()

    assert res == "foobar"
    assert log() == ["foo", "bar", "foobar"]

@task
def make_123_par():
    v1,v2,v3 = yield (make_num(1), make_num(2), make_num(3))
    yield "%d%d%d" % (v1, v2, v3)

@with_setup(setup_function)
def test_run_par_with_params():
    res = make_123_par().run()

    assert res == "123"
    assert log() ==  [1,2,3]

@task
def make_barfoobar():
    bar = yield make_bar()
    foobar = yield make_foobar()
    yield bar + foobar

@with_setup(setup_function)
def test_run_nested():
    res = make_barfoobar().run()

    assert res == "barfoobar"
    assert log() == ["bar", "foo", "foobar"] 

@task
def make_loop():
    l = yield make_loop()
    yield "res"

@with_setup(setup_function)
def test_detect_loop():
    try:
        make_loop().run()
        assert False
    except LoopError:
        pass

@task
def make_loop_1():
    l = yield make_loop_2()
    yield "res"

@task
def make_loop_2():
    l = yield make_loop_1()
    yield "res"

@with_setup(setup_function)
def test_detect_long_loop():
    try:
        make_loop_1().run()
        assert False
    except LoopError:
        pass

@with_setup(setup_function)
def test_props():
    assert make_loop.__name__ == "make_loop"

@task
def make_foo_early():
    log("before")
    yield "foo"
    log("after")

@with_setup(setup_function)
def test_early_result():
    res = make_foo_early().run()

    assert res == "foo"
    assert log() == ["before", "after"]

@task
def make_foo_and_then_bar():
    yield "foo"
    yield "bar"

@with_setup(setup_function)
def test_no_double_result():
    try:
        make_foo_and_then_bar().run()
        assert False
    except DoubleResultError:
        pass

@task
def make_foo_spawn_foobar():
    log("foo_spawn")
    yield "foo"
    foobar = yield make_foobar()
    log(foobar + "_spawn")

@with_setup(setup_function)
def test_early_result_with_new_task():
    res = make_foo_spawn_foobar().run()

    assert res == "foo"
    assert log() == ["foo_spawn", "foo", "bar", "foobar", "foobar_spawn"]
