'''
.. :py:module:: test_rule

Tests for rule module.
'''
import unittest

from creamas.core.artifact import Artifact
from creamas.core.rule import Rule, RuleLeaf
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
        m1 = BooleanMapper(mode='10')
        m2 = BooleanMapper(mode='10')
        rl1 = RuleLeaf(f, m1)
        rl2 = RuleLeaf(f2, m2)
        self.assertEqual(rl1.feat, f)
        self.assertEqual(rl1.mapper, m1)
        self.assertEqual(rl2.feat, f2)
        self.assertEqual(rl2.mapper, m2)
        r = Rule([rl1, rl2], [1.0, 1.0])
        self.assertSetEqual({bool, int}, r.domains)
        self.assertIn(rl1, r.R)
        self.assertIn(rl2, r.R)

        d = DummyAgent()
        ar = Artifact(d, True)
        ret = r(ar)
        self.assertIsNone(ret)
        ar.domain = bool
        ret = r(ar)
        self.assertEqual(ret, 1.0)

        with self.assertRaises(TypeError):
            r = Rule([f, rl1], [0.1, 1.0])
