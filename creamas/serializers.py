'''
.. py:module:: serializers
    :platform:

Predefined serializers for routers.
'''
import pickle

import aiomas

from creamas import Artifact


def artifact_serializer():
    '''Serializer from :class¨:`creamas.core.artifact.Artifact` objects using
    pickle. Needs MsgPack-codec to work.
    '''
    return Artifact, pickle.dumps, pickle.loads


def proxy_serializer():
    '''Serializer from :class:`aiomas.rpc.Proxy` objects using pickle. Needs
    MsgPack-codec to work.
    '''
    return aiomas.rpc.Proxy, pickle.dumps, pickle.loads