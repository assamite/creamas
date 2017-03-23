'''
.. :py:module:: test_simulation
    :platform: Unix

Tests for environment module.
'''
import asyncio
import unittest
from random import choice

import aiomas

from creamas.core.agent import CreativeAgent
from creamas.core.artifact import Artifact
from creamas.core.environment import Environment


class TestEnvironment(unittest.TestCase):

    def setUp(self):
        self.env = Environment.create(('localhost', 5555))
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.env.destroy()

    def test_environment(self):
        self.assertTrue(issubclass(self.env.__class__, aiomas.Container))

        # create some agents to environment
        agents = []
        for i in range(20):
            agents.append(CreativeAgent(self.env))

        # see that all get_agents are actually in environment
        env_agents = self.env.get_agents(address=False)
        for a in agents:
            self.assertIn(a, env_agents)

        for i in range(1000):
            a = choice(env_agents)
            r = self.env.get_random_agent(a)
            # Random agent cannot be the same as the agent calling
            self.assertNotEqual(a, r)

        conns = 6
        self.env.create_initial_connections(n=conns)
        for a in agents:
            a_conns = a.connections
            # all get_agents get enough random connections
            self.assertEqual(len(a_conns), conns)
            # all connections are different
            self.assertEqual(len(a_conns), len(set(a_conns)))
            # agent cannot have itself in connections
            self.assertNotIn(a, a_conns)

        a = agents[0]
        arts = []
        for i in range(5):
            ar = Artifact(a, i)
            arts.append(ar)
            self.env.add_artifact(ar)

        e = self.env.get_artifacts(agents[0])
        env_arts = self.loop.run_until_complete(e)
        for a in arts:
            self.assertIn(a, env_arts)

        # destroy should shutdown aiomas.Container -> no _tcp_server anymore
        self.env.destroy()
        self.assertIsNone(self.env._tcp_server)
