"""
.. py:module:: simulation

Basic simulation implementation where agents in the same environment can be
run in an iterative manner.
"""
import time
import logging
from random import shuffle

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.logging import ObjectLogger
from creamas import util

__all__ = ['Simulation']


class Simulation():
    """A base class for iterative simulations.

    In each step the simulation calls :py:meth:`~creamas.core.agent.CreativeAgent.act` for each agent in the simulation.
    """
    @classmethod
    def create(cls, agent_cls=None, n_agents=10, agent_kwargs={}, env_cls=Environment, env_kwargs={}, callback=None,
               conns=0, log_folder=None):
        """A convenience function to create simple simulations.

        Method first creates environment, then instantiates agents into it with give arguments, and finally creates
        simulation for the environment.

        :param agent_cls:
            class for agents, or list of classes. If list, then **n_agents** and **agent_kwargs** are expected to be
            lists also.

        :param n_agents:
            amount of agents for simulation, or list of amounts

        :param agent_kwargs:
            keyword arguments passed to agents at creation time, or list of keyword arguments.

        :param env_cls:
            environment class for simulation

        :type env_cls:
            :py:class:`~creamas.core.environment.Environment`

        :param dict env_kwargs:
            keyword arguments passed to environment at creation time

        :param callable callback:
            optional callable to call after each simulation step

        :param conns:
            Create **conns** amount of initial (random) connections for agents in the simulation environment.

        :param str log_folder:
            folder for possible logging. This overwrites *log_folder* keyword argument from **agent_kwargs** and
            **env_kwargs**.
        """
        if not issubclass(env_cls, Environment):
            raise TypeError("Environment class must be derived from ({}"
                            .format(Environment.__class__.__name__))
        if callback is not None and not hasattr(callback, '__call__'):
            raise TypeError("Callback must be callable.")

        if hasattr(agent_cls, '__iter__'):
            for e in agent_cls:
                if not issubclass(e, CreativeAgent):
                    raise TypeError("All agent classes must be derived from {}"
                                    .format(CreativeAgent.__class__.__name__))
        else:
            if not issubclass(agent_cls, CreativeAgent):
                raise TypeError("Agent class must be derived from {}"
                                .format(CreativeAgent.__class__.__name__))

        env = env_cls.create(**env_kwargs)

        agents = []
        if hasattr(agent_cls, '__iter__'):
            for i in range(len(n_agents)):
                agent_kwargs[i]['environment'] = env
                agent_kwargs[i]['log_folder'] = log_folder
                agents = agents + [agent_cls[i](**agent_kwargs[i]) for e in
                                   range(n_agents[i])]
        else:
            agent_kwargs['environment'] = env
            agent_kwargs['log_folder'] = log_folder
            agents = [agent_cls(**agent_kwargs) for e in range(n_agents)]

        if conns > 0:
            env.create_random_connections(n=conns)

        return Simulation(env, callback, log_folder)

    def __init__(self, env, callback=None, log_folder=None):
        """Create simulation for previously set up environment.

        :param env: fully initialized environment with agents already set
        :type env:
            :class:`~creamas.core.environment.Environment`,
            :class:`~creamas.mp.MultiEnvironment` or
            :class:`~creamas.ds.DistributedEnvironment`
        :param callable callback: function to call after each simulation step
        :param str log_folder: folder to log simulation information
        """
        self._env = env
        self._callback = callback
        self._age = 0
        self._order = 'alphabetical'
        self._name = 'sim'
        self._start_time = time.monotonic()
        self._step_start_time = None
        self._step_processing_time = 0.0
        self._processing_time = 0.0
        self._end_time = None

        # List of agents that have not been triggered for current step.
        self._agents_to_act = []

        if type(log_folder) is str:
            self.logger = ObjectLogger(self, log_folder, add_name=False,
                                       init=True)
        else:
            self.logger = None

    @property
    def name(self):
        """Name of the simulation.
        """
        return self._name

    @property
    def env(self):
        """Environment for the simulation.
        """
        return self._env

    @property
    def age(self):
        """Age of the simulation.
        """
        return self._age

    @property
    def callback(self):
        """Callable to be called after each simulation step for any extra bookkeeping, etc.. Should accept one
        parameter: *age* that is current simulation age.
        """
        return self._callback

    @property
    def order(self):
        """Order in which agents are run. Order is not enforced for asynchronous executions.

        Possible values:

        * alphabetical: agents are sorted by name
        * random: agents are shuffled

        Changing the order while iteration is unfinished will take place in the next iteration.
        """
        return self._order

    @order.setter
    def order(self, order):
        assert order in ['alphabetical', 'random']
        self._order = order

    def _get_order_agents(self):
        agents = self.env.get_agents(addr=True)
        if self.order == 'alphabetical':
            return sorted(agents)
        shuffle(agents)
        return agents

    def _init_step(self):
        """Initialize next step of simulation to be run.
        """
        self._age += 1
        self.env.age = self._age
        self._log(logging.INFO, "")
        self._log(logging.INFO, "\t***** Step {:0>10} *****". format(self.age))
        self._log(logging.INFO, "")
        self._agents_to_act = self._get_order_agents()
        self._step_processing_time = 0.0
        self._step_start_time = time.monotonic()

    def _finalize_step(self):
        """Finalize simulation step after all agents have acted for the current
        step.
        """
        t = time.time()
        if self._callback is not None:
            self._callback(self.age)
        t2 = time.monotonic()
        self._step_processing_time += t2 - t
        self._log(logging.INFO, "Step {} run in: {:.3f}s ({:.3f}s of "
                  "actual processing time used)"
                  .format(self.age, self._step_processing_time,
                          t2 - self._step_start_time))
        self._processing_time += self._step_processing_time

    def finish_step(self):
        """Progress simulation to the end of the current step.

        .. deprecated:: 0.4.0
            Use :func:`step` instead.
        """
        rets = []
        while len(self._agents_to_act) > 0:
            ret = self.next()
            rets.append(ret)
        return rets

    def step(self):
        """Progress simulation by a single step.
        """
        assert len(self._agents_to_act) == 0
        t = time.monotonic()
        rets = []

        self._init_step()

        while len(self._agents_to_act) > 0:
            addr = self._agents_to_act.pop(0)
            ret = util.run(self.env.trigger_act(addr=addr))
            rets.append(ret)

        self._finalize_step()
        self._step_processing_time = time.monotonic() - t
        return rets

    def steps(self, n):
        """Progress simulation with given amount of steps.

        Can not be called when some of the agents have not acted for the current step.

        :param int n: amount of steps to run
        """
        assert len(self._agents_to_act) == 0
        rets = []
        for _ in range(n):
            ret = self.step()
            rets.append(ret)

        return rets

    def async_step(self):
        """Progress simulation by running all agents asynchronously once.
        """
        assert len(self._agents_to_act) == 0
        self._init_step()
        t = time.time()
        ret = util.run(self.env.trigger_all())
        self._agents_to_act = []
        self._step_processing_time = time.monotonic() - t
        self._finalize_step()
        return ret

    def async_steps(self, n):
        """Progress simulation by running all agents *n* times asynchronously.
        """
        assert len(self._agents_to_act) == 0
        rets = []
        for _ in range(n):
            ret = self.async_step()
            rets.append(ret)

        return rets

    def _log(self, level, msg):
        if self.logger is not None:
            self.logger.log(level, msg)

    def end(self, folder=None):
        """Close the simulation and the current simulation environment.

        .. deprecated:: 0.4.0
            Use func:`close` instead.
        """
        return self.close(folder=folder)

    def close(self, folder=None):
        """Close the simulation and the current simulation environment.
        """
        ret = self.env.close(folder=folder)
        self._end_time = time.time()
        self._log(logging.DEBUG, "{} step simulation completed in {:.3f}s (actual processing time {:.3f}s)."
                  .format(self.age, self._end_time - self._start_time, self._processing_time))
        return ret
