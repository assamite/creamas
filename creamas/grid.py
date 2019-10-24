"""
.. py:module:: grid
    :platform: Unix

The module holds implementations for 2D-grid environments where the agents
know their neighbors in each of the four cardinal directions. Currently
implemented are:

    * :class:`~creamas.grid.GridAgent`: The base grid agent implementation,
      should be used inside :class:`~creamas.grid.GridEnvironment`. Agent
      places itself in the environment's
      :attr:`~creamas.grid.GridEnvironment.grid` and knows its neighbors
      in the cardinal directions: N, E, S, W. Subclass the agent for your
      specific needs.

    * :class:`~creamas.grid.GridEnvironment`: A single process grid
      environment.

    * :class:`~creamas.grid.GridEnvManager`: A manager for a single process
      grid environment.

    * :class:`~creamas.grid.GridMultiEnvironment`: Multi-processing environment
      holding several :class:`~creamas.grid.GridEnvironment` slaves with
      managers.

    * :class:`~creamas.grid.GridMultiEnvManager`: A manager for a
      multi-processing environment. Used especially if the environment needs to
      be able to execute commands from external sources, e.g. when used as a
      part of :class:`creamas.ds.DistributedEnvironment`.
"""
import asyncio
import logging
import traceback

import aiomas

from creamas import CreativeAgent, Environment
from creamas.mp import MultiEnvironment, MultiEnvManager, EnvManager

# Relative xy coordinates for the cardinal directions
_rel_xy = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
_polars = {'N': 'S', 'E': 'W', 'S': 'N', 'W': 'E'}


def _get_neighbor_xy(card, xy):
    rxy = _rel_xy[card]
    return xy[0] + rxy[0], xy[1] + rxy[1]


