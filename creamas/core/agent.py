"""
.. py:module:: agent
    :platform: Unix

Agent module holds :class:`CreativeAgent` implementation, a subclass of
:class:`aiomas.Agent`, which holds basic functionality thought to be shared by
creative agents.
"""
import logging
import re
from random import choice

from aiomas import Agent

from creamas.core.artifact import Artifact
from creamas.logging import ObjectLogger
from creamas.util import expose

__all__ = ['CreativeAgent']


class CreativeAgent(Agent):
    """Base class for all creative agents.

    All agents share certain common attributes:

    :ivar ~creamas.core.agent.CreativeAgent.env:
        The environment where the agent lives.

    :ivar int max_res:
        Agent's resources per step, 0 if agent has unlimited resources.

    :ivar int cur_res:
        Agent's current resources.

    :ivar list A:
        Artifacts the agent has created so far

    :ivar dict D:
        Domain knowledge, other agents' artifacts seen by this agent

    :ivar list connections:
        Dictionary of other agents this agent knows

    :ivar str ~creamas.core.agent.CreativeAgent.name:
        Name of the agent. Defaults to the address of the agent.
    """
    def __init__(self, environment, resources=0, name=None, log_folder=None,
                 log_level=logging.DEBUG):
        super().__init__(environment)
        self._env = environment
        self._max_res = resources
        self._cur_res = resources
        self._A = []
        self._D = {}
        self._connections = {}

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
        """The name of the agent.

        The agent should not change its name during its lifetime.
        """
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def logger(self):
        """A logger for the agent.

        The logger should be derived from
        :class:`~creamas.logging.ObjectLogger`.
        """
        return self._logger

    @logger.setter
    def logger(self, l):
        self._logger = l

    def sanitized_name(self):
        """Sanitized name of the agent, used for file and directory creation.
        """
        a = re.split("[:/]", self.name)
        return "_".join([i for i in a if len(i) > 0])

    @property
    def env(self):
        """The environment where the agent lives. Must be a subclass of
        :py:class:`~creamas.core.environment.Environment`.
        """
        return self._env

    @property
    def A(self):
        """Artifacts created so far by the agent.
        """
        return self._A

    @property
    def D(self):
        """Domain knowledge accumulated by this agent.

        Dictionary of agents and their artifacts.
        """
        return self._D

    @property
    def max_res(self):
        """Maximum resources for the agent per simulation iteration act.

        If ``max_res == 0``, agent has unlimited resources. If maximum
        resources are set below current resources, current resources are
        capped to new maximum resources.
        """
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
        """Agent's current resources. Capped to maximum resources.
        """
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
        """Known other agents

        The connections has a dict-in-a-dict data type able to hold arbitrary
        information about known other agents. The keys in the dictionary are
        agent addresses and values are dictionaries holding information
        relating to the key-agent.
        """
        return self._connections

    def qualname(self):
        """Get qualified name of this class.
        """
        return "{}:{}".format(self.__module__, self.__class__.__name__)

    def add_artifact(self, artifact):
        """Add artifact to :attr:`A`.

        :raises TypeError:
            If the artifact is not derived from
            :class:`~creamas.core.artifact.Artifact`.
        """
        if not issubclass(artifact.__class__, Artifact):
            raise TypeError("Artifact to add ({}) is not {}."
                            .format(artifact, Artifact))
        self._A.append(artifact)

    @expose
    def add_connection(self, addr, **kwargs):
        """Add an agent with given address to current :attr:`connections` with
        given information.

        Does nothing if address is already in :attr:`connections`. Given
        ``**kwargs`` are stored as key-value pairs to ``connections[addr]``
        dictionary.

        :param str addr:
            Address of the agent to be added
        :returns:
            ``True`` if the agent was successfully added, ``False`` otherwise.
        """
        if addr not in self._connections:
            self.connections[addr] = {}
            for k, v in kwargs.items():
                self.connections[addr][k] = v
            return True
        return False

    @expose
    def add_connections(self, conns):
        """Add agents from :attr:`conns` to :attr:`connections`.

        :param list conns: A list of ``(addr, kwargs)``-tuples
        :returns:
            A boolean list, as returned by
            :meth:`~creamas.core.agent.CreativeAgent.add_connections`.
        """
        rets = []
        for addr, kwargs in conns:
            r = self.add_connection(addr, **kwargs)
            rets.append(r)
        return rets

    @expose
    def remove_connection(self, addr):
        """Remove agent with given address from current connections.
        """
        return self._connections.pop(addr, None)

    @expose
    def clear_connections(self):
        """Clear all connections from the agent.
        """
        self._connections = {}

    @expose
    def get_connections(self, data=False):
        """Get agent's current connections.

        :param bool data:
            Also return the data dictionary for each connection.

        :returns: A list of agent addresses or a dictionary
        """
        if data:
            return self._connections
        return list(self._connections.keys())

    async def connect(self, addr):
        """Connect to agent in given address using the agent's environment.

        This is a shortcut to
        :meth:`~creamas.core.environment.Environment.connect`.

        :returns: :class:`aiomas.Proxy` object for the connected agent.
        """
        return await self.env.connect(addr)

    async def random_connection(self):
        """Connect to random agent from current :attr:`connections`.

        :returns: :class:`aiomas.Proxy` object for the connected agent.
        """
        addr = choice(list(self._connections.keys()))
        return await self.env.connect(addr)

    def publish(self, artifact):
        """Publish artifact to agent's environment.

        :param artifact: artifact to be published
        :type artifact: :py:class:`~creamas.core.artifact.Artifact`
        """
        self.env.add_artifact(artifact)
        self._log(logging.DEBUG, "Published {} to domain.".format(artifact))

    def refill(self):
        """Refill agent's resources to maximum."""
        self._cur_res = self._max_res

    @expose
    def evaluate(self, artifact):
        """Evaluate an artifact.

        ** This is a dummy method which should be overridden in a subclass. **
        """
        return 0.0, None

    async def ask_opinion(self, addr, artifact):
        """Ask an agent's opinion about an artifact.

        :param str addr: Address of the agent which opinion is asked
        :type addr: :py:class:`~creamas.core.agent.CreativeAgent`
        :param object artifact: artifact to be evaluated
        :returns: agent's evaluation of the artifact
        :rtype: float

        This is a shortcut to::

            remote_agent = await self.env.connect(addr)
            opinion = await remote_agent.evaluate(artifact)

        .. note::

            The artifact object should be serializable by the environment.
        """
        remote_agent = await self.env.connect(addr)
        return await remote_agent.evaluate(artifact)

    @expose
    async def act(self, *args, **kwargs):
        """Trigger agent to act.

        **This is a dummy method which should be overridden in a subclass.**

        This function serves as the main function for the simulations, and
        is called for each agent on each step of the simulation.

        .. seealso::

            :meth:`~creamas.core.environment.Environment.trigger_all`
        """
        return args, kwargs

    def _log(self, level, msg):
        if self.logger is not None:
            self.logger.log(level, msg)

    @expose
    def close(self, folder=None):
        """Perform any bookkeeping needed before closing the agent.

        **This is a dummy method which should be overridden in a subclass.**

        :param str folder: Folder where the agent should save its data.
        """
        pass

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.name)
