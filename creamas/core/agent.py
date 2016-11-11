'''
.. py:module:: agent
    :platform: Unix

Agent module holds **CreativeAgent** implementation, a subclass of
``aiomas.Agent``, which holds basic functionality thought to be shared by all
creative agents.
'''
import logging
import operator
import pickle
from random import choice

import aiomas

from creamas.core.artifact import Artifact
from creamas.core.rule import Rule, RuleLeaf
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

    :ivar list ~creamas.core.agent.CreativeAgent.R:
        rules agent uses to evaluate artifacts

    :ivar list ~creamas.core.agent.CreativeAgent.W:
        Weight for each rule in **R**, in [-1,1].

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
    def __init__(self, environment, resources=0, name=None, log_folder=None,
                 log_level=logging.DEBUG):
        super().__init__(environment)
        self._age = 0
        self._env = environment
        self._max_res = resources
        self._cur_res = resources
        self._R = []
        self._W = []
        self._A = []
        self._D = {}
        self._connections = []
        self._attitudes = []

        if type(name) is str and len(name) > 0:
            self.__name = name
        else:
            self.__name = self.addr

        if type(log_folder) is str:
            self.logger = ObjectLogger(self, log_folder, add_name=True,
                                       init=True, log_level=log_level)
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
        environment. Agent should not change its name during its lifetime.'''
        return self.__name

    def sanitized_name(self):
        import re
        a = re.split("[:/]", self.name)
        return "_".join([i for i in a if len(i) > 0])

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def env(self):
        '''The environment where the agent lives. Must be a subclass of
        :py:class:`~creamas.core.environment.Environment`.'''
        return self._env

    @property
    def R(self):
        '''Rules agent uses to evaluate artifacts. Each rule in **R** is
        expected to be a callable with single parameter, the artifact to be
        evaluated. Callable should return a float in [-1,1], where 1 means that
        rule is very prominent in the artifact, and 0 that there is none of
        that rule in the artifact, and -1 means that the artifact shows
        traits opposite to the rule.

        .. note::

            If used other way than what is stated above, override
            :py:meth:`~creamas.core.agent.CreativeAgent.extract`.
        '''
        return self._R

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
        resources. If maximum resources are set below current resources,
        current resources are capped to new maximum resources.
        '''
        return self._max_res

    @max_res.setter
    def max_res(self, value):
        if value < 0:
            value = 0
        self._max_res = value
        if self._cur_res > self._max_res:
            self._cur_res = self._max_res

    @property
    def cur_res(self):
        '''Agent's current resources. Capped to maximum resources.'''
        return self._cur_res

    @cur_res.setter
    def cur_res(self, value):
        if value > self._max_res:
            value = self._max_res
        if value < 0:
            value = 0
        self._cur_res = value

    @property
    def connections(self):
        '''Connections to the other agents in the **env**.'''
        return self._connections

    @property
    def attitudes(self):
        '''Attitudes towards agents in **connections**.'''
        return self._attitudes

    def qualname(self):
        '''Get qualified name of this class.
        '''
        return "{}:{}".format(self.__module__, self.__class__.__name__)

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

    def set_weight(self, rule, weight):
        '''Set weight for rule in **R**, if rule is not in **R**, adds
        it.
        '''
        if not (issubclass(rule.__class__, Rule) or
                issubclass(rule.__class__, RuleLeaf)):
            raise TypeError("Rule to set weight ({}) is not subclass "
                            "of {} or {}.".format(rule, Rule, RuleLeaf))
        assert (weight >= -1.0 and weight <= 1.0)
        try:
            ind = self._R.index(rule)
            self._W[ind] = weight
        except:
            self.add_rule(rule, weight)

    def get_weight(self, rule):
        '''Get weight for rule. If rule is not in **R**, returns None.'''
        if not (issubclass(rule.__class__, Rule) or
                issubclass(rule.__class__, RuleLeaf)):
            raise TypeError("Rule to get weight ({}) is not subclass "
                            "of {} or {}.".format(rule, Rule, RuleLeaf))
        try:
            ind = self._R.index(rule)
            return self._W[ind]
        except:
            return None

    def add_artifact(self, artifact):
        '''Add artifact to **A**.'''
        if not issubclass(artifact.__class__, Artifact):
            raise TypeError("Artifact to add ({}) is not {}."
                            .format(artifact, Artifact))
        self._A.append(artifact)

    def add_rule(self, rule, weight):
        '''Add rule to **R** with initial weight.

        :param rule: rule to be added
        :type rule: `~creamas.core.rule.Rule`
        :param float weight: initial weight for the rule
        :raises TypeError: if rule is not subclass of :py:class:`Rule`
        :returns: true if rule was successfully added, otherwise false
        :rtype bool:
        '''
        if not (issubclass(rule.__class__, Rule) or
                issubclass(rule.__class__, RuleLeaf)):
            raise TypeError("Rule to add ({}) is not subclass of {} or {}."
                            .format(rule.__class__, Rule, RuleLeaf))
        if rule not in self._R:
            self._R.append(rule)
            self._W.append(weight)
            return True
        return False

    def remove_rule(self, rule):
        '''Remove rule from **R** and its corresponding weight from **W**.

        :param rule: rule to remove
        :type rule: `~creamas.core.rule.Rule`
        :raises TypeError: if rule is not subclass of :py:class:`Rule`
        :returns: true if rule was successfully removed, otherwise false
        :rtype bool:
        '''
        if not (issubclass(rule.__class__, Rule) or
                issubclass(rule.__class__, RuleLeaf)):
            raise TypeError("Rule to remove ({}) is not subclass of {} or {}."
                            .format(rule.__class__, Rule, RuleLeaf))
        try:
            ind = self._R.index(rule)
            del self._R[ind]
            del self._W[ind]
            return True
        except:
            return False

    def add_connection(self, agent, attitude=0.0):
        '''Added agent to current **connections** with given initial attitude.

        Does nothing if agent is already in **connections**.

        :param agent: agent to be added
        :type agent: :py:class:`~creamas.core.agent.CreativeAgent`
        :param attitude: initial attitude towards agent, in [-1, 1]
        :type attitude: float
        '''
        if not issubclass(agent.__class__, CreativeAgent):
            raise TypeError("Agent to add in connections ({}), was not "
                            "subclass of {}"
                            .format(agent, CreativeAgent))
        if agent not in self._connections:
            self.connections.append(agent)
            self.attitudes.append(attitude)
            return True
        return False

    def remove_connection(self, agent):
        '''Remove agent from current connections.'''
        if not issubclass(agent.__class__, CreativeAgent):
            raise TypeError("Agent to remove from connections ({}), was "
                            "not subclass of {}"
                            .format(agent, CreativeAgent))
        try:
            ind = self._connections.index(agent)
            del self._connections[ind]
            del self._attitudes[ind]
            return True
        except:
            return False

    async def connect(self, addr):
        '''Connect to agent in given address.
        '''
        remote_agent = await self.env.connect(addr)
        return remote_agent

    async def random_connection(self):
        '''Connect to random agent from current **connections**.

        .. note::

            This is an async method that should be awaited.

        :returns: connected remote agent
        :rtype: :py:class:`~creamas.core.agent.CreativeAgent`
        '''
        r_agent = choice(self._connections)
        remote_agent = await self.env.connect(r_agent.addr)
        return remote_agent

    def publish(self, artifact):
        '''Publish artifact to agent's environment.

        :param artifact: artifact to be published
        :type artifact: :py:class:`~creamas.core.artifact.Artifact`
        '''
        self.env.add_artifact(artifact)
        self._log(logging.DEBUG, "Published {} to domain.".format(artifact))

    def refill(self):
        '''Refill agent's resources to maximum.'''
        self._cur_res = self._max_res

    def evaluate(self, artifact):
        r'''Evaluate artifact with agent's current rules and weights.

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

            e(A) = \frac{\sum_{i=1}^{n} r_{i}(A)w_i}
            {\sum_{i=1}^{n} \lvert w_i \rvert},

        where :math:`r_{i}(A)` is the :math:`i` th rule's evaluation on
        artifact :math:`A`, and :math:`w_i` is the weight for rule
        :math:`r_i`.
        '''
        s = 0
        w = 0.0
        if len(self.R) == 0:
            return 0.0, None

        for i in range(len(self.R)):
            s += self.R[i](artifact) * self.W[i]
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
        ret = await remote_agent.evaluate_pickle(pkl)
        ev = pickle.loads(ret)
        return ev

    @aiomas.expose
    async def act(self):
        '''Trigger agent to act. **Dummy method, override in subclass.**

        :raises NotImplementedError: if not overridden in subclass

        .. note::

            This is an async method that should be awaited.
        '''
        raise NotImplementedError('Override in subclass.')

    def validate_candidates(self, candidates):
        '''Validate list of candidate artifacts.
        '''
        return candidates

    @aiomas.expose
    def vote(self, candidates):
        '''Rank artifact candidates based on agent's own *evaluate*-method.

        :param candidates:
            list of :py:class:`~creamas.core.artifact.Artifact` objects to be
            ranked

        :returns:
            ordered list of (candidate, evaluation)-tuples
        '''
        ranks = [(c, self.evaluate(c)[0]) for c in candidates]
        ranks.sort(key=operator.itemgetter(1), reverse=True)
        return ranks

    @aiomas.expose
    async def get_older(self):
        '''Age agent by one simulation step.'''
        self._age = self._age + 1

    def _log(self, level, msg):
        if self.logger is not None:
            self.logger.log(level, msg)

    @aiomas.expose
    def close(self, folder=None):
        '''Perform any bookkeeping needed before closing the agent.

        **Dummy implementation, override in subclass if needed.**
        '''
        pass

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.name)
