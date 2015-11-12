'''
.. py:module:: agent
    :platform: Unix
    
Agent implementations for creative tasks. Mainly module holds ``CreativeAgent``
implementation, a subclass of ``aiomas.Agent``, which holds basic functionality 
needed for creative agents.
'''
from random import choice, randint
import logging

import aiomas

class CreativeAgent(aiomas.Agent):
    '''Base class for all creative agents.
    
    All agents share certain common attributes:
    
    :ivar env: The environment where the agent lives.
    :ivar int max_R: Agent's resources per step, 0 if agent has unlimited resources.
    :ivar int cur_R: current resources.
    :ivar list F: features agent uses to evaluate artifacts
    :ivar list W: weight for each feature in **F**, in [-1,1].
    :ivar list A: artifacts the agent has created so far
    :ivar dict D: domain knowledge, other agents' artifacts seen by this agent 
    :ivar list connections: other agents this agent knows
    :ivar list attitudes: attitude towards each agent in **connections**, in [-1,1]
    
    In this basic implementation each feature in **F** is expected to be a callable
    with single parameter, the artifact to be evaluated. Callable should return 
    a float in [-1,1], where 1 means that feature is very prominent in the artifact, 
    and 0 that there is none of that feature in the artifact, and -1 means that 
    the artifact shows traits opposite to the feature. Actual evaluation formula 
    is documented in ``evaluate``.
    ''' 
    
    def __init__(self, environment, resources = 0, feats = [], weights = [], loggers = []):
        super().__init__(environment.container)
        #: Environment where agent lives.
        self.env = environment
        self.max_R = resources
        self.cur_R  = resources
        self.F = feats
        self.W = weights
        self.A = []
        self.D = {}
        self.connections = []
        self.attitudes = []
        self.loggers = loggers
    
    async def random_connection(self):
        '''Connect to random agent from current ``connections``.
        
        .. note::
            
            This is an async method that should be awaited.
        
        :returns: connected remote agent
        :rtype: instance of ``CreativityAgent``, or its subclass
        '''
        r_agent = choice(self.connections)
        remote_agent = await self.container.connect(r_agent.addr)
        return remote_agent
    
    def publish(self, artifact, framing):
        '''Publish artifact to agent's environment with given framing.
        
        :param object artifact: artifact to be published
        :param object framing: framing information attached to the artifact
        '''
        self.env.add_artifact(self, artifact, framing)
        self._log(logging.DEBUG, "Published {} to domain because of {}".format(self, artifact, framing))
    
    def refill_resources(self):
        '''Refill agent's resources to maximum.'''
        self.cur_R = self.max_R
        
    def attach_logger(self, logger):
        '''Add new logger to agent.'''
        self.loggers.append(logger)
        
    @aiomas.expose
    def evaluate(self, artifact):  
        r'''Evaluate artifact with agent's current features and weights.
        
        TODO: return framing also
        
        :param object artifact: artifact to be evaluated
        :returns: agent's evaluation of the artifact, in [-1,1]
        :rtype: float
        
        Actual evaluation formula is: 
        
        .. math::
        
            e(A) = \frac{\sum_{i=1}^{n} f_{i}(A)w_i}{\sum_{i=1}^{n} \lvert w_i \rvert},
        
        where :math:`f_{i}(A)` is the :math:`i` th feature's evaluation on artifact :math:`A`.   
        '''
        s = 0
        w = 0
        for i in range(len(self.F)):
            s += self.F[i](artifact) * self.W[i]
            w += abs(self.W[i])
            
        return s / w 
        
        
    async def ask_opinion(self, agent, artifact):
        '''Ask agent's opinion about artifact.
        
        .. note::
            
            This is an async method that should be awaited.
        
        :param agent: agent which opinion is asked
        :type agent: instance of ``CreativeAgent``, or its subclass
        :param object artifact: artifact to be evaluated
        :returns: agent's evaluation of the artifact
        :rtype: float
        '''
        remote_agent = await self.container.connect(agent.addr)
        ret = await remote_agent.evaluate(artifact)
        return ret
        
        
        
    def _log(self, level, msg):
        for logger in self.loggers:
            if logger.__class__ == logging.Logger:
                logger.log(level, msg)
            
            
    def close(self, folder = None):
        '''Perform any book keeping needed before closing the agent.
        
        Called from ``Environment.destroy()``.
        '''
        self._log(logging.DEBUG, 'Closing.'.format(self))  
        
    
class NumberAgent(CreativeAgent):
    '''Number agent created for early testing purposes of basic functionality.
    
    Searchs "new" integers and evaluates them based on how many features in F 
    (also integers) result in mod == 0.
    '''
    
    def __init__(self, environment, loggers = []):
        super().__init__(environment, loggers = loggers)
        rand = randint(2, 100)
        self.F = [rand]
        self.A = [rand]
        self.D[self.addr] = [rand]
        self._log(logging.DEBUG, 'Created: {} with feat={}'.format(self, rand))
        
        
    def add_connection(self, agent):
        self.connections.append(agent)
        
        
    async def ask_opinion(self, agent, number):
        remote_agent = await self.container.connect(agent.addr)
        ret = await remote_agent.evaluate(number)
        return ret
        
          
    def invent_number(self, low, high):
        '''Invent new number from given interval.'''
        self._log(logging.DEBUG, "{} inventing number from ({}, {})".format(self, low, high))
        numbers = []
        steps = 0
        while len(numbers) < 10 and steps < 1000:
            steps += 1
            r = randint(low, high)
            if r not in self.A:
                numbers.append(r)

        if len(numbers) == 0: 
            print("{} could not invent new number!".format(self))
            return 1
             
        best_eval = self.evaluate(numbers[0])
        best_number = numbers[0]
        for n in numbers[1:]:
            e = self.evaluate(n)
            if e > best_eval:
                best_eval = e
                best_number = n
        
        print("{} invented number {}, with e = {}.".format(self, best_number, best_eval))
        if best_eval > 0.5:
            self.F.append(best_number)   
            print("{} appended {} to features.".format(self, best_number))     
            
        return best_number, best_eval       
        
    
    async def act(self):
        m = max(self.F)
        n, e = self.invent_number(2, m + 100)
        evaluations = []
        for a in self.connections:
            ev = await self.ask_opinion(a, n)
            evaluations.append(ev)
        
        evaluations.sort(reverse = True)
        be = sum(evaluations[:3]) / 3
        if be > 0.25 and e > 0.5:
            self.publish(n, (e, be))
  
        
    @aiomas.expose
    def add(self, value):
        return value + choice(self.features)
    
    
    @aiomas.expose
    def evaluate(self, number):
        evaluation = 0.0
        for n in self.F:
            if number % n == 0: 
                evaluation += 1
                
        return evaluation / len(self.F)

        