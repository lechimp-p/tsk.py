#
# Define tasks depending on each other and execute them.
#
# Copyright (c) 2016 Richard Klees <richard.klees@rwth-aachen.de>
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

@task
def make_foo_teardown():
    yield "foo"
    log("teardown")
    yield make_foofoo_contreived()

@task
def make_foofoo_contreived():
    foo1 = yield make_foo_teardown()
    foo2 = yield make_foo_teardown()
    yield foo1 + foo2
    yield make_foo_teardown()
    log("foofoo")

@with_setup(setup_function)
def test_exchange_initial_goal():
    # I should be able to execute this, as i already have
    # all results i need. There is no LoopError.
    res = make_foofoo_contreived().run()

    assert res == "foofoo"
    assert log() == ["teardown", "foofoo"]

@with_setup(setup_function)
def test_with_log_task_simple():
    _log = []

    res = make_foobar().run(log = lambda msg: _log.append(msg))

    assert res == "foobar"
    assert len(_log) == 6

    l0 = _log[0]
    assert isinstance(l0, EnteredTask)
    assert l0.task.__name__ == "make_foobar"
    assert l0.args == ()
    assert [t.task.__name__ for t in l0.dependents] == []

    l1 = _log[1]
    assert isinstance(l1, EnteredTask)
    assert l1.task.__name__ == "make_foo"
    assert l1.args == ()
    assert [t.task.__name__ for t in l1.dependents] == ["make_foobar"]

    l2 = _log[2]
    assert isinstance(l2, CompletedTask)
    assert l2.task.__name__ == "make_foo"
    assert l2.args == ()
    assert [t.task.__name__ for t in l2.dependents] == ["make_foobar"]

    l3 = _log[3]
    assert isinstance(l3, EnteredTask)
    assert l3.task.__name__ == "make_bar"
    assert l3.args == ()
    assert [t.task.__name__ for t in l3.dependents] == ["make_foobar"]

    l4 = _log[4]
    assert isinstance(l4, CompletedTask)
    assert l4.task.__name__ == "make_bar"
    assert l4.args == ()
    assert [t.task.__name__ for t in l4.dependents] == ["make_foobar"]

    l5 = _log[5]
    assert isinstance(l5, CompletedTask)
    assert l5.task.__name__ == "make_foobar"
    assert l5.args == ()
    assert [t.task.__name__ for t in l5.dependents] == []

@with_setup(setup_function)
def test_with_log_task_args():
    _log = []

    res = make_123().run(log = lambda msg: _log.append(msg))

    assert res == "123"
    assert len(_log) == 8

    l0 = _log[0]
    assert isinstance(l0, EnteredTask)
    assert l0.task.__name__ == "make_123"
    assert l0.args == ()
    assert [t.task.__name__ for t in l0.dependents] == []

    l1 = _log[1]
    assert isinstance(l1, EnteredTask)
    assert l1.task.__name__ == "make_num"
    assert l1.args == (1,)
    assert [t.task.__name__ for t in l1.dependents] == ["make_123"]

    l2 = _log[2]
    assert isinstance(l2, CompletedTask)
    assert l2.task.__name__ == "make_num"
    assert l2.args == (1,)
    assert [t.task.__name__ for t in l2.dependents] == ["make_123"]

    l3 = _log[3]
    assert isinstance(l3, EnteredTask)
    assert l3.task.__name__ == "make_num"
    assert l3.args == (2,)
    assert [t.task.__name__ for t in l3.dependents] == ["make_123"]

    l4 = _log[4]
    assert isinstance(l4, CompletedTask)
    assert l4.task.__name__ == "make_num"
    assert l4.args == (2,)
    assert [t.task.__name__ for t in l4.dependents] == ["make_123"]

    l5 = _log[5]
    assert isinstance(l5, EnteredTask)
    assert l5.task.__name__ == "make_num"
    assert l5.args == (3,)
    assert [t.task.__name__ for t in l5.dependents] == ["make_123"]

    l6 = _log[6]
    assert isinstance(l6, CompletedTask)
    assert l6.task.__name__ == "make_num"
    assert l6.args == (3,)
    assert [t.task.__name__ for t in l6.dependents] == ["make_123"]

    l7 = _log[7]
    assert isinstance(l7, CompletedTask)
    assert l7.task.__name__ == "make_123"
    assert l7.args == ()
    assert [t.task.__name__ for t in l7.dependents] == []

@with_setup(setup_function)
def test_with_log_task_reuse_result():
    _log = []

    res = make_foofoo().run(log = lambda msg: _log.append(msg))

    assert res == "foofoo"
    assert len(_log) == 5

    l0 = _log[0]
    assert isinstance(l0, EnteredTask)
    assert l0.task.__name__ == "make_foofoo"
    assert l0.args == ()
    assert [t.task.__name__ for t in l0.dependents] == []

    l1 = _log[1]
    assert isinstance(l1, EnteredTask)
    assert l1.task.__name__ == "make_foo"
    assert l1.args == ()
    assert [t.task.__name__ for t in l1.dependents] == ["make_foofoo"]

    l2 = _log[2]
    assert isinstance(l2, CompletedTask)
    assert l2.task.__name__ == "make_foo"
    assert l2.args == ()
    assert [t.task.__name__ for t in l2.dependents] == ["make_foofoo"]

    l3 = _log[3]
    assert isinstance(l3, UseResultOfTask)
    assert l3.task.__name__ == "make_foo"
    assert l3.args == ()
    assert [t.task.__name__ for t in l3.dependents] == ["make_foofoo"]

    l4 = _log[4]
    assert isinstance(l4, CompletedTask)
    assert l4.task.__name__ == "make_foofoo"
    assert l4.args == ()
    assert [t.task.__name__ for t in l4.dependents] == []

