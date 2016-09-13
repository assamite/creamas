'''
.. :py:module:: test_simulation
    :platform: Unix

Tests for environment module.
'''
import unittest
from random import choice

import aiomas

from creamas.core.agent import CreativeAgent
from creamas.core.artifact import Artifact
from creamas.core.environment import Environment


class TestEnvironment(unittest.TestCase):

    def test_environment(self):
        env = Environment(('localhost', 5555), name='test_env')

        self.assertEqual(env.container.__class__, aiomas.Container)
        self.assertEqual(env.name, 'test_env')

        # create some get_agents to environment
        get_agents = []
        for i in range(20):
            get_agents.append(CreativeAgent(env))

        # see that all get_agents are actually in environment
        env_agents = env.get_agents
        for a in get_agents:
            self.assertIn(a, env_agents)

        for i in range(1000):
            a = choice(env_agents)
            r = env.get_random_agent(a)
            # Random agent cannot be the same as the agent calling
            self.assertNotEqual(a, r)

        for a in get_agents:
            r = env.get_agent(a.name)
            self.assertEqual(a, r)

        conns = 6
        env.create_initial_connections(n=conns)
        for a in get_agents:
            a_conns = a.connections
            # all get_agents get enough random connections
            self.assertEqual(len(a_conns), conns)
            # all connections are different
            self.assertEqual(len(a_conns), len(set(a_conns)))
            # agent cannot have itself in connections
            self.assertNotIn(a, a_conns)

        a = get_agents[0]
        arts = []
        for i in range(5):
            ar = Artifact(a, i)
            arts.append(ar)
            env.add_artifact(ar)

        for a in arts:
            self.assertIn(a, env.get_artifacts(get_agents[0]))

        env.destroy()
        # destroy should shutdown aiomas.Container -> no _tcp_server anymore
        self.assertIsNone(env.container._tcp_server)
