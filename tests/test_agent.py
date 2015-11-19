'''
.. :py:module:: test_agent
    :platform: Unix

Tests for agent module.
'''
import unittest

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment


class TestAgent(unittest.TestCase):

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
            self.assertEqual(len(a.F), 0)
            self.assertEqual(type(a.F), list)
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

        # adding connections works
        a1.add_connection(a_agents[0])
        a1.add_connection(a_agents[1], 0.5)
        a1.add_connection(a_agents[2], -0.5)
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
