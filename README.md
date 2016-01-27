[![Build Status](https://travis-ci.org/lechimp-p/tsk.svg?branch=master)](https://travis-ci.org/lechimp-p/task)

# tsk.py

**Define tasks depending on each other and execute them.**

Sometime you have a plethora of tasks, depending on each other, were you want
to execute the single tasks only once, but reuse the results in multiple places.
For me that situation occured when writing a static page generator. I wanted to
generate pages automatically when they were required via a link in another page,
but then i only wanted to generate them once. I could have solved it with a
cache or something, but i might have found a slightly more general and maybe
neater approach.

# Example using some Stubs

```py

from tsk import * # Only exports task

# For demonstration purpose.
rendered_pages = set()

# Create some generators and decorate them.

@task
def read_config(path):
    # Yield results ...
    yield { "pages" : ["one", "two"] }

@task
def make_index():
    # or yield new tasks we need to accomplish and get
    # their results.
    config = yield read_config("foo.ini")

    for p in config["pages"]:
        # If you look closely you will see in make_page, that
        # this would loop and we would call make_index multiple
        # times. But read on in make_page...
        url = yield make_page(p)

        # You would render the url here or something...
        rendered_pages.add("index")

    # We return the url of the page we rendered.
    yield "index.html"

@task
def make_page(page):
    # We return the url of the rendered page here early, to not run
    # in the lock i mentioned earlier. I would do this as well in
    # in make_index in reality, but i defered that trick for dramatic
    # purpose.

    yield "pages/%s.html" % page

    # The task will go on even if it returned a result earlier on.

    # And we could still retreive the result from make_index. If there
    # is a re
    index_url = make_index()

    rendered_pages.add(page)

# Then just run the task.
make_index().run()

# The engine ensures, that each task only runs once for every distinct
# combination of arguments to it.
assert rendered_pages ==  {"index", "one", "two"}

```

# What's next?

I actually try to use this for my page generator. I might be adding some logging
and error facility to show a nested view of where things went wrong. To achieve
this is might introduce some notion of environment the tasks run in.
