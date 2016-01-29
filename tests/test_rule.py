'''
.. :py:module:: test_rule

Tests for rule module.
'''
import unittest

from creamas.core.artifact import Artifact
from creamas.core.rule import Rule, RuleLeaf
from creamas.core.feature import Feature
from creamas.mappers import BooleanMapper
from creamas.features import ModuloFeature


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

        mf = ModuloFeature(5)
        mf2 = ModuloFeature(10)
        mf3 = ModuloFeature(9)
        m3 = BooleanMapper(mode='10')
        rl1 = RuleLeaf(mf, m1)
        rl2 = RuleLeaf(mf2, m2)
        rl3 = RuleLeaf(mf3, m3)
        rule = Rule([rl1, rl2, rl3], [1.0, 1.0, 1.0])
        ar = Artifact(d, 20)
        ar.domain = int
        self.assertAlmostEqual(rule(ar), 0.6666666666666666)
        rule = Rule([rl1, rl2, rl3], [-1.0, 1.0, 1.0])
        self.assertAlmostEqual(rule(ar), 0.0)
        rule = Rule([rl1, rl2, rl3], [1.0, 1.0, -1.0])
        self.assertAlmostEqual(rule(ar), 0.6666666666666666)
        rule = Rule([rl1, rl2, rl3], [1.0, 1.0, 0.0])
        self.assertAlmostEqual(rule(ar), 1.0)
        rule = Rule([rl1, rl2, rl3], [0.0, 1.0, 1.0])
        self.assertAlmostEqual(rule(ar), 0.5)
        m4 = BooleanMapper(mode='1-1')
        rl4 = RuleLeaf(mf3, m4)
        rule = Rule([rl1, rl2, rl4], [1.0, 1.0, -1.0])
        self.assertAlmostEqual(rule(ar), 1.0)
