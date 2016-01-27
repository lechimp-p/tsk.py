#
# Define tasks depending on each other and execute them.
#
# Copyright (c) 2015 Richard Klees <richard.klees@rwth-aachen.de>
#
# This software is licensed under The MIT License. You should have
# received a copy of the LICENSE with the code.
#

import functools
import types
from collections import namedtuple

class task(object):
    """
    Turn an ordinary generator of tasks to a task.
    """
    def __init__(self, fun):
        self.fun = fun

        functools.update_wrapper(self, fun)

    def __call__(self, *args, **kwargs):
        return TaskCall(self, args, kwargs)

    def __repr__(self):
        return self.fun.__repr__()


class TaskCall(object):
    """
    A call to a task
    """
    def __init__(self, task, args, kwargs):
        self.task = task
        self.args = args
        tup = namedtuple("Kwargs", kwargs.keys())
        self.kwargs = tup(**kwargs)

    def run(self):
        vm = VM(self)
        return vm.result()

    def __hash__(self):
        return hash((self.task, self.args, self.kwargs))

    def __eq__(self, other):
        return ((self.task, self.args, self.kwargs)
                == (other.task, other.args, other.kwargs))

    def __repr__(self):
        return "<call to task %s at %s>" % (self.task.__repr__(), hex(id(self)))


class VM(object):
    def __init__(self, tc):
        self.tc = tc

        self.results = {}       # results that are already known
        self.states = {}        # current states of task calls
        self.requires = {}      # requirement to advance state of task calls
        self.goals = [self.tc]  # we start with one single goal and stack
                                # futures goals above

    def result(self):
        made_progress = True
        finished_last_goal = False

        while True:
            # If we neither solved a goal nor got any new goals,
            # we loop infinitely
            if not made_progress:
                raise LoopError()

            # This is what we want to achieve next
            next_goal = self.goals[-1]

            # This is when all work is done
            if finished_last_goal:
                return self.results[next_goal]

            state = self.get_state(next_goal)
            requires = self.get_requires(next_goal)
            results = self.get_results_for(requires)

            try:
                res = state.send(results)
            except StopIteration:
                 # We might have finished the last goal ...
                if len(self.goals) > 1:
                    # ... but if it was intermediate we don't
                    # need it anymore.
                    self.goals.pop()
                else:
                    finished_last_goal = True
                continue


            # We either need to fullfill new goals ...
            if self.is_new_requires(res):
                made_progress = self.set_requires(next_goal, res)
            # ... or have a result.
            else:
                made_progress = True
                del self.requires[next_goal]
                if next_goal in self.results:
                    raise DoubleResultError()
                self.results[next_goal] = res

    def get_state(self, tc):
        if not tc in self.states:
            state = tc.task.fun(*tc.args, **tc.kwargs._asdict())
            assert isinstance(state, types.GeneratorType)
            self.states[tc] = state

        return self.states[tc]

    def get_requires(self, tc):
        if not tc in self.requires:
            self.requires[tc] = tuple()
        return self.requires[tc]

    @staticmethod
    def is_new_requires(res):
        return (isinstance(res, TaskCall)
                or (isinstance(res, types.TupleType)
                    and all((isinstance(s, TaskCall) for s in res))))

    def set_requires(self, tc, requires):
        if not isinstance(requires, types.TupleType):
            requires = (requires,)
        self.requires[tc] = requires

        # Make progress maybe
        made_progress = False
        for r in reversed(requires):
            # We already have that goal, but need to solve it
            # earlier now.
            if r in self.goals:
                self.goals.remove(r)
                self.goals.append(r)
                # But we surely made no progress, if we still need
                # a result for the original task or the task it
                # requires.
                made_progress = (tc in self.results) or (r in self.results)
            else:
                # We need to solve that goal if we did not
                # solve it earlier.
                if not r in self.results:
                    self.goals.append(r)
                # This is a new goal that is progress, or we
                # could proceed on the goal that requires it,
                # that is progress too.
                made_progress = True

        return made_progress

    def get_results_for(self, requires):
        if requires == tuple():
            return None
        if all((r in self.results for r in requires)):
            tup = tuple((self.results[r] for r in requires))
            if len(tup) == 1:
                return tup[0]
            else:
                return tup
        return None

class TaskError(RuntimeError):
    pass

class LoopError(TaskError):
    pass

class DoubleResultError(TaskError):
    pass
