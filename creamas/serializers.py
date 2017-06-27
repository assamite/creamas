"""
.. py:module:: serializers
    :platform:

Predefined serializers for routers.
"""
import pickle

from creamas import Artifact


def artifact_serializer():
    """Basic serializer for :class¨:`~creamas.core.artifact.Artifact` objects
    using pickle.

    This serializer requires attr:`~aiomas.codecs.MsgPack` codec to work.
    """
    return Artifact, pickle.dumps, pickle.loads
