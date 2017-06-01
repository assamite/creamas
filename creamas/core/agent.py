'''
.. py:module:: agent
    :platform: Unix

Agent module holds **CreativeAgent** implementation, a subclass of
``aiomas.Agent``, which holds basic functionality thought to be shared by
creative agents.
'''
import logging
from random import choice
import re

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
        Name of the agent. Defaults to the address of the agent.
    '''
    def __init__(self, environment, resources=0, name=None, log_folder=None,
                 log_level=logging.DEBUG):
        super().__init__(environment)
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
            self._logger = ObjectLogger(self, log_folder, add_name=True,
                                        init=True, log_level=log_level)
        else:
            self._logger = None

    @property
    def name(self):
        '''Name of the agent. The agent should not change its
        name during its lifetime.'''
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def logger(self):
        '''Logger of the agent. Should be derived from
        :class:`~creamas.logging.ObjectLogger`.
        '''
        return self._logger

    @logger.setter
    def logger(self, l):
        self._logger = l

    def sanitized_name(self):
        '''Sanitized name of the agent, used for file and directory creation.
        '''
        a = re.split("[:/]", self.name)
        return "_".join([i for i in a if len(i) > 0])

    @property
    def env(self):
        '''The environment where the agent lives. Must be a subclass of
        :py:class:`~creamas.core.environment.Environment`.'''
        return self._env

    @property
    def R(self):
        '''Rules agent uses to evaluate artifacts. Each rule in **R** is
        expected to be a callable with a single parameter, the artifact to be
        evaluated. Callable should return a float in [-1,1]; where 1 means that
        rule is very prominent in the artifact; 0 means that there is none of
        that rule in the artifact; -1 means that the artifact shows
        traits opposite to the rule.
        '''
        return self._R

    @property
    def W(self):
        '''Weights for the features. Each weight should be in [-1,1].'''
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
        '''Addresses of known other agents in the society/simulation.'''
        return self._connections

    @property
    def attitudes(self):
        '''Attitudes towards agents in :attr:`connections`.'''
        return self._attitudes

    def qualname(self):
        '''Get qualified name of this class.
        '''
        return "{}:{}".format(self.__module__, self.__class__.__name__)

    def get_attitude(self, addr):
        '''Get attitude towards agent in **connections**. If agent is not in
        **connections**, returns None.
        '''
        try:
            ind = self._connections.index(addr)
            return self._attitudes[ind]
        except:
            return None

    def set_attitude(self, addr, attitude):
        '''Set attitude towards agent. If agent is not in **connections**, adds
        it.
        '''
        try:
            ind = self._connections.index(addr)
            self._attitudes[ind] = attitude
        except:
            self.add_connection(addr, attitude)

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
        '''Add artifact to **A**.

        :raises TypeError:
            If the artifact is not a member of
            :class:`~creamas.core.artifact.Artifact` or its subclass.
        '''
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
        if not issubclass(rule.__class__, (Rule, RuleLeaf)):
            raise TypeError("Rule to add ({}) must be derived from {} or {}."
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

    @aiomas.expose
    def add_connection(self, addr, attitude=0.0):
        '''Add an agent with given address to current :attr:`connections` with
        given initial attitude.

        Does nothing if address is already in :attr:`connections`.

        :param str addr: Address of the agent to be added
        :param float attitude: initial attitude towards agent, in [-1, 1]
        :returns: True if the agent was successfully added, False otherwise.
        '''
        if addr not in self._connections:
            self.connections.append(addr)
            self.attitudes.append(attitude)
            return True
        return False

    @aiomas.expose
    def add_connections(self, conns):
        '''Add agents from *conns* to :attr:`connections`.

        :param list conns: A list of (addr, attitude)-tuples
        '''
        rets = []
        for addr, att in conns:
            r = self.add_connection(addr, att)
            rets.append(r)
        return rets

    @aiomas.expose
    def remove_connection(self, addr):
        '''Remove agent with given address from current connections.'''
        try:
            ind = self._connections.index(addr)
            del self._connections[ind]
            del self._attitudes[ind]
            return True
        except:
            return False

    @aiomas.expose
    def get_connections(self, attitudes=False):
        '''Get agent's current connections.

        :param bool attitudes:
            If ``True``, returns a list of (address, attitude)-tuples,
            otherwise returns a list of addresses.

        :returns: A list of connections or (connection, attitude)-tuples.
        '''
        if attitudes:
            return list(zip(self._connections, self._attitudes))
        return self._connections

    async def connect(self, addr):
        '''Connect to agent in given address using the agent's environment.

        This is a shortcut to
        :meth:`~creamas.core.enviroment.Environment.connect`.

        :returns: :class:`aiomas.Proxy` object for the connected agent.
        '''
        remote_agent = await self.env.connect(addr)
        return remote_agent

    async def random_connection(self):
        '''Connect to random agent from current :attr:`connections`.

        :returns: :class:`aiomas.Proxy` object for the connected agent.
        '''
        addr = choice(self._connections)
        remote_agent = await self.env.connect(addr)
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

    @aiomas.expose
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

        Actual evaluation formula in this basic implementation is:

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

    async def ask_opinion(self, addr, artifact):
        '''Ask an agent's opinion about an artifact.

        :param str addr: Address of the agent which opinion is asked
        :type agent: :py:class:`~creamas.core.agent.CreativeAgent`
        :param object artifact: artifact to be evaluated
        :returns: agent's evaluation of the artifact
        :rtype: float

        This is a shortcut to::

            remote_agent = await self.env.connect(addr)
            opinion = await remote_agent.evaluate(artifact)

        .. note::

            The artifact object should be serializable by the environment.
        '''
        remote_agent = await self.env.connect(addr)
        ret = await remote_agent.evaluate(artifact)
        return ret

    @aiomas.expose
    async def act(self, *args, **kwargs):
        '''Trigger agent to act. **Dummy method, override in subclass.**

        This function serves as the main function for the simulations, and
        is called for each agent on each iteration step of the simulation.

        :raises NotImplementedError: If not overridden in subclass.
        '''
        raise NotImplementedError('Override in subclass.')

    def _log(self, level, msg):
        if self.logger is not None:
            self.logger.log(level, msg)

    @aiomas.expose
    def close(self, folder=None):
        '''Perform any bookkeeping needed before closing the agent.

        **Dummy implementation, override in subclass if needed.**

        :param str folder: Folder where the agent should save its data.
        '''
        pass

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.name)
