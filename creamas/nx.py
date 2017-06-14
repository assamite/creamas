'''
.. py:module:: nx
    :platform: Unix

Functions to create agent connections from
`NetworkX <https://networkx.github.io/>`_ graph structures and NetworkX graphs
from agent connections.

.. note::

    NetworkX has to be installed in order for the functions in this module to
    work. It is not installed as a default dependency.

    Use, e.g. ``pip install networkx``

'''
from networkx import Graph, DiGraph

from creamas.util import sort_addrs


def connections_from_graph(env, G, weight_key=None):
    '''Create connections for agents in the given environment from the given
    NetworkX graph structure.

    :param env:
        Environment where the agents live. The environment should be derived
        from :class:`~creamas.core.environment.Environment`,
        :class:`~creamas.mp.MultiEnvironment` or
        :class:`~creamas.ds.DistributedEnvironment`.

    :param G:
        NetworkX graph structure, either :class:`networkx.graph.Graph` or
        :class:`networkx.digraph.DiGraph`. The graph needs to have the same
        number of nodes as the environment has agents (excluding the managers).

    :param weight_key:
        Optional. If specified, the key is used to extract edge weights
        from the graph for each agent connection that is created. The
        connection weights are stored in the agents as :attr:`attitudes`
        towards other agents.

    .. note::

        By design, manager agents are excluded from the connections and should
        not be counted towards environment's agent count.

    The created connections are stored in each agent's
    :attr:`~creamas.core.agent.CreativeAgent.connections` and the possible
    ``weight_key`` is used for priming
    :attr:`~creamas.core.agent.CreativeAgent.attitudes` towards each remote
    agent. If ``weight_key`` is not given, then all attitudes are primed to
    0.0.

    The agents are sorted by their environments' hosts and ports before each
    agent is mapped to a node in **G**. This should cause some network
    generation methods in NetworkX, e.g.
    :func:`~networkx.generators.random_graphs.connected_watts_strogatz_graph`,
    to create more connections between agents in the same environment and/or
    node when using :class:`~creamas.mp.MultiEnvironment` or
    :class:`~creamas.ds.DistributedEnvironment`.
    '''
    if not issubclass(G.__class__, (Graph, DiGraph)):
        raise TypeError("Graph structure must be derived from Networkx's "
                        "Graph or DiGraph.")
    if not hasattr(env, 'get_agents'):
        raise TypeError("Parameter 'env' must have get_agents.")

    addrs = env.get_agents(addr=True)
    if len(addrs) != len(G):
        raise ValueError("The number of graph nodes and agents in the "
                         "environment (excluding the manager agent) must "
                         "match. Now got {} nodes and {} agents."
                         .format(len(G), len(addrs)))
    # Sort agent addresses to the order they were added to the environment.
    addrs = sort_addrs(addrs)
    _addrs2nodes(addrs, G)
    conn_map = _edges2conns(G, weight_key)
    env.create_connections(conn_map)


def graph_from_connections(env, directed=False):
    '''Create NetworkX graph from agent connections in a given environment.

    :param env:
        Environment where the agents live. The environment must be derived from
        :class:`~creamas.core.environment.Environment`,
        :class:`~creamas.mp.MultiEnvironment` or
        :class:`~creamas.ds.DistributedEnvironment`.

    :param bool directed:
        If ``True``, creates an instance of :class:`~networkx.digraph.DiGraph`,
        otherwise creates an instance of :class:`~networkx.graph.Graph`.

    :returns: The created NetworkX graph.
    :rtype:
        :class:`~networkx.digraph.DiGraph` or :class:`~networkx.graph.Graph`

    .. note::

        If the created graph is undirected and two connected agents have
        different attitudes towards each other, then the value of
        ``"attitude"`` key in the resulting graph for the edge is chosen
        randomly from the two values.
    '''
    G = DiGraph() if directed else Graph()
    conn_list = env.get_connections(attitudes=True)
    for agent, conns in conn_list:
        ebunch = []
        for nb, att in conns:
            ebunch.append((agent, nb, {'attitude': att}))
        if len(ebunch) > 0:
            G.add_edges_from(ebunch)
    return G


def _addrs2nodes(addrs, G):
    '''Map agent addresses to nodes in the graph.
    '''
    for i, n in enumerate(G.nodes()):
        G.node[n]['addr'] = addrs[i]


def _edges2conns(G, weight_key=None):
    '''Create a mapping from graph edges to agent connections to be created.

    :param G:
        NetworkX's Graph or DiGraph which has :attr:`addr` attribute for each
        node.

    :param str weight_key:
        Optional. If specified, the returned connection mapping will return
        a list of (neighbor, weight)- tuples for each address key. The weights
        are extracted from the graph with given ``weight_key``, i.e.
        ``G[n][nb][weight_key] = 0.1`` will result in a tuple ``(nb, 0.1)``
        for a key ``n`` in the returned connection mapping.

    :returns:
        A dictionary where keys are agent addresses and values are lists of
        addresses to which key-agent should create connections in order to
        recreate the graph structure in an agent society.

    :rtype: dict
    '''
    cm = {}
    for n in G.nodes(data=True):
        if weight_key is None:
            cm[n[1]['addr']] = [(G.node[nb]['addr'], 0.0) for nb in G[n[0]]]
        else:
            cm[n[1]['addr']] = [(G.node[nb]['addr'], G[n[0]][nb][weight_key])
                                for nb in G[n[0]]]
    return cm
