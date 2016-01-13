try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config =
    { "description" : "A utility to run tasks."
    , "author" : "Richard Klees"
    , "author_email" : "richard.klees@rwth-aachen.de"
    , "version" : "1.0"
    , "install-requires" : ["nose"]
    , "packages" : ["tsk"]
    , "scripts" : []
    , "name" : "tsk"
    }

setup(**config)
