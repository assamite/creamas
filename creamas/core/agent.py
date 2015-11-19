'''
.. py:module:: creamas.coreagent
    :platform: Unix

Agent module holds **CreativeAgent** implementation, a subclass of
``aiomas.Agent``, which holds basic functionality thought to be shared by all
creative agents.
'''
import logging
import pickle
from random import choice

import aiomas

from creamas.logging import ObjectLogger

__all__ = ['CreativeAgent']


class CreativeAgent(aiomas.Agent):
    '''Base class for all creative agents.

    All agents share certain common attributes:

    :ivar ~creamas.core.agent.CreativeAgent.env:
        The environment where the agent lives.

    :ivar int max_res:
        Agent's resources per step, 0 if agent has unlimited resources.

    :ivar int cur_res:
        Agent's current resources.

    :ivar list ~creamas.core.agent.CreativeAgent.F:
        features agent uses to evaluate artifacts

    :ivar list ~creamas.core.agent.CreativeAgent.W:
        Weight for each feature in **F**, in [-1,1].

    :ivar list A:
        Artifacts the agent has created so far

    :ivar dict D:
        Domain knowledge, other agents' artifacts seen by this agent

    :ivar list connections:
        Other agents this agent knows

    :ivar list attitudes:
        Attitude towards each agent in **connections**, in [-1,1]

    :ivar str ~creamas.core.agent.CreativeAgent.name:
        Name of the agent. defaults to A<n>, where n is the agent's number in
        environment. Agent's name must be unique within its environment.

    :ivar ~creamas.core.agent.CreativeAgent.age:
        Age of the agent
    '''
    def __init__(self, environment, resources=0, name=None, log_folder=None):
        super().__init__(environment.container)
        self._age = 0
        self._env = environment
        self._max_res = resources
        self._cur_res = resources
        self._F = []
        self._W = []
        self._A = []
        self._D = {}
        self._connections = []
        self._attitudes = []

        if type(name) is str and len(name) > 0:
            self.__name = None
            if self.env.get_agent(name) is not None:
                raise ValueError('Agent names should be unique within the '
                                 'environment. Agent "{}" already found.'
                                 .format(name))
            self.__name = name
        else:
            n = "A{}".format(self.addr.rsplit("/", 1)[1])
            self.__name = n

        if type(log_folder) is str:
            self.logger = ObjectLogger(self, log_folder, add_name=True,
                                       init=True)
        else:
            self.logger = None

    @property
    def age(self):
        '''Age of the agent.'''
        return self._age

    @age.setter
    def age(self, i):
        self._age = i

    @property
    def name(self):
        '''Human readable name of the agent. Must be unique in agent's
        environment. Agent cannot change its name during its lifetime.'''
        return self.__name

    @property
    def env(self):
        '''The environment where the agent lives. Must be a subclass of
        :py:class:`~creamas.core.environment.Environment`.'''
        return self._env

    @property
    def F(self):
        '''Features agent uses to evaluate artifacts. Each feature in **F** is
        expected to be a callable with single parameter, the artifact to be
        evaluated. Callable should return a float in [-1,1], where 1 means that
        feature is very prominent in the artifact, and 0 that there is none of
        that feature in the artifact, and -1 means that the artifact shows
        traits opposite to the feature.

        .. note::

            If used other way than what is stated above, override
            :py:meth:`~creamas.core.agent.CreativeAgent.evaluate`.
        '''
        return self._F

    @property
    def W(self):
        '''Weights for features. Each weight should be in [-1,1].'''
        return self._W

    @property
    def A(self):
        '''Artifacts created so far by the agent.'''
        return self._A

    @property
    def D(self):
        '''Domain knowledge accumulated by this agent.

        Dictionary of agents and their artifacts.
        '''
        return self._D

    @property
    def max_res(self):
        '''Maximum resources for the agent per act. If 0, agent has unlimited
        resources.'''
        return self._max_res

    @max_res.setter
    def max_res(self, value):
        self._max_res = value

    @property
    def cur_res(self):
        '''Agent's current resources.'''
        return self._cur_res

    @cur_res.setter
    def cur_res(self, value):
        assert value <= self.max_res
        self._cur_res = value

    @property
    def connections(self):
        '''Connections to the other agents in the **env**.'''
        return self._connections

    @property
    def attitudes(self):
        '''Attitudes towards agents in **connections**.'''
        return self._attitudes

    def get_attitude(self, agent):
        '''Get attitude towards agent in **connections**. If agent is not in
        **connections**, returns None.
        '''
        try:
            ind = self._connections.index(agent)
            return self._attitudes[ind]
        except:
            return None

    def set_attitude(self, agent, attitude):
        '''Set attitude towards agent. If agent is not in **connections**, adds
        it.
        '''
        assert (attitude >= -1.0 and attitude <= 1.0)
        try:
            ind = self._connections.index(agent)
            self._attitudes[ind] = attitude
        except:
            self.add_connection(agent, attitude)

    def set_weight(self, feature, weight):
        '''Set weight for feature in **F**, if feature is not in **F**, adds
        it.
        '''
        assert (weight >= -1.0 and weight <= 1.0)
        try:
            ind = self._F.index(feature)
            self._W[ind] = weight
        except:
            self.add_feature(feature, weight)

    def get_weight(self, feature):
        '''Get weight for feature. If feature is not in **F**, returns None.'''
        try:
            ind = self._F.index(feature)
            return self._W[ind]
        except:
            return None

    def add_artifact(self, artifact):
        '''Add artifact to **A**.'''
        self._A.append(artifact)

    def add_feature(self, feature, weight):
        '''Add feature to **F** with initial weight. Does nothing, if feature
        is already in **F**.'''
        if feature not in self._F:
            self._F.append(feature)
            self._W.append(weight)

    def remove_feature(self, feature):
        '''Remove feature from **F**.'''
        try:
            ind = self._F.index(feature)
            del self._F[ind]
            del self._W[ind]
        except:
            pass

    def add_connection(self, agent, attitude=0.0):
        '''Added agent to current **connections** with given initial attitude.

        Does nothing if agent is already in **connections**.

        :param agent: agent to be added
        :type agent: :py:class:`~creamas.core.agent.CreativeAgent`
        :param attitude: initial attitude towards agent, in [-1, 1]
        :type attitude: float
        '''
        if agent not in self._connections:
            self.connections.append(agent)
            self.attitudes.append(attitude)

    def remove_connection(self, agent):
        '''Remove agent from current connections.'''
        try:
            ind = self._connections.index(agent)
            del self._connections[ind]
            del self._attitudes[ind]
        except:
            pass

    async def random_connection(self):
        '''Connect to random agent from current **connections**.

        .. note::

            This is an async method that should be awaited.

        :returns: connected remote agent
        :rtype: :py:class:`~creamas.core.agent.CreativeAgent`
        '''
        r_agent = choice(self._connections)
        remote_agent = await self.container.connect(r_agent.addr)
        return remote_agent

    def publish(self, artifact):
        '''Publish artifact to agent's environment.

        :param object artifact: artifact to be published
        '''
        self.env.add_artifact(self, artifact)
        self._log(logging.DEBUG, "Published {} to domain because of {}"
                  .format(self, artifact))

    def refill(self):
        '''Refill agent's resources to maximum.'''
        self._cur_res = self._max_res

    @aiomas.expose
    def evaluate_other(self, pkl):
        '''Evaluate function that first unpickles artifact, then calls
        **evaluate** and then pickles the evaluation results to be send over
        tcp.

        .. note::

            This function is exposed to other agents by default.
        '''
        artifact = pickle.loads(pkl)
        ret = self.evaluate(artifact)
        return pickle.dumps(ret)

    def evaluate(self, artifact):
        r'''Evaluate artifact with agent's current features and weights.

        :param artifact:
            artifact to be evaluated

        :type artifact:
            :py:class:`~creamas.core.artifact.Artifact`

        :returns:
            agent's evaluation of the artifact, in [-1,1], and framing. In this
             basic implementation framing is always *None*.

        :rtype:
            tuple

        Actual evaluation formula is:

        .. math::

            e(A) = \frac{\sum_{i=1}^{n} f_{i}(A)w_i}
            {\sum_{i=1}^{n} \lvert w_i \rvert},

        where :math:`f_{i}(A)` is the :math:`i` th feature's evaluation on
        artifact :math:`A`, and :math:`w_i` is the weight for feature
        :math:`f_i`.
        '''
        s = 0
        w = 0.0
        if len(self.F) == 0:
            return 0.0, None
        for i in range(len(self.F)):
            s += self.F[i](artifact) * self.W[i]
            w += abs(self.W[i])

        if w == 0.0:
            return 0.0, None
        return s / w, None

    async def ask_opinion(self, agent, artifact):
        '''Ask agent's opinion about artifact.

        .. note::

            This is an async method that should be awaited.

        :param agent: agent which opinion is asked
        :type agent: :py:class:`~creamas.core.agent.CreativeAgent`
        :param object artifact: artifact to be evaluated
        :returns: agent's evaluation of the artifact
        :rtype: float
        '''
        remote_agent = await self.container.connect(agent.addr)
        pkl = pickle.dumps(artifact)
        ret = await remote_agent.evaluate_other(pkl)
        ev = pickle.loads(ret)
        return ev

    async def act(self):
        '''Trigger agent to act. **Dummy method, override in subclass.**

        :raises NotImplementedError: if not overridden in subclass

        .. note::

            This is an async method that should be awaited.
        '''
        raise NotImplementedError

    def get_older(self):
        '''Age agent by one simulation step.'''
        self._age = self._age + 1

    def _log(self, level, msg):
        if self.logger is not None:
            self.logger.log(level, msg)

    def close(self, folder=None):
        '''Perform any bookkeeping needed before closing the agent.

        **Dummy implementation, override in subclass if needed.**
        '''
        pass

    def __str__(self):
        return self.__name

    def __repr__(self):
        return "{}:{}({})".format(self.__name, self.__class__.__name__,
                                  self.addr)