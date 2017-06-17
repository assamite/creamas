'''
.. :py:module:: test_agent
    :platform: Unix

Tests for agent module.
'''
import asyncio
import unittest
import logging

import aiomas

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.core.rule import RuleLeaf
from creamas.core.feature import Feature
from creamas.core.artifact import Artifact
from creamas.core.mapper import Mapper

from creamas.logging import ObjectLogger


class AgentTestCase(unittest.TestCase):

    def setUp(self):
        self.env = Environment.create(('localhost', 5555))
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.env.destroy()

    def test_agent(self):
        env = self.env
        a1 = CreativeAgent(env)
        a2 = CreativeAgent(env, name='test_name')
        test_agents = [a1, a2]
        a_agents = [CreativeAgent(env), CreativeAgent(env), CreativeAgent(env)]
        b_agents = [CreativeAgent(env), CreativeAgent(env), CreativeAgent(env)]

        self.assertEqual(a1.env, env)
        self.assertEqual(a1.name, 'tcp://localhost:5555/0')
        self.assertEqual(a1.sanitized_name(), 'tcp_localhost_5555_0')
        self.assertEqual(a2.name, 'test_name')

        # All basic data structures have been initialized
        for a in test_agents:
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
            self.assertEqual(len(a.connections.keys()), 0)
            self.assertEqual(type(a.connections), dict)
            self.assertIsNone(a.logger)
            self.assertEqual(a.qualname(), 'creamas.core.agent:CreativeAgent')

        a3 = CreativeAgent(env, name='log_test', log_folder='test_folder',
                           log_level=logging.DEBUG)
        self.assertEqual(type(a3.logger), ObjectLogger)

        a2.name = 'plop'
        self.assertEqual(a2.name, 'plop')

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
        self.assertTrue(a1.add_connection(a_agents[0].addr))
        self.assertTrue(a1.add_connection(a_agents[1].addr))
        self.assertTrue(a1.add_connection(a_agents[2].addr))
        self.assertEqual(len(a1.connections.keys()), 3)

        # adding existing connection returns False
        self.assertFalse(a1.add_connection(a_agents[0].addr))

        # Removing connection removes the right connection and attitude.
        a1.remove_connection(a_agents[1].addr)
        self.assertEqual(len(a1.connections.keys()), 2)

        # Adding connections in a bunch works
        a1.add_connections([(b.addr, {'foo': 'bar'}) for b in b_agents])
        self.assertEqual(len(a1.connections.keys()), 5)

        # Removing non-existing connection returns false
        self.assertFalse(a1.remove_connection(a_agents[1].addr))

        # Connecting to a random agent in connections works and returns a Proxy
        ret = self.loop.run_until_complete(a1.random_connection())
        self.assertTrue(type(ret), aiomas.rpc.Proxy)

        # connect shortcut works and returns a Proxy
        ret = self.loop.run_until_complete(a1.connect(list(a1.connections.keys())[0]))
        self.assertTrue(type(ret), aiomas.rpc.Proxy)

        # other agents can get other agents connections
        r_agent = self.loop.run_until_complete(a2.connect(a1.addr))
        conns = self.loop.run_until_complete(r_agent.get_connections())
        for c in conns:
            self.assertIn(c, a1.connections)

        # Getting data also works for other agents connections
        r_agent = self.loop.run_until_complete(a2.connect(a1.addr))
        conns = self.loop.run_until_complete(r_agent.get_connections(True))
        for c, d in conns.items():
            self.assertIn(c, list(a1.connections.keys()))
            self.assertTrue(type(d), dict)

        # Default act raises error
        with self.assertRaises(NotImplementedError):
            self.loop.run_until_complete(a1.act())

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
        arts = self.loop.run_until_complete(self.env.get_artifacts(a1))
        self.assertIn(art, arts)

        with self.assertRaises(TypeError):
            a1.add_artifact(1)
