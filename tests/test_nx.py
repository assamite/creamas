'''
.. :py:module:: test_nx
    :platform: Unix

Basic test for creamas.nx-module.

Multi-environment and distributed environment testing are done in their
respective testing modules.
'''
import asyncio
import unittest
import random

import networkx

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.nx import connections_from_graph, graph_from_connections


def edge_sim(e1, e2):
    return e1 == e2


class NXTestCase(unittest.TestCase):

    def setUp(self):
        self.env = Environment.create(('localhost', 5555))
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.env.close()

    def test_nx_asserts(self):
        n_agents = 40
        G = networkx.fast_gnp_random_graph(n_agents + 1 , 0.4)
        for _ in range(n_agents):
            agent = CreativeAgent(self.env)

        with self.assertRaises(ValueError):
            connections_from_graph(self.env, G)

        with self.assertRaises(TypeError):
            connections_from_graph(self.env, [(1, 2), (3, 4)])

        with self.assertRaises(TypeError):
            connections_from_graph(CreativeAgent, G)

    def test_nx_env(self):
        for _ in range(50):
            env = Environment.create(('localhost', 5556))
            n_agents = random.randint(10, 60)
            G = networkx.fast_gnp_random_graph(n_agents, 0.4)
            for _ in range(n_agents):
                CreativeAgent(env)

            connections_from_graph(env, G)
            G2 = graph_from_connections(env, directed=False)
            self.assertEqual(len(G2), n_agents)
            self.assertTrue(networkx.is_isomorphic(G, G2))
            env.close()

    def test_nx_env_weighted(self):
        for _ in range(50):
            env = Environment.create(('localhost', 5556))
            n_agents = random.randint(10, 60)
            G = networkx.fast_gnp_random_graph(n_agents, 0.4)
            for _ in range(n_agents):
                CreativeAgent(env)

            for edge in G.edges_iter(data=True):
                edge[2]['weight'] = random.random()

            connections_from_graph(env, G, edge_data=True)
            G2 = graph_from_connections(env, directed=False)
            self.assertEqual(len(G2), n_agents)
            self.assertTrue(networkx.is_isomorphic(G, G2, edge_match=edge_sim))
            env.close()

    def test_nx_env_directed(self):
        for _ in range(50):
            env = Environment.create(('localhost', 5556))
            n_agents = random.randint(10, 60)
            G = networkx.gnc_graph(n_agents)
            for _ in range(n_agents):
                CreativeAgent(env)

            connections_from_graph(env, G)
            G2 = graph_from_connections(env, directed=True)
            self.assertEqual(len(G2), n_agents)
            self.assertTrue(networkx.is_isomorphic(G, G2))
            self.env.clear_connections()
            env.close()

    def test_nx_env_directed_weighted(self):
        for _ in range(50):
            env = Environment.create(('localhost', 5556))
            n_agents = random.randint(10, 60)
            G = networkx.gnc_graph(n_agents)
            for _ in range(n_agents):
                CreativeAgent(env)

            for edge in G.edges_iter(data=True):
                edge[2]['weight'] = random.random()

            connections_from_graph(env, G, edge_data=True)
            G2 = graph_from_connections(env, directed=True)
            self.assertEqual(len(G2), n_agents)
            self.assertTrue(networkx.is_isomorphic(G, G2, edge_match=edge_sim))
            env.close()