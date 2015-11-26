'''
.. :py:module:: test_rule

Tests for rule module.
'''
import unittest

from creamas.core.artifact import Artifact
from creamas.core.rule import Rule
from creamas.core.feature import Feature
from creamas.mappers import BooleanMapper


class DummyFeature(Feature):

    def __init__(self, name, domains, rtype):
        super().__init__(name, domains, rtype)

    def extract(self, artifact):
        return artifact.obj


class DummyAgent():
    name = 'foo'


class RuleTestCase(unittest.TestCase):

    def test_rule(self):
        f = DummyFeature('test1', {bool, int}, bool)
        f2 = DummyFeature('test2', {bool}, bool)
        r = Rule([f, f2], [1.0, 1.0])
        m1 = BooleanMapper(mode='10')
        m2 = BooleanMapper(mode='10')
        r.mappers = [m1, m2]
        self.assertSetEqual({bool, int}, r.domains)
        self.assertIn(f, r.F)
        self.assertIn(f2, r.F)
        self.assertIn(m1, r.mappers)
        self.assertIn(m2, r.mappers)

        d = DummyAgent()
        ar = Artifact(d, True)
        ret = r(ar)
        self.assertIsNone(ret)
        ar.domain = bool
        ret = r(ar)
        self.assertEqual(ret, 1.0)

        with self.assertRaises(TypeError):
            r = Rule([1, f], [0.1, 1.0])

        r = Rule([f, f2], [1.0, 1.0])
        with self.assertRaises(ValueError):
            r.mappers = [m1]
