'''
.. :py:module:: test_simulation
    :platform: Unix

Tests for environment module.
'''
import asyncio
import unittest
from random import choice, random

import aiomas

from creamas.core.agent import CreativeAgent
from creamas.core.artifact import Artifact
from creamas.core.environment import Environment


class CreativeTestAgent(CreativeAgent):
    @aiomas.expose
    async def act(self, *args, **kwargs):
        return args, kwargs


class TestEnvironment(unittest.TestCase):

    def setUp(self):
        self.env = Environment.create(('localhost', 5555))
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.env.destroy()

    def test_environment(self):
        self.assertTrue(issubclass(self.env.__class__, aiomas.Container))
        n_agents = 20

        # create some agents to environment
        agents = []
        for i in range(n_agents):
            agents.append(CreativeAgent(self.env))

        # see that all get_agents are actually in environment
        env_agents = self.env.get_agents(addr=False)
        self.assertEqual(len(env_agents), n_agents)
        for a in agents:
            self.assertIn(a, env_agents)

        # Check that addr-parameter works and returns agent addresses
        agent_addrs = self.env.get_agents(addr=True)
        self.assertEqual(len(agent_addrs), n_agents)
        for addr in agent_addrs:
            self.assertTrue(type(addr), str)
            self.assertTrue(addr.rsplit("/", 1)[0], 'tcp://localhost:5555')

        # If environment has manager, it is not returned by default parameters
        # of get_agents
        a0 = agents[0]
        self.env.manager = a0
        env_agents = self.env.get_agents(addr=False)
        self.assertEqual(len(env_agents), n_agents - 1)
        self.assertNotIn(a0, env_agents)

        # None manager is handled as no manager attribute at all.
        self.env.manager = None
        env_agents = self.env.get_agents(addr=False)
        self.assertEqual(len(env_agents), n_agents)

        c_agent = CreativeTestAgent(self.env)
        c_agents = self.env.get_agents(addr=False, agent_cls=CreativeTestAgent)
        self.assertEqual(len(c_agents), 1)
        self.assertEqual(c_agent, c_agents[0])
        c_agents = self.env.get_agents(addr=True, agent_cls=CreativeTestAgent)
        self.assertEqual(len(c_agents), 1)
        self.assertEqual(c_agents[0], c_agent.addr)
        env_agents = self.env.get_agents(agent_cls=CreativeAgent)
        self.assertEqual(len(env_agents), 20)

        env_agents = self.env.get_agents(addr=False)
        for i in range(1000):
            a = choice(env_agents)
            r = self.env.get_random_agent(a)
            # Random agent cannot be the same as the agent calling
            self.assertNotEqual(a, r)

        conns = 6
        self.env.create_random_connections(n=conns)
        for a in agents:
            a_conns = list(a.connections.keys())
            # all get_agents get enough random connections
            self.assertEqual(len(a_conns), conns)
            # all connections are different
            self.assertEqual(len(a_conns), len(set(a_conns)))
            # agent cannot have itself in connections
            self.assertNotIn(a.addr, a_conns)

        # Not specifying addr or agent raises error.
        with self.assertRaises(TypeError):
            self.loop.run_until_complete(self.env.trigger_act())

        # args and kwargs get passed down to agents in trigger_act
        args = ('ploo', 'plaa')
        kwargs = {'arg1': 1, 'arg2': 2}
        ret = self.loop.run_until_complete(self.env.trigger_act
                                           (*args, agent=c_agent, **kwargs))
        self.assertEqual(args, ret[0])
        self.assertEqual(kwargs, ret[1])

        # args and kwargs are passed down to agents in trigger_all and all
        # agents are triggered
        env2 = Environment.create(('localhost', 5556))
        for _ in range(n_agents):
            a = CreativeTestAgent(env2)
        rets = self.loop.run_until_complete(env2.trigger_all(*args, **kwargs))
        self.assertEqual(len(rets), n_agents)
        for ret in rets:
            self.assertEqual(args, ret[0])
            self.assertEqual(kwargs, ret[1])

        env2_addrs = env2.get_agents(addr=True)
        con_map = {}
        for addr in env2_addrs:
            conns = []
            appended = []
            while len(conns) < 5:
                r = choice(env2_addrs)
                if (r != addr) and (r not in appended):
                    conns.append((r, {'attitude': random()}))
                    appended.append(r)
            con_map[addr] = conns

        # Check that create_connections works
        env2.create_connections(con_map)
        for agent in env2.get_agents(addr=False):
            conns = con_map[agent.addr]
            self.assertEqual(len(conns), len(list(agent.connections.keys())))
            for addr, data in conns:
                self.assertIn(addr, list(agent.connections.keys()))
                self.assertEqual(agent.connections[addr], data)
        env2.destroy()

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
