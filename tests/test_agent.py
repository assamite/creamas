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

        self.assertEqual(a1.env, env)
        self.assertEqual(a2.name, 'test_name')
