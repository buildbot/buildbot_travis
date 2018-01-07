from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from twisted.trial import unittest
from buildbot_travis.safe_eval import safe_eval


class SafeEvalTests(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(safe_eval("1", {}), 1)

    def test_local(self):
        self.assertEqual(safe_eval("a", {'a': 2}), 2)

    def test_local_bool(self):
        self.assertEqual(safe_eval("a==2", {'a': 2}), True)

    def test_lambda(self):
        self.assertRaises(ValueError, safe_eval, "lambda : None", {'a': 2})

    def test_bad_name(self):
        self.assertRaises(ValueError, safe_eval, "a == None2", {'a': 2})

    def test_attr(self):
        self.assertRaises(ValueError, safe_eval, "a.__dict__", {'a': 2})

    def test_eval(self):
        self.assertRaises(ValueError, safe_eval, "eval('os.exit()')", {})

    def test_exec(self):
        self.assertRaises(SyntaxError, safe_eval, "exec 'import os'", {})

    def test_multiply(self):
        self.assertRaises(ValueError, safe_eval, "'s' * 3", {})

    def test_power(self):
        self.assertRaises(ValueError, safe_eval, "3 ** 3", {})

    def test_comprehensions(self):
        self.assertRaises(ValueError, safe_eval, "[i for i in [1,2]]", {'i': 1})
