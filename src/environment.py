'''
.. py:module:: environment

Environments for agents.
'''
from random import choice
import logging

import aiomas

class Environment():
    '''Basic environment for agents.
    
    :ivar container: communication route between agents.
    :vartype container: ``aiomas.Container`` 
    :ivar dict artifacts: published artifacts for all agents.
    '''
    def __init__(self, addr, clock = None, extra_serializers = None, loggers = []):
        self.container = aiomas.Container.create(addr, clock = clock, extra_serializers = extra_serializers)
        self.artifacts = {}
        self.loggers = loggers
        
        
    def create_initial_connections(self, n = 5):
        '''Create random initial connections for all agents.
        
        :param int n: number of connections for each agent
        '''
        for a in list(self.container.agents.dict.values()):
            for i in range(n):
                a.add_connection(self.get_random_agent(a))
     
     
    def get_random_agent(self, agent):
        '''Return random agent that is not the same as agent given as parameter.
        
        :param agent: Agent that produced the artifact
        :type agent: instance of ``CreativeAgent`` subclass
        :returns: random, non-connected, agent from the environment
        :rtype: instance of ``CreativeAgent`` subclass
        '''
        r_agent = choice(list(self.container.agents.dict.values()))
        while r_agent.addr == agent.addr: 
            r_agent = choice(list(self.container.agents.dict.values()))        
        return r_agent
    
    
    def add_artifact(self, agent, artifact, framing):
        '''Add artifact with given framing to the environment.
        
        :param agent: Agent that produced the artifact
        :type agent: subclass of ``CreativeAgent``
        :param object artifact: Artifact to be added.
        :param framing: Framing for the artifact.
        :type framing: object
        '''
        if agent.addr not in self.artifacts:
            self.artifacts[agent.addr] = [] 
        self.artifacts[agent.addr].append((artifact, framing))
        self._log(logging.DEBUG, "{} added '{}' with framing '{}' to environment artifacts.".format(agent, artifact, framing))
        
        
    
    def get_artifacts(self, agent):
        '''Get artifacts published by certain agent.
        
        :returns: All artifacts published by the agent.
        :rtype: list
        '''
        return self.domain[agent.addr]
    

    def _log(self, level, msg):
        for logger in self.loggers:
            if logger.__class__ == logging.Logger:
                logger.log(level, msg)
        
        
    def destroy(self, folder = None):
        '''Destroy the environment. 

        Destroying the environment calls all its agents shutdown method, and 
        then shuts down the agent container. If ``folder`` is given, saves 
        information of the run to that folder.
        '''
        for a in list(self.container.agents.dict.values()):
            a.close(folder = folder)
            
        if folder is not None:
            pass
        
        self.container.shutdown()