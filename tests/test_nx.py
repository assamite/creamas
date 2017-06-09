'''
.. :py:module:: test_nx
    :platform: Unix

Tests for creamas.nx-module.
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

    def test_nx_menv(self):
        self.menv = MultiEnvironment(('localhost', 5556),
                                     env_cls=Environment,
                                     mgr_cls=None)
        self.menv.spawn_slaves(slave_addrs=[('localhost', 5557),
                                            ('localhost', 5558)],
                               slave_env_cls=Environment,
                               slave_mgr_cls=EnvManager)
        run(self.menv.wait_slaves(5, check_ready=True))

        n_agents = 160
        G = networkx.fast_gnp_random_graph(n_agents, 0.4)
        agents = []
        for _ in range(n_agents):
            agent = run(self.menv.spawn('creamas.core.agent:CreativeAgent'))
            agents.append(agent)

        connections_from_graph(self.menv, G)
        G2 = graph_from_connections(self.menv, False)
        self.assertEqual(len(G2), n_agents)
        self.assertTrue(networkx.is_isomorphic(G, G2))
        self.menv.destroy()