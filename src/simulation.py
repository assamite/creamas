'''
.. py:module:: simulation

Basic simulation implementation for research purposes.
'''
from random import choice, randint, shuffle
import logging
import os

import aiomas

from agent import NumberAgent
from environment import Environment

class Simulation():
    '''Base class for simulations.'''
    
    def __init__(self, host = 'localhost', port = 5555, n_agents = 10, 
                 agent_cls = NumberAgent, log = True, log_folder = None,
                 log_level = logging.DEBUG):
        self.log_folder = log_folder
        self.log = log
        env_logger = None
        a_logger = None
        fmt = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(log_level)
        fh = None
        
        # Create environment and simulation loggers.
        if self.log:
            self.logger = logging.getLogger(name = 'MAS-sim')
            self.logger.addHandler(ch)
            self.logger.setLevel(logging.DEBUG)
            env_logger = logging.getLogger(name = 'MAS-env')
            env_logger.addHandler(ch)
            env_logger.setLevel(logging.DEBUG)
            
            if self.log_folder is not None:
                fh = logging.FileHandler(os.path.join(log_folder, 'sim.log'))
                fh.setFormatter(fmt)
                fh.setLevel(log_level)
                self.logger.addHandler(fh)
                fh = logging.FileHandler(os.path.join(log_folder, 'env.log'))
                fh.setFormatter(fmt)
                fh.setLevel(log_level)
                env_logger.addHandler(fh)
                
        self.env = Environment((host, port), loggers = [env_logger])               
        self.agents = []
         
        # Create agents and possible loggers
        for i in range(n_agents):
            sn = len(str(n_agents))
            loggers = []
            if self.log:
                a_logger = logging.getLogger(name = ('MAS-agent{0:<' + str(sn) + '}').format(i))
                a_logger.addHandler(ch)
                a_logger.setLevel(logging.DEBUG)
                if self.log_folder is not None:
                    fh = logging.FileHandler(os.path.join(log_folder, ('agent{0:<' + str(sn) + '}.log').format(i)))
                    fh.setFormatter(fmt)
                    fh.setLevel(log_level)
                    a_logger.addHandler(fh)
            loggers.append(a_logger)
            
            agent = agent_cls(self.env, loggers = loggers)
            self.agents.append(agent)

        self.env.create_initial_connections()
        self.age = 0


    def run_steps(self, steps = 10, order = 'random'):
        '''Progress simulation with given amount of steps.'''
        for i in range(steps):
            self.run(order = order)
                
                
    def run(self, order = 'random'):
        '''Run simulation for single step.'''
        self.age += 1
        self._log(logging.INFO, "\t***** Step {} *****". format(self.age))
        if order == 'random': shuffle(self.agents)
        for a in self.agents:
            aiomas.run(until=a.act())
                
     
    def _log(self, level, msg):
        if self.logger.__class__ == logging.Logger:
            self.logger.log(level, msg)
        
        
    def end(self, folder = None):
        '''End simulation and destroy the current simulation environment.'''
        self.env.destroy(folder = folder)
            
            
if __name__ == "__main__":        
    sim = Simulation(log = True, log_folder = "/Users/pihatonttu/git/mas/logs/")
    sim.run_steps(steps = 10, order = 'random')
    sim.end()

            
        