class GridAgent(CreativeAgent):
    """An agent living in a 2D-grid with four neighbors in cardinal directions.

    The agent assumes that its environment is derived from
    :class:`~creamas.grid.GridEnvironment`, and places itself into the grid
    when it is initialized.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._xy = self.env.add_to_grid(agent=self)
        self.name = "{}-{}({})".format(self._xy[0], self._xy[1], self.addr)
        self._neighbors = {'N': None, 'E': None, 'S': None, 'W': None}

    @property
    def xy(self):
        """Agent's place (coordinate) in the grid, (x, y)-tuple.
        """
        return self._xy

    @property
    def neighbors(self):
        """Map of neighboring agent addresses in cardinal directions:
        N, E, S, W.
        """
        return self._neighbors

    async def send(self, card, msg):
        """Send message *msg* to the neighboring agent in the *card*
        cardinal direction.

        :param str card: 'N', 'E', 'S', or 'W'.
        :param msg: Message to the agent.
        :returns: Response from the agent

        The method calls the neighboring agent's :meth:`rcv` with the message
        and returns any value returned by that agent.

        This method will fail silently if there is no neighbor agent in the
        given cardinal direction.
        """
        addr = self.neighbors[card]
        if addr is None:
            return None
        try:
            r_agent = await self.env.connect(addr, timeout=10)
            return await r_agent.rcv(msg)
        except:
            self._log(logging.WARNING, "Could not connect to agent in {}:\n{}"
                      .format(addr, traceback.format_exc()))
        return None

    @aiomas.expose
    async def rcv(self, msg):
        """Receive and handle message coming from another agent.

        This method is called from :meth:`send`.

        The base implementation does nothing, override in a subclass.
        """
        pass

    @aiomas.expose
    async def act(self, *args, **kwargs):
        """See :py:class:`creamas.core.agent.CreativeAgent.act`.
        """
        pass


class GridEnvironment(Environment):
    """Environment where agents reside in a 2D-grid.

    Each agent is connected to neighbors in cardinal directions: N, E, S, W.
    Grid environments can be horizontally stacked with
    :py:class:`GridMultiEnvironment`.
    """
    def __init__(self, base_url, loop, clock, connect_kwargs):
        super().__init__(base_url, loop, clock, connect_kwargs)
        self._gs = (0, 0)
        self._grid = []
        self._origin = (0, 0)
        self._neighbors = {'N': None, 'E': None, 'S': None, 'W': None}

    @property
    def gs(self):
        """Size of the grid as a 2-tuple. Changing the size of the grid after
        spawning any agents in the environment will clear the grid, but does
        not remove the agents from the environment.
        """
        return self._gs

    @gs.setter
    def gs(self, gs):
        self._gs = gs
        self._grid = [[None for _ in range(self._gs[1])]
                      for _ in range(self._gs[0])]

    @property
    def origin(self):
        """Upper left corner of the grid, [0,0] by default.

        You should define the origin before spawning any agents into the
        environment.
        """
        return self._origin

    @origin.setter
    def origin(self, origin):
        self._origin = origin

    @property
    def grid(self):
        """The agents in the grid. 2D-list with the same size as **gs**.
        """
        return self._grid

    @property
    def neighbors(self):
        """Map of neighboring grid environments in cardinal directions.

        Acceptable keys: N, E, S, W.

        The values are **the addresses of the managers** in the neighboring
        grid environments.
        """
        return self._neighbors

    def is_ready(self):
        """Grid environment is ready when its grid is full.

        .. seealso::

            :meth:`GridEnvironment.is_full`, :meth:`Environment.is_ready`
        """
        return self.is_full()

    def is_full(self):
        """:class:`GridEnvironment` is full when its **grid** is fully
        populated with agents.

        :returns:
            True if the grid is full, False otherwise. Will also return False
            for uninitialized grids with (0,0) grid size.
        """
        if len(self.grid) == 0:
            return False

        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if self.grid[i][j] is None:
                    return False
        return True

    def add_to_grid(self, agent):
        """Add agent to the next available spot in the grid.

        :returns:
            (x,y) of the agent in the grid. This is the agent's overall
            coordinate in the grand grid (i.e. the actual coordinate of the
            agent w.t.r **origin**).

        :raises: `ValueError` if the grid is full.
        """
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if self.grid[i][j] is None:
                    x = self.origin[0] + i
                    y = self.origin[1] + j
                    self.grid[i][j] = agent
                    return (x, y)

        raise ValueError("Trying to add an agent to a full grid."
                         .format(len(self._grid[0]), len(self._grid[1])))

    def get_xy(self, xy, addr=True):
        """Get the agent with xy-coordinate in the grid. If *addr* is True,
        returns only the agent's address.

        If no such agent in the grid, returns None.

        :raises:
            :exc:`ValueError` if xy-coordinate is outside the environment's
            grid.
        """
        x = xy[0]
        y = xy[1]
        if x < self.origin[0] or x >= self.origin[0] + self.gs[0]:
            raise ValueError("x-coordinate inappropriate ({})".format(x))
        if y < self.origin[1] or y >= self.origin[1] + self.gs[1]:
            raise ValueError("y-coordinate inappropriate ({})".format(y))

        i = x - self.origin[0]
        j = y - self.origin[1]
        if addr:
            return self.grid[i][j].addr
        return self.grid[i][j]

    async def _get_xy_address_from_neighbor(self, card, xy):
        if self.neighbors[card] is None:
            return None
        r_manager = await self.connect(self.neighbors[card])
        addr = await r_manager.get_xy_address(xy)
        return addr

    async def set_agent_neighbors(self):
        """Set neighbors for each agent in each cardinal direction.

        This method assumes that the neighboring :class:`GridEnvironment` of
        this grid environment have already been set.
        """
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                agent = self.grid[i][j]
                xy = (self.origin[0] + i, self.origin[1] + j)
                nxy = _get_neighbor_xy('N', xy)
                exy = _get_neighbor_xy('E', xy)
                sxy = _get_neighbor_xy('S', xy)
                wxy = _get_neighbor_xy('W', xy)
                if j == 0:
                    naddr = await self._get_xy_address_from_neighbor('N', nxy)
                else:
                    naddr = self.get_xy(nxy, addr=True)
                if i == 0:
                    waddr = await self._get_xy_address_from_neighbor('W', wxy)
                else:
                    waddr = self.get_xy(wxy, addr=True)
                if j == len(self.grid[0]) - 1:
                    saddr = await self._get_xy_address_from_neighbor('S', sxy)
                else:
                    saddr = self.get_xy(sxy, addr=True)
                if i == len(self.grid) - 1:
                    eaddr = await self._get_xy_address_from_neighbor('E', exy)
                else:
                    eaddr = self.get_xy(exy, addr=True)
                agent.neighbors['N'] = naddr
                agent.neighbors['E'] = eaddr
                agent.neighbors['S'] = saddr
                agent.neighbors['W'] = waddr


class GridEnvManager(EnvManager):
    """Manager for :py:class:`GridEnvironment`.
    """
    @aiomas.expose
    async def spawn_n(self, agent_cls, n, *args, **kwargs):
        """Spawn *n* agents to the managed environment. This is a convenience
        function so that one does not have to repeatedly make connections to
        the environment to spawn multiple agents with the same parameters.

        See :py:meth:`~creamas.mp.EnvManager.spawn` for details.
        """
        rets = []
        for _ in range(n):
            ret = await self.spawn(agent_cls, *args, **kwargs)
            rets.append(ret)
        return rets

    @aiomas.expose
    def get_xy_address(self, xy):
        """Get address of the agent in *xy* coordinate, or None if no such
        agent exists.
        """
        return self.env.get_xy(xy, addr=True)

    @aiomas.expose
    def set_origin(self, origin):
        """Set originating coordinates for the managed environment.
        """
        self.env.origin = origin

    @aiomas.expose
    def get_origin(self):
        return self.env.origin

    @aiomas.expose
    def set_gs(self, gs):
        """Set grid size for the managed environment.
        """
        self.env.gs = gs

    @aiomas.expose
    def get_gs(self):
        return self.env.gs

    @aiomas.expose
    async def set_grid_neighbor(self, card, addr):
        """Set the neighbor grid for the grid in *card* cardinal direction.
        The *addr* should point to thanager* of the neighboring grid.
        """
        self.env.neighbors[card] = addr

    @aiomas.expose
    async def set_agent_neighbors(self):
        """Set neighboring agents for all the agents in the grid.

        If the  managed grid contains neighboring grids, uses those to
        correctly set also neighboring agents for agents on the edge of the
        grid.

        This function assumes that:

            * Grid is full, i.e. it has maximum number of agents.
            * All the (possible) neighboring grids have been initialized and
              have the maximum number of agents. That is, if managed grid's
              neighbor map still points to ``None``, this grid is assumed to be
              in the edge of the super-grid containing multiple
              :py:class:`GridEnvironment` instances.

        """
        await self.env.set_agent_neighbors()


class GridMultiEnvironment(MultiEnvironment):
    """Multi-environment which stacks its slave :py:class:`GridEnvironment`
    instances horizontally.

    Call :meth:`creamas.grid.GridMultiEnvironment.set_slave_params` immediately
    after initializing :class:`GridMultiEnvironment`!

    .. note::

        The manager agents for the slave environments will not be part of
        :attr:`~creamas.grid.GridEnvironment.grid` in the slave environments.

    """
    def __init__(self, *args, **kwargs):
        self._gs = kwargs.pop('grid_size')
        self._origin = kwargs.pop('origin')
        super().__init__(*args, **kwargs)
        self._neighbors = {'N': None, 'E': None, 'S': None, 'W': None}

    async def spawn_slaves(self, *args, **kwargs):
        await super().spawn_slaves(*args, **kwargs)
        self._n_slaves = len(kwargs['slave_addrs'])
        self._end_coord = (self.origin[0] + (self.gs[0] * self._n_slaves) - 1,
                           self.origin[1] + self.gs[1] - 1)

    async def set_slave_params(self):
        """Set origin and grid size for each slave environment.

        This method needs to be called before slave environments are populated
        and agents' and slave environments' neighbors are set.
        """
        self._slave_origins = []
        cur_x = self.origin[0]
        for addr in self.addrs:
            new_origin = (cur_x, self.origin[1])
            await self.set_origin(addr, new_origin)
            await self.set_gs(addr, self._gs)
            self._slave_origins.append((new_origin, addr))
            new_x = cur_x + self.gs[0]
            cur_x = new_x

    @property
    def origin(self):
        """Origin of this multi-environment (the *xy* coordinate of the first
        agent in the first slave environment).
        """
        return self._origin

    @property
    def gs(self):
        """Grid size for each slave environment.
        """
        return self._gs

    async def set_gs(self, addr, gs):
        r_agent = await self.env.connect(addr)
        return await r_agent.set_gs(gs)

    async def get_gs(self, addr):
        r_agent = await self.env.connect(addr)
        return await r_agent.get_gs()

    async def set_origin(self, addr, origin):
        r_agent = await self.env.connect(addr)
        return await r_agent.set_origin(origin)

    async def get_origin(self, addr):
        r_agent = await self.env.connect(addr)
        return await r_agent.get_origin()

    @property
    def neighbors(self):
        """Map of neighboring multi-environments for this multi-environment.
        The map's values are *manager addresses* for the neighbors.
        """
        return self._neighbors

    def get_xy_environment(self, xy):
        """Get manager address for the environment which should have the agent
        with given *xy* coordinate, or None if no such environment is in this
        multi-environment.
        """
        x = xy[0]
        y = xy[1]
        for origin, addr in self._slave_origins:
            ox = origin[0]
            oy = origin[1]
            if ox <= x < ox + self.gs[0] and oy <= y < oy + self.gs[1]:
                return addr
        return None

    async def get_xy_address(self, xy):
        """Get address of the agent residing in *xy* coordinate, or ``None``
        if no such agent is in this multi-environment.
        """
        manager_addr = self.get_xy_environment(xy)
        if manager_addr is None:
            return None
        else:
            r_agent = await self._env.connect(manager_addr)
            xy_addr = await r_agent.get_xy_address(xy)
            return xy_addr

    async def set_slave_neighbors(self):
        """Set neighbor environments for all the slave environments. Assumes
        that :attr:`neighbors` are set for this multi-environment.
        """
        for i, elem in enumerate(self._slave_origins):
            o, addr = elem
            r_slave = await self.env.connect(addr)
            nxy = _get_neighbor_xy('N', o)
            exy = _get_neighbor_xy('E', (o[0] + self.gs[0] - 1, o[1]))
            sxy = _get_neighbor_xy('S', (o[0], o[1] + self.gs[1] - 1))
            wxy = _get_neighbor_xy('W', o)
            if i == 0 and self.neighbors['W'] is not None:
                m_addr = self.neighbors['W']
                r_manager = await self.env.connect(m_addr)
                n_addr = await r_manager.get_xy_environment(wxy)
                await r_slave.set_grid_neighbor('W', n_addr)
            elif i == self._n_slaves - 1 and self.neighbors['E'] is not None:
                m_addr = self.neighbors['E']
                r_manager = await self.env.connect(m_addr)
                n_addr = await r_manager.get_xy_environment(exy)
                await r_slave.set_grid_neighbor('E', n_addr)
            else:
                w_addr = self.get_xy_environment(wxy)
                e_addr = self.get_xy_environment(exy)
                await r_slave.set_grid_neighbor('W', w_addr)
                await r_slave.set_grid_neighbor('E', e_addr)

            if self.neighbors['N'] is not None:
                m_addr = self.neighbors['N']
                r_manager = await self.env.connect(m_addr)
                n_addr = await r_manager.get_xy_environment(nxy)
                await r_slave.set_grid_neighbor('N', n_addr)

            if self.neighbors['S'] is not None:
                m_addr = self.neighbors['S']
                r_manager = await self.env.connect(m_addr)
                n_addr = await r_manager.get_xy_environment(sxy)
                await r_slave.set_grid_neighbor('S', n_addr)

    async def set_agent_neighbors(self):
        """Set neighbors for all the agents in all the slave environments.
        Assumes that all the slave environments have their neighbors set.
        """
        for addr in self.addrs:
            r_manager = await self.env.connect(addr)
            await r_manager.set_agent_neighbors()

    async def set_neighbors(self):
        """Set neighbors for all slave environments and agents in them.

        This is a convenience function for calling
        :meth:`~creamas.grid.GridMultiEnvironment.set_slave_neighbors` and
        :meth:`~creamas.grid.GridMultiEnvironment.set_agent_neighbors`.
        """
        await self.set_slave_neighbors()
        await self.set_agent_neighbors()

    async def _populate_slave(self, addr, agent_cls, n, *args, **kwargs):
        r_manager = await self.env.connect(addr, timeout=5)
        ret = await r_manager.spawn_n(agent_cls, n, *args, **kwargs)
        return ret

    async def populate(self, agent_cls, *args, **kwargs):
        """Populate all the slave grid environments with agents. Assumes that
        no agents have been spawned yet to the slave environment grids. This
        excludes the slave environment managers as they are not in the grids.)
        """
        n = self.gs[0] * self.gs[1]
        tasks = []
        for addr in self.addrs:
            task = asyncio.ensure_future(self._populate_slave(addr, agent_cls,
                                                              n, *args,
                                                              **kwargs))
            tasks.append(task)
        rets = await asyncio.gather(*tasks)
        return rets


class GridMultiEnvManager(MultiEnvManager):
    """Manager agent for :py:class:`GridMultiEnvironment`.
    """
    @aiomas.expose
    async def set_origin(self, mgr_addr, origin):
        """Set originating coordinates for :py:class:`GridEnvironment` which
        manager is in given address.

        :param str mgr_addr: Address of the manager agent

        :param origin:
            New origin of the grid environment, iterable with length 2.
        """
        remote_manager = await self.env.connect(mgr_addr)
        await remote_manager.set_origin(origin)

    @aiomas.expose
    async def set_gs(self, mgr_addr, gs):
        """Set grid size for :py:class:`GridEnvironment` which manager is in
        given address.

        :param str mgr_addr: Address of the manager agent

        :param gs:
            New grid size of the grid environment, iterable with length 2.
        """
        remote_manager = await self.env.connect(mgr_addr)
        await remote_manager.set_gs(gs)

    @aiomas.expose
    def set_grid_neighbor(self, card, addr):
        """Set the neighbor multi-grid for this multi-grid in *card* cardinal
        direction. The *addr* should point to the *manager* of the neighboring
        multi-grid.
        """
        self.menv.neighbors[card] = addr

    @aiomas.expose
    async def get_xy_address(self, xy):
        """Get address of the agent in the environment with given coordinates.

        This is a managing function for
        :meth:`~creamas.grid.MultiEnvironment.get_xy_address`.

        """
        ret = await self.menv.get_xy_address(xy)
        return ret

    @aiomas.expose
    def get_xy_environment(self, xy):
        """Get environment (address of the manager of that environment) which
        has agent with given coordinates.

        This is a managing function for
        :meth:`~creamas.grid.MultiEnvironment.get_xy_environment`.
        """
        return self.menv.get_xy_environment(xy)

    @aiomas.expose
    async def set_slave_neighbors(self):
        """Set neighbor environments for all the slave environments.

        This is a managing function for
        :meth:`creamas.grid.GridMultiEnvironment.set_slave_neighbors`.
        """
        await self.menv.set_slave_neighbors()

    @aiomas.expose
    async def set_agent_neighbors(self):
        """Set neighbor agents for all the agents in the slave environments.

        This is a managing function for
        :meth:`creamas.grid.GridMultiEnvironment.set_agent_neighbors`.
        """
        await self.menv.set_agent_neighbors()

    @aiomas.expose
    async def set_neighbors(self):
        """Set neighbors for all the agents in all the slave environments.

        This is a managing function for
        :meth:`creamas.grid.GridMultiEnvironment.set_neighbors`.
        """
        await self.menv.set_neighbors()
