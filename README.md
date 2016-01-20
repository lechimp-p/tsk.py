[![Build Status](https://travis-ci.org/lechimp-p/tsk.svg?branch=master)](https://travis-ci.org/lechimp-p/task)

# tsk.py

** Define tasks depending on each other and execute them. **

Sometime you have a plethora of tasks, depending on each other, were you want
to execute the single tasks only once, but reuse the results in multiple places.
For me that situation occured when writing a static page generator. I wanted to
generate pages automatically when they were required via a link in another page,
but then i only wanted to generate them once. I could have solved it with a
cache or something, but i might have found a slightly more general and maybe
neater approach.

# Example using some Stubs

```py

from tsk import * # Only exports task and LoopError

# Create some generators and decorate them.

@task
def read_config(path):
    # Yield results
    yield { "pages" : ["one", "two"] }

@task
def generate_index():
    # Or yield new tasks, we want to accomplish and use
    # the results
    config = yield read_config("foo.ini")
    for p in config.pages:
        url = yield make_page(p)

        # Render url or something...
        pass

    yield "index.html"
         
     

```

# What's next?

I actually try to use this for my page generator. I might be adding some logging
and error facility to show a nested view of where things went wrong.
