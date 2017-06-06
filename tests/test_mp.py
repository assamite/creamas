'''
.. :py:module:: test_mp
    :platform: Unix

Tests for creamas.mp-module.
'''
import asyncio
import unittest

import aiomas

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.mp import MultiEnvironment, EnvManager, MultiEnvManager
from creamas.util import run, split_addrs

class MenvTestAgent(CreativeAgent):

    @aiomas.expose
    async def act(self, *args, **kwargs):
        return args, kwargs

class MenvTestCase(unittest.TestCase):

    def setUp(self):
        self.menv = MultiEnvironment(('localhost', 5555),
                                     env_cls=Environment,
                                     mgr_cls=MultiEnvManager,
                                     slave_addrs=[('localhost', 5556),
                                                  ('localhost', 5557),
                                                  ('localhost', 5558),
                                                  ('localhost', 5559)],
                                     slave_env_cls=Environment,
                                     slave_mgr_cls=EnvManager)
        run(self.menv.wait_slaves(5, check_ready=True))
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.menv.destroy()

    def test_menv(self):
        n_agents = 40

        self.assertEqual(self.menv.artifacts, [])
        self.assertEqual(self.menv.candidates, [])
        ready = run(self.menv.is_ready())
        self.assertEqual(ready, True)

        # Test setting host managers
        async def check_host_manager(addr):
            r_manager = await self.menv.connect(addr)
            return await r_manager.host_manager()

        ret = run(self.menv.set_host_managers(5))
        for addr in self.menv.addrs:
            ret = run(check_host_manager(addr))
            self.assertEqual(self.menv.manager.addr, ret)

        # There are no initial agents even though managers have been created.
        agents = self.menv.get_agents()
        self.assertEqual(len(agents), 0)

        # Test spawn
        for _ in range(n_agents):
            run(self.menv.spawn('test_mp:MenvTestAgent'))

        agents = self.menv.get_agents(addr=True)
        self.assertEqual(len(agents), n_agents)

        # Test that spawn divides agents equally to the slave environments
        split_agents = split_addrs(agents)
        for host, values in split_agents.items():
            for port, addrs in values.items():
                self.assertEqual(len(addrs), 10)

        n_agents2 = 10
        run(self.menv.spawn_n('test_mp:MenvTestAgent', n_agents2))
        agents = self.menv.get_agents(addr=True)
        self.assertEqual(len(agents), n_agents + n_agents2)

        # Test that triggerl
        args = ('plop', 10)
        kwargs = {'foo': 'bar', 'yep': 2}
        ret = run(self.menv.trigger_all(*args, **kwargs))
        self.assertEqual(len(ret), n_agents + n_agents2)
        for r in ret:
            c_args, c_kwargs = r
            self.assertEqual(args, c_args)
            self.assertEqual(kwargs, c_kwargs)
