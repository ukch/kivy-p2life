""" Doctests for kivy-p2life """

import doctest
import sys
import unittest

import mock

MODULES_WITH_DOCTESTS = [
    "kivy_grid_cells.widgets",
    "kivy_p2life.widgets",
    "kivy_p2life.gol",
    "main",
]

def load_tests(loader, tests, ignore):
    for name in MODULES_WITH_DOCTESTS:
        tests.addTests(doctest.DocTestSuite(name))
    return tests

if __name__ == "__main__":
    # Kivy hijacks the argv so we need to clear it
    argv = sys.argv[:]
    sys.argv = sys.argv[:1]

    with mock.patch("kivy.base.EventLoopBase.ensure_window"):
        unittest.main(argv=argv)
