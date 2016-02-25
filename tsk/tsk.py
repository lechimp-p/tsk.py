#
# Define tasks depending on each other and execute them.
#
# Copyright (c) 2016 Richard Klees <richard.klees@rwth-aachen.de>
#
# This software is licensed under The MIT License. You should have
# received a copy of the LICENSE with the code.
#

import functools
import types
from collections import namedtuple


# BASIC INTERFACE

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
    A call to a task. You can run this.
    """
    def __init__(self, task, args, kwargs):
        self.task = task
        self.args = args
        tup = namedtuple("Kwargs", kwargs.keys())
        self.kwargs = tup(**kwargs)

    def run(self, log = None):
        """
        Run this task.

        You may provide a logger function that retreives LoggerEntries during
        execution.
        """
        vm = VM(self, log)
        return vm.result()

    def __hash__(self):
        return hash((self.task, self.args, self.kwargs))

    def __eq__(self, other):
        if other is None:
            return False
        return ((self.task, self.args, self.kwargs)
                == (other.task, other.args, other.kwargs))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<call to task %s at %s>" % (self.task.__repr__(), hex(id(self)))


# ERRORS

class TaskError(RuntimeError):
    """ General error from this library. """
    pass

class LoopError(TaskError):
    """ Tasks require results in a circular way. """
    pass

class DoubleResultError(TaskError):
    """ A task announced two results. """
    pass


# LOGGING

class ConsoleLogger(object):
    """
    A very basic logger. Use this like

        make_foo.run(log = ConsoleLogger())

    or customize it to your needs (or even write your own one and contribute it).
    """
    entered_color = "white"
    error_color = "red"
    completed_color = "green"
    use_result_color = "blue"
    indentation = "    "

    def __init__(self, pr = None):
        from termcolor import colored
        self.colored = colored

        if pr is None:
            def pr(s):
                print(s)
        self.pr = pr
        self.level = 0
        self.last = None
        self.first_task_call = None

    def __call__(self, msg):
        # We defer the printing of the messages to be able to react to tasks
        # that don't require results from other tasks. This is a bit tricky...

        # We need to know the first task to not defer the printing of the last
        # entry to the log.
        if self.first_task_call is None:
            self.first_task_call = msg.task_call

        # We need to know the last entry to be able to print it later on.
        if self.last is None:
            self.last = msg
            return

        # We need to know some facts about the last and the current task to
        # be able to react correctly and get the indentation right.
        last_entered = isinstance(self.last, EnteredTask)
        last_completed = isinstance(self.last, CompletedTask)
        cur_completed = isinstance(msg, CompletedTask)

        # this happens when a task doe not invoke subtasks
        if last_entered and cur_completed and self.last.task_call == msg.task_call:
            self.print_msg(msg)
            self.last = None
        else:
            if last_completed:
                self.level -= 1

            self.print_msg(self.last)

            if last_entered:
                self.level += 1

            self.last = msg

        # this happens when the first task completes
        if cur_completed and self.first_task_call == msg.task_call:
            self.level -= 1
            self.print_msg(msg)

    def print_msg(self, msg):
        if isinstance(msg, EnteredTask):
            color = self.entered_color
        elif isinstance(msg, CompletedTask):
            color = self.completed_color
        elif isinstance(msg, UseResultOfTask):
            color = self.use_result_color
        #elif isinstance(msg, EnteredTask):
        #    color = self.entered_color
        else:
            raise RuntimeError("Unknown message: %s" % msg)

        ind = self.indentation * self.level
        txt = self.format_msg(msg)

        self.pr(self.colored(ind + txt, color))

    def format_msg(self, msg):
        return msg.task.__name__


class LogEntry(object):
    """
    An entry send to TaskCall.run()s log parameter.

    This is the base class, the classes below are used for signalling concrete
    facts.
    """
    def __init__(self, task_call, dependency_chain):
        self.task_call = task_call
        self.dependency_chain = dependency_chain

    @property
    def task(self):
        return self.task_call.task

    @property
    def args(self):
        return self.task_call.args

    @property
    def dependents(self):
        return self.dependency_chain

class EnteredTask(LogEntry):
    """ The runner entered a task. """
    pass

class CompletedTask(LogEntry):
    """ A task was completed. """
    pass

class UseResultOfTask(LogEntry):
    """ The result of a task was reused. """
    pass


# EXECUTION

class VM(object):
    """
    This is the machine that runs the tasks and manages the results.
    """
    def __init__(self, tc, log):
        self.tc = tc
        self.log = (lambda x: None) if log is None else log

        self.results = {}       # results that are already known
        self.states = {}        # current states of task calls
        self.requires = {}      # requirement to advance state of task calls
        self.goals = [self.tc]  # we start with one single goal and stack
                                # futures goals above
        self.last_goal = None   # holds the last goal we accomplished (for logging)

    def result(self):
        made_progress = True
        finished_last_goal = False

        self.log(EnteredTask(self.tc, []))

        while True:
            # If we neither solved a goal nor got any new goals,
            # we loop infinitely
            if not made_progress:
                raise LoopError()

            # This is what we want to achieve next
            next_goal = self.goals[-1]

            # This is when all work is done
            if finished_last_goal:
                self.log(CompletedTask(self.tc, []))
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
                    tc = self.goals[-1]
                    deps = self.get_dependents_of(tc)
                    self.goals.pop()
                    self.log(CompletedTask(tc, deps))
                    self.last_goal = tc
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
                or (isinstance(res, tuple)
                    and all((isinstance(s, TaskCall) for s in res))))

    def set_requires(self, tc, requires):
        if not isinstance(requires, tuple):
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
                made_progress = made_progress or (tc in self.results) or (r in self.results)
            else:
                # We need to solve that goal if we did not
                # solve it earlier.
                if not r in self.results:
                    self.goals.append(r)
                    self.log(EnteredTask(r, self.get_dependents_of(r)))
                # This is a new goal that is progress, or we
                # could proceed on the goal that requires it,
                # that is progress too.
                made_progress = True

        return made_progress

    def get_dependents_of(self, tc):
        if self.goals[-1] == tc:
            return self.goals[0:-1]
        else:
            return self.goals

    def get_results_for(self, requires):
        if requires == tuple():
            return None
        if all((r in self.results for r in requires)):
            _tup = []
            for r in requires:
                _tup.append(self.results[r])
                if self.last_goal != r:
                    self.log(UseResultOfTask(r, self.get_dependents_of(r)))
                else:
                    self.last_goal = None
            tup = tuple(_tup)
            if len(tup) == 1:
                return tup[0]
            else:
                return tup
        return None
