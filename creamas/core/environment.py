'''
.. py:module:: environment

Environments for agents.
'''
import logging
from random import choice

import aiomas

from creamas.logging import ObjectLogger


__all__ = ['Environment']


class Environment():
    '''Basic environment for agents.

    '''
    def __init__(self, addr=('localhost', 5555), name=None, clock=None,
                 extra_ser=None, log_folder=None):
        self._container = aiomas.Container.create(addr, codec=aiomas.MsgPack,
                                                  clock=clock,
                                                  extra_serializers=extra_ser)
        self._artifacts = {}
        self._name = name if type(name) is str else 'env'

        if type(log_folder) is str:
            self.logger = ObjectLogger(self, log_folder, add_name=False,
                                       init=True)
        else:
            self.logger = None

    @property
    def name(self):
        '''Name of the environment.'''
        return self._name

    @property
    def container(self):
        '''``aiomas.Container``, serves as a communication route between
        agents.
        '''
        return self._container

    @property
    def agents(self):
        '''Agents in environment.'''
        return list(self._container.agents.dict.values())

    @property
    def artifacts(self):
        '''Published artifacts for all agents.'''
        return self._artifacts

    def get_agent(self, name):
        '''Get agent by its name.'''
        agent = None
        for a in self.agents:
            if a.name == name:
                agent = a
                break
        return agent

    def create_initial_connections(self, n=5):
        '''Create random initial connections for all agents.

        :param int n: number of connections for each agent
        '''
        assert type(n) == int
        assert n > 0
        for a in self.agents:
            for i in range(n):
                r_agent = self.get_random_agent(a)
                while r_agent in a.connections:
                    r_agent = self.get_random_agent(a)
                a.add_connection(r_agent)

    def get_random_agent(self, agent):
        '''Return random agent that is not the same as agent given as
        parameter.

        :param agent: Agent that produced the artifact
        :type agent: :py:class:`~creamas.core.agent.CreativeAgent`
        :returns: random, non-connected, agent from the environment
        :rtype: :py:class:`~creamas.core.agent.CreativeAgent`
        '''
        r_agent = choice(self.agents)
        while r_agent.addr == agent.addr:
            r_agent = choice(self.agents)
        return r_agent

    def add_artifact(self, agent, artifact):
        '''Add artifact with given framing to the environment.

        :param agent: Agent that produced the artifact
        :type agent: :py:class:`~creamas.core.agent.CreativeAgent`
        :param object artifact: Artifact to be added.
        '''
        if agent.name not in self.artifacts:
            self.artifacts[agent.name] = []
        self.artifacts[agent.name].append(artifact)
        self._log(logging.DEBUG, "Added '{}' to environment artifacts."
                  .format(artifact))

    def get_artifacts(self, agent):
        '''Get artifacts published by certain agent.

        :returns: All artifacts published by the agent.
        :rtype: list
        '''
        return self.artifacts[agent.name]

    def _log(self, level, msg):
        if self.logger.__class__ == logging.Logger:
            self.logger.log(level, msg)

    def save_info(self, folder):
        '''Save information accumulated during the environments lifetime.

        Called from :py:meth:`~creamas.core.Environment.destroy`. Override in
        subclass.

        :param str folder: root folder to save information
        '''
        pass

    def destroy(self, folder=None):
        '''Destroy the environment.

        Does the following:

        1. calls :py:meth:`~creamas.core.Environment.save_info`
        2. for each agent: calls :py:meth:`close`
        3. calls shutdown for its **container**.
        '''
        self.save_info(folder)
        for a in self.agents:
            a.close(folder=folder)
        self.container.shutdown()
