'''
.. :py:module:: test_rule

Tests for rule module.
'''
import unittest

from creamas.core.rule import Rule
from creamas.core.feature import Feature
from creamas.mappers import LinearMapper


class RuleTestCase(unittest.TestCase):

    def test_rule(self):
        f = Feature('test1', {int}, bool)
        f2 = Feature('test2', {int, float}, bool)
        r = Rule([f, f2], [0.3, 0.5])
        m1 = LinearMapper(-1, 1)
        m2 = LinearMapper(-10, 10)
        r.mappers = [m1, m2]
        self.assertSetEqual({int, float}, r.domains)
        self.assertIn(f, r.F)
        self.assertIn(f2, r.F)
        self.assertIn(m1, r.mappers)
        self.assertIn(m2, r.mappers)
