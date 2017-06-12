'''
.. py:module:: test_ds
    :platform: Unix

Tests for creamas.ds-module.
'''
import asyncio
import unittest
import multiprocessing

import aiomas

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.ds import DistributedEnvironment
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
        self.server_rets = []
        for p in self.server_ports:
            r = self.loop.run_in_executor(None, run_server, p)
            self.server_rets.append(r)

        addr = ('localhost', 5550)
        nodes = [('localhost', p) for p in self.server_ports]
        self.denv = DistributedEnvironment(addr, Environment, nodes,
                                           codec=aiomas.MsgPack)

    def tearDown(self):
        #self.loop.stop()
        self.denv.destroy(as_coro=False)


    def test_ds(self):
        spawn_cmds = ['python spawn_test_node.py --port 5560',
                      'python spawn_test_node.py --port 5570']

        ports = {('localhost', 8022): 5560, ('localhost', 8023): 5570}
        run(self.denv.spawn_slaves(spawn_cmds, ports=ports, known_hosts=None,
                                   username='test', password='test'))
        ret = run(self.denv.wait_slaves(5, check_ready=True))
        self.assertTrue(ret)
        for _ in range(8):
            ret = run(self.denv.spawn_n('denv_agent:DenvTestAgent', 10))
            self.assertEqual(len(ret), 10)

        ret = self.denv.get_agents()
        self.assertEqual(len(ret), 80)
        for r in ret:
            self.assertEqual(type(r), str)

        args = (1, 'plaa')
        kwargs = {'yep': 2, 'foo': {}}
        rets = run(self.denv.trigger_all(*args, **kwargs))
        self.assertEqual(len(rets), 80)
        for r in rets:
            self.assertEqual(r[0], args)
            self.assertEqual(r[1], kwargs)
