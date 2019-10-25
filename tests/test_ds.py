'''
.. py:module:: test_ds
    :platform: Unix

Tests for creamas.ds-module.
'''
import asyncio
import unittest
# import multiprocessing

import aiomas

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.ds import DistributedEnvironment, ssh_exec
from creamas.util import run

from ssh_server import run_server

class DenvTestAgent(CreativeAgent):

    @aiomas.expose
    async def act(self, *args, **kwargs):
        return args, kwargs

class DenvTestCase(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.server_ports = [8022, 8023]
        addr = ('localhost', 5550)
        nodes = [('localhost', p) for p in self.server_ports]
        self.denv = DistributedEnvironment(addr, Environment, nodes,
                                           codec=aiomas.MsgPack)

    def tearDown(self):
        self.denv.close(as_coro=False)

    def test_ssh_conn(self):
        self.loop.run_in_executor(None, run_server, 8024)
        run(asyncio.sleep(1.0))
        r = run(ssh_exec('localhost', 'echo Hello!', port=8024,
                         username='test', password='test', known_hosts=None))
        self.assertEqual(r.stdout, 'Hello!\n')


    def test_ds(self):
        self.server_rets = []
        for p in self.server_ports:
            r = self.loop.run_in_executor(None, run_server, p)
            self.server_rets.append(r)
        run(asyncio.sleep(1.0))
        spawn_cmds = ['python spawn_test_node.py --port 5560',
                      'python spawn_test_node.py --port 5570']

        ports = {('localhost', 8022): 5560, ('localhost', 8023): 5570}
        run(self.denv.spawn_nodes(spawn_cmds, ports=ports, known_hosts=None,
                                  username='test', password='test'))
        ret = run(self.denv.wait_nodes(5, check_ready=True))
        self.assertTrue(ret)
        for _ in range(8):
            ret = run(self.denv.spawn_n('denv_agent:DenvTestAgent', 10))
            self.assertEqual(len(ret), 10)

        # Test that get_slave_managers returns all true slave manager addresses
        # That is, the addresses of the "real" slave environment managers, not
        # multi-environment managers.
        managers = self.denv.get_slave_managers()
        self.assertEqual(len(managers), 8)
        expected_addrs = ['tcp://localhost:5561/0',
                          'tcp://localhost:5562/0',
                          'tcp://localhost:5563/0',
                          'tcp://localhost:5564/0',
                          'tcp://localhost:5571/0',
                          'tcp://localhost:5572/0',
                          'tcp://localhost:5573/0',
                          'tcp://localhost:5574/0']
        for maddr in managers:
            self.assertIn(maddr, expected_addrs)

        # Test that get_agents retrieves all the agents (excluding managers)
        ret = self.denv.get_agents()
        self.assertEqual(len(ret), 80)
        for r in ret:
            self.assertEqual(type(r), str)

        # Test that trigger all is actually triggered for all agents and all
        # agents get the args and kwargs
        args = (1, 'plaa')
        kwargs = {'yep': 2, 'foo': {}}
        rets = run(self.denv.trigger_all(*args, **kwargs))
        self.assertEqual(len(rets), 80)
        for r in rets:
            self.assertEqual(r[0], args)
            self.assertEqual(r[1], kwargs)

        n_agents = len(rets)

        # Test that creating connections from a graph work for
        # distributed environments
        import networkx
        from creamas.nx import connections_from_graph, graph_from_connections
        G = networkx.fast_gnp_random_graph(n_agents, 0.4)
        connections_from_graph(self.denv, G)
        G2 = graph_from_connections(self.denv, False)
        self.assertEqual(len(G2), n_agents)
        self.assertTrue(networkx.is_isomorphic(G, G2))
