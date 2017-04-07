'''
.. py:module:: ukko
    :platform: Unix

Utility functions to parse available Ukko nodes.
'''
import asyncio
import operator
import re
import urllib.request

import asyncssh

# URL for Ukko's report file
URL_UKKO_REPORT = 'http://www.cs.helsinki.fi/ukko/hpc-report.txt'

def _parse_ukko_report(report):
    '''Parse Ukko's report for available (non-reserved) nodes and their current
    loads. The nodes that have load marked as '-' in report are not returned.

    :returns: List of available ukko-nodes sorted in order of their current
    load (nodes with least load are first).
    '''
    lines = report.split("\\n")
    cc = r'ukko[0-9]{3}.hpc.cs.helsinki.fi'
    nodes = []
    for line in lines:
        if re.match(cc, line) and not re.search('Reserved', line):
            # This is a line for ukko-node which is not reserved
            sline = line.split(maxsplit=10)
            try:
                load = float(sline[5])
            except:
                # Could not parse load, node might not accept SSH-connections,
                #etc. Continue to next line.
                continue
            nodes.append((sline[0], load))
    return [n[0] for n in sorted(nodes, key=operator.itemgetter(1))]


def _get_ukko_report():
    '''Get Ukko's report from the fixed URL.
    '''
    with urllib.request.urlopen(URL_UKKO_REPORT) as response:
        ret = str(response.read())
    return ret


async def _test_node(node):
    '''Test node if it is currently loggable with ssh.
    '''
    try:
        conn = await asyncssh.connect(node, known_hosts=None)
        conn.close()
    except:
        return False
    return True


def get_nodes(n=8, exclude=[], loop=None):
    '''Get Ukko nodes with the least amount of load.

    May return less than *n* nodes if there are not as many nodes available,
    the nodes are reserved or the nodes are on the exclude list.

    :param int n: Number of Ukko nodes to return.
    :param list exclude: Nodes to exclude from the returned list.
    :param loop:
        asyncio's event loop to test if each returned node is currently
        loggable. The test is done by trying to connect to the node with
        (async)ssh.

    :rtype list:
    :returns: Locations of Ukko nodes with the least amount of load
    '''
    report = _get_ukko_report()
    nodes = _parse_ukko_report(report)
    ret = []
    while len(ret) < n and len(nodes) > 0:
        node = nodes[0]
        if node not in exclude:
            reachable = True
            if loop is not None:
                reachable = loop.run_until_complete(_test_node(node))
            if reachable:
                ret.append(node)
        nodes = nodes[1:]
    return ret
