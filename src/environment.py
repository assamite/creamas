'''
'''
from random import choice
import logging

import aiomas

class Environment():
    '''Basic environment for agents.
    
    Environment contains ``aiomas.Container`` as a communication route between 
    agents and has ``artifacts`` variable that holds all the artifacts agents 
    have published.
    '''
    def __init__(self, addr, clock = None, extra_serializers = None, loggers = []):
        self.container = aiomas.Container.create(addr, clock = clock, extra_serializers = extra_serializers)
        self.artifacts = {}
        self.loggers = loggers
        
        
    def create_initial_connections(self, n = 5, type = 'random'):
        for a in list(self.container.agents.dict.values()):
            for i in range(n):
                if type == 'random':
                    a.add_connection(self.get_random_agent(a))
     
     
    def get_random_agent(self, agent):
        '''Return random agent that is not the same as agent given as parameter.'''
        r_agent = choice(list(self.container.agents.dict.values()))
        while r_agent.addr == agent.addr: 
            r_agent = choice(list(self.container.agents.dict.values()))        
        return r_agent
    
    
    def add_artifact(self, agent, artifact, framing):
        '''Add artifact with give framing to environment.'''
        if agent.addr not in self.artifacts:
            self.artifacts[agent.addr] = [] 
        self.artifacts[agent.addr].append((artifact, framing))
        self._log(logging.DEBUG, "{} added '{}' with framing '{}' to environment artifacts.".format(agent, artifact, framing))
        
        
    
    def get_domain_artifacts(self, agent):
        '''Get domain artifacts published by certain agent.'''
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