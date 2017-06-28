'''
.. :py:module:: test_rules
    :platform: Unix

Tests for rules-package
'''
import asyncio
import unittest

from creamas.rules.feature import Feature
from creamas.rules.mapper import Mapper

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.rules.rule import RuleLeaf, Rule
from creamas.rules.agent import RuleAgent


class RulesTestCase(unittest.TestCase):

    def setUp(self):
        self.env = Environment.create(('localhost', 5555))
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.env.destroy()

    def test_rules(self):
        env = self.env
        a1 = RuleAgent(env)

        self.assertEqual(len(a1.R), 0)
        self.assertEqual(type(a1.R), list)
        self.assertEqual(len(a1.W), 0)
        self.assertEqual(type(a1.W), list)

        # FEATURES
        # feature must be subclass of Feature
        with self.assertRaises(TypeError):
            a1.add_rule({}, 1.0)

        f = Feature('test_feat', {float}, float)
        f2 = Feature('test_feat2', {float}, float)
        rule = RuleLeaf(f, Mapper())
        rule2 = RuleLeaf(f2, Mapper())
        self.assertTrue(a1.add_rule(rule, 1.0))
        self.assertIn(rule, a1.R)
        a1.set_weight(rule, 0.0)
        self.assertEqual(a1.get_weight(rule), 0.0)
        self.assertIsNone(a1.get_weight(rule2))
        a1.set_weight(rule2, 1.0)
        self.assertIn(rule2, a1.R)
        self.assertEqual(a1.get_weight(rule2), 1.0)

        with self.assertRaises(TypeError):
            a1.get_weight(1)

        with self.assertRaises(TypeError):
            a1.set_weight(1, 0.0)

        with self.assertRaises(TypeError):
            a1.remove_rule(1)

        self.assertTrue(a1.remove_rule(rule))
        self.assertNotIn(rule, a1.R)
        self.assertEqual(1, len(a1.R))
        self.assertEqual(1, len(a1.W))
        self.assertEqual(a1.get_weight(rule2), 1.0)
        self.assertFalse(a1.remove_rule(rule))
