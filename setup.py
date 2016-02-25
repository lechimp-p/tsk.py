#
# Define tasks depending on each other and execute them.
#
# Copyright (c) 2016 Richard Klees <richard.klees@rwth-aachen.de>
#
# This software is licensed under The MIT License. You should have
# received a copy of the LICENSE with the code.
#

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = (
    { "description" : "A utility to run tasks."
    , "author" : "Richard Klees"
    , "author_email" : "richard.klees@rwth-aachen.de"
    , "version" : "0.7"
    , "install-requires" : ["nose"]
    , "packages" : ["tsk"]
    , "scripts" : []
    , "name" : "tsk"
    })

setup(**config)
