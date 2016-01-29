'''
.. :py:module:: test_agent
    :platform: Unix

Tests for agent module.
'''
import unittest

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.core.rule import RuleLeaf
from creamas.core.feature import Feature
from creamas.core.artifact import Artifact
from creamas.core.mapper import Mapper


class AgentTestCase(unittest.TestCase):

    def setUp(self):
        self.env = Environment(('localhost', 5555), name='test_env')

    def tearDown(self):
        self.env.destroy()

    def test_agent(self):
        env = self.env
        a1 = CreativeAgent(env)
        a2 = CreativeAgent(env, name='test_name')
        test_agents = [a1, a2]
        a_agents = [CreativeAgent(env), CreativeAgent(env), CreativeAgent(env)]

        self.assertEqual(a1.env, env)
        self.assertEqual(a2.name, 'test_name')

        # No two agents with same name in environment.
        with self.assertRaises(ValueError):
            CreativeAgent(env, name='test_name')

        # All basic data structures have been initialized
        for a in test_agents:
            self.assertEqual(a.age, 0)
            self.assertEqual(a.max_res, 0)
            self.assertEqual(a.cur_res, 0)
            self.assertEqual(len(a.R), 0)
            self.assertEqual(type(a.R), list)
            self.assertEqual(len(a.W), 0)
            self.assertEqual(type(a.W), list)
            self.assertEqual(len(a.A), 0)
            self.assertEqual(type(a.A), list)
            self.assertEqual(type(a.D), dict)
            self.assertEqual(len(a.D.keys()), 0)
            self.assertEqual(len(a.connections), 0)
            self.assertEqual(type(a.connections), list)
            self.assertEqual(len(a.attitudes), 0)
            self.assertEqual(type(a.attitudes), list)

        a1.get_older()
        self.assertEqual(a1.age, 1)
        a1.age = 100
        self.assertEqual(a1.age, 100)
        a1.max_res = 10
        a1.cur_res = 100
        self.assertEqual(a1.max_res, a1.cur_res)
        a1.max_res = 5
        self.assertEqual(a1.max_res, a1.cur_res)
        a1.cur_res = -1
        self.assertEqual(a1.cur_res, 0)
        a1.refill()
        self.assertEqual(a1.cur_res, a1.max_res)
        a1.max_res = -1
        self.assertEqual(a1.max_res, 0)

        # adding connections works
        self.assertTrue(a1.add_connection(a_agents[0]))
        self.assertTrue(a1.add_connection(a_agents[1], 0.5))
        self.assertTrue(a1.add_connection(a_agents[2], -0.5))
        self.assertEqual(len(a1.connections), 3)
        self.assertEqual(len(a1.attitudes), 3)
        self.assertEqual(a1.get_attitude(a_agents[0]), 0.0)
        self.assertEqual(a1.get_attitude(a_agents[1]), 0.5)
        self.assertEqual(a1.get_attitude(a_agents[2]), -0.5)

        # Removing connection removes the right connection and attitude.
        a1.remove_connection(a_agents[1])
        self.assertEqual(len(a1.connections), 2)
        self.assertEqual(len(a1.attitudes), 2)
        self.assertEqual(a1.get_attitude(a_agents[0]), 0.0)
        self.assertEqual(a1.get_attitude(a_agents[2]), -0.5)
        self.assertIsNone(a1.get_attitude(a_agents[1]))

        # Set attitude works, and attitude cannot be set outside -1,1.
        a1.set_attitude(a_agents[0], 0.5)
        self.assertEqual(a1.get_attitude(a_agents[0]), 0.5)

        with self.assertRaises(AssertionError):
            a1.set_attitude(a_agents[0], -1.1)

        with self.assertRaises(AssertionError):
            a1.set_attitude(a_agents[0], -1.1)

        # Removing non-existing connection returns false
        self.assertFalse(a1.remove_connection(a_agents[1]))

        a1.set_attitude(a_agents[1], -0.5)
        self.assertIn(a_agents[1], a1.connections)
        self.assertEqual(a1.get_attitude(a_agents[1]), -0.5)

        # Cannot try to remove other than CreativeAgents
        with self.assertRaises(TypeError):
            a1.remove_connection('b')

        # connection must be subclass of CreativeAgent
        with self.assertRaises(TypeError):
            a1.add_connection('a', 0.5)

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

        # ARTIFACTS
        art = Artifact(a1, 1)
        a1.add_artifact(art)
        self.assertIn(art, a1.A)
        a1.publish(art)
        self.assertIn(art, env.artifacts[a1.name])

        with self.assertRaises(TypeError):
            a1.add_artifact(1)
