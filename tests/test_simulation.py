"""
.. :py:module:: test_simulation
    :platform: Unix

Tests for simulation module.
"""
import unittest

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.core.simulation import Simulation


class DummyAgent(CreativeAgent):

    async def act(self):
        pass


class SimulationTestCase(unittest.TestCase):

    def test_create(self):
        """Test Simulation.create."""
        sim = Simulation.create(env_cls=Environment,
                                env_kwargs={'addr': ('localhost', 5555)},
                                agent_cls=CreativeAgent, n_agents=10,
                                agent_kwargs={}, conns=3, log_folder=None)

        env = sim.env
        self.assertEqual(sim.name, 'sim')
        self.assertEqual(env.__class__, Environment,
                         'env class is not expected')
        agents = sim.env.get_agents(addr=False)
        a = agents[0]
        self.assertEqual(a.__class__, CreativeAgent,
                         'Agent class is not as expected')
        self.assertEqual(len(agents), 10,
                         'Simulation did not create correct amount of agents')

        for a in agents:
            self.assertEqual(len(a.connections), 3,
                             'Simulation did not create correct initial connections')

        sim.close()
        self.assertIsNone(sim.env._tcp_server)

        a_classes = [CreativeAgent, DummyAgent]
        a_nums = [10, 5]
        sim = Simulation.create(agent_cls=a_classes, n_agents=a_nums,
                                agent_kwargs=[{}, {}],
                                env_kwargs={'addr': ('localhost', 5555)})

        # Both get_agents get created right amount
        n_ca = 0
        n_da = 0
        for a in sim.env.get_agents(addr=False):
            if a.__class__ == CreativeAgent:
                n_ca += 1
            if a.__class__ == DummyAgent:
                n_da += 1
        self.assertEqual(n_ca, 10)
        self.assertEqual(n_da, 5)
        sim.close()

        sim = Simulation.create(agent_cls=DummyAgent, conns=3,
                                env_kwargs={'addr': ('localhost', 5555)})
        self.assertEqual(sim.cur_step, 0)
        self.assertEqual(len(sim._agents_to_act), 0)
        sim.step()
        self.assertEqual(len(sim._agents_to_act), 0)
        self.assertEqual(sim.cur_step, 1)
        sim.step()
        self.assertEqual(len(sim._agents_to_act), 0)
        self.assertEqual(sim.cur_step, 2)
        sim.steps(10)
        self.assertEqual(sim.cur_step, 12)
        self.assertEqual(len(sim._agents_to_act), 0)
        sim.close()


if __name__ == '__main__':
    unittest.main()
