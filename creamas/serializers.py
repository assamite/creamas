"""
.. py:module:: serializers
    :platform: Unix

Predefined serializers for routers.
"""
import pickle

from numpy import array, ndarray

from creamas.core.artifact import Artifact


def get_serializers():
    """Get all basic serializers defined in this module as a list.
    """
    return [artifact_serializer, array_serializer, ndarray_serializer]


def artifact_serializer():
    """Basic serializer for :class¨:`~creamas.core.artifact.Artifact` objects
    using pickle.

    This serializer requires attr:`~aiomas.codecs.MsgPack` codec to work.
    """
    return Artifact, pickle.dumps, pickle.loads


def array_serializer():
    """Basic serializer for :class¨:`~numpy.array` objects using pickle.

    This serializer requires attr:`~aiomas.codecs.MsgPack` codec to work.
    """
    return array, pickle.dumps, pickle.loads


def ndarray_serializer():
    """Basic serializer for :class¨:`~numpy.ndarray` objects using pickle.

    This serializer requires attr:`~aiomas.codecs.MsgPack` codec to work.
    """
    return ndarray, pickle.dumps, pickle.loads
