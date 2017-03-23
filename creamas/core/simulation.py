'''
.. py:module:: simulation

Basic simulation implementation where agents in the same environment can be
run in an iterative manner.
'''
import time
import logging
from random import shuffle

import asyncio
import aiomas

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.logging import ObjectLogger

__all__ = ['Simulation']


class Simulation():
    '''Base class for iterative simulations.

    In each simulation step calls
    :py:meth:`~creamas.core.agent.CreativeAgent.act` for each agent in
    simulation environment.
    '''
    @classmethod
    def create(self, agent_cls=None, n_agents=10, agent_kwargs={},
               env_cls=Environment, env_kwargs={}, callback=None, conns=0,
               log_folder=None):
        '''Convenience function to create simple simulations.

        Method first creates environment, then instantiates agents into it
        with give arguments, and finally creates simulation for the
        environment.

        :param agent_cls:
            class for agents, or list of classes. If list, then **n_agents**
            and **agent_kwargs** are expected to be lists also.

        :param n_agents:
            amount of agents for simulation, or list of amounts

        :param agent_kwargs:
            keyword arguments passed to agents at creation time, or list of
            keyword arguments.

        :param env_cls:
            environment class for simulation

        :type env_cls:
            :py:class:`~creamas.core.environment.Environment`

        :param dict env_kwargs:
            keyword arguments passed to environment at creation time

        :param callable callback:
            optional callable to call after each simulation step

        :param conns:
            Create **conns** amount of initial (random) connections for agents
            in the simulation environment.

        :param str log_folder:
            folder for possible logging. This overwrites *log_folder* keyword
            argument from **agent_kwargs** and **env_kwargs**.
        '''
        assert issubclass(env_cls, Environment)
        assert (callback is None or hasattr(callback, '__call__'))
        if hasattr(agent_cls, '__iter__'):
            for e in agent_cls:
                assert issubclass(e, CreativeAgent)
        else:
            assert issubclass(agent_cls, CreativeAgent)

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
            env.create_initial_connections(n=conns)

        return Simulation(env, callback, log_folder)

    def __init__(self, env, callback=None, log_folder=None):
        '''Create simulation for previously set up environment.

        :param env: fully initialized environment with agents already set
        :type env: :py:class:`~creamas.core.environment.Environment`
        :param callable callback: function to call after each simulation step
        :parat str log_folder: folder to log simulation information
        '''
        self._env = env
        self._callback = callback
        self._age = 0
        self._order = 'alphabetical'
        self._name = 'sim'
        self._start_time = time.time()
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
        '''Name of the simulation.'''
        return self._name

    @property
    def env(self):
        '''Environment for the simulation. Must be a subclass of
        :py:class:`~creamas.core.environment.Environment`.
        '''
        return self._env

    @property
    def age(self):
        '''Age of the simulation.'''
        return self._age

    @property
    def callback(self):
        '''Callable to be called after each simulation step for any extra
        bookkeeping, etc.. Should accept one parameter: *age* that is current
        simulation age.
        '''
        return self._callback

    @property
    def order(self):
        '''Order in which agents are run.

        Possible values:

        * alphabetical: agents are sorted by name
        * random: agents are shuffled

        Changing the order while iteration is unfinished will take place in the
        next iteration.
        '''
        return self._order

    @order.setter
    def order(self, order):
        assert order in ['alphabetical', 'random']
        self._order = order

    def _get_order_agents(self):
        agents = self.env.get_agents(address=True)
        if self.order == 'alphabetical':
            return sorted(agents)
        shuffle(agents)
        return agents

    def _init_step(self):
        '''Initialize next step of simulation to be run.'''
        self._age += 1
        self.env.age = self._age
        self._log(logging.INFO, "")
        self._log(logging.INFO, "\t***** Step {:0>4} *****". format(self.age))
        self._log(logging.INFO, "")
        self._agents_to_act = self._get_order_agents()
        self._step_processing_time = 0.0
        self._step_start_time = time.time()

    def _finalize_step(self):
        '''Finalize simulation step after all agents have acted for the current
        step.
        '''
        t = time.time()
        if self._callback is not None:
            self._callback(self.age)
        t2 = time.time()
        self._step_processing_time += t2 - t
        self._log(logging.INFO, "Step {} run in: {:.3f}s ({:.3f}s of "
                  "actual processing time used)"
                  .format(self.age, self._step_processing_time,
                          t2 - self._step_start_time))
        self._processing_time += self._step_processing_time

    def async_steps(self, n):
        assert len(self._agents_to_act) == 0
        for _ in range(n):
            self.async_step()

    def async_step(self):
        '''Progress simulation by running all agents once asynchronously.
        '''
        assert len(self._agents_to_act) == 0
        self._init_step()
        t = time.time()
        tasks = [asyncio.ensure_future(self.env.trigger_act(addr)) for
                 addr in self._agents_to_act]
        aiomas.run(until=asyncio.gather(*tasks))
        self._agents_to_act = []
        self._step_processing_time = time.time() - t
        self._finalize_step()

    def steps(self, n):
        '''Progress simulation with given amount of steps.

        Can not be called when some of the agents have not acted for the
        current step.

        :param int n: amount of steps to run
        '''
        assert len(self._agents_to_act) == 0
        for _ in range(n):
            self.step()

    def step(self):
        '''Progress simulation with a single step.

        Can not be called when some of the agents have not acted for the
        current step.
        '''
        assert len(self._agents_to_act) == 0
        self.next()
        while len(self._agents_to_act) > 0:
            self.next()

    def next(self):
        '''Trigger next agent to :py:meth:`~creamas.core.CreativeAgent.act` in
        the current step.
        '''
        # all agents acted, init next step
        t = time.time()
        if len(self._agents_to_act) == 0:
            self._init_step()

        agent = self._agents_to_act.pop(0)
        aiomas.run(until=self.env.trigger_act(agent))
        t2 = time.time()
        self._step_processing_time += t2 - t

        # all agents acted, finalize current step
        if len(self._agents_to_act) == 0:
            self._finalize_step()

    def finish_step(self):
        '''Progress simulation to the end of the current step.'''
        while len(self._agents_to_act) > 0:
            self.next()

    def _log(self, level, msg):
        if self.logger is not None:
            self.logger.log(level, msg)

    def end(self, folder=None):
        '''End simulation and destroy the current simulation environment.'''
        ret = self.env.destroy(folder=folder)
        self._end_time = time.time()
        self._log(logging.INFO, "Simulation run with {} steps took {:.3f}s to "
                  "complete, while actual processing time was {:.3f}s."
                  .format(self.age, self._end_time - self._start_time,
                          self._processing_time))
        return ret
