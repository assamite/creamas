'''
.. :py:module:: test_nx
    :platform: Unix

Basic test for creamas.nx-module.

Multi-environment and distributed environment testing are done in their
respective testing modules.
'''
import asyncio
import unittest

import networkx

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.mp import MultiEnvironment, EnvManager
from creamas.nx import connections_from_graph, graph_from_connections
from creamas.util import run

class NXTestCase(unittest.TestCase):

    def setUp(self):
        self.env = Environment.create(('localhost', 5555))
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.env.destroy()

    def test_nx_env(self):
        n_agents = 40
        G = networkx.fast_gnp_random_graph(n_agents, 0.4)
        agents = []
        for _ in range(n_agents):
            agent = CreativeAgent(self.env)
            agents.append(agent)

        connections_from_graph(self.env, G)
        G2 = graph_from_connections(self.env, False)
        self.assertEqual(len(G2), n_agents)
        self.assertTrue(networkx.is_isomorphic(G, G2))
