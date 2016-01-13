import functools

class task(object):
    """
    Turn an ordinary generator of tasks to a task.
    """
    def __init__(self, fun):
        self.fun = fun

        functools.update_wrapper(self, fun)

class LoopError(RuntimeError):
    pass

