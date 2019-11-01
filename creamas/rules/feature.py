"""
.. py:module:: feature
    :platform: Unix

Feature module holds base implementation for features,
:py:class:`~creamas.rules.feature.Feature`, which creative agents have in their
rule sets considering artifacts.
"""
_all__ = ['Feature']


class Feature:
    """Base feature class that is callable after initialization.

    Each feature takes as an input an artifact, and returns feature's
    value for that artifact. If artifact type is not supported, feature's
    evaluation should return ``None``.

    Returned feature values can be of any type, but rules
    (:py:class:`~creamas.rules.rule.Rule`) should have appropriate mappers to
    map possible feature values to the interval [-1, 1].

    Usage example:

    .. code-block:: python

        from myfeat import MyFeature
        from myartifact import MyArtifact
        myart = MyArtifact(*myparams)
        myart.domain = mytype
        f = MyFeature()
        mytype in f.domains == True # True
        ret = f(myart)
        type(ret) == f.rtype # True
    """
    def __init__(self, name, domains, rtype):
        """
        :param str name:
            Feature's name

        :param list domains:
            A list of all artifact domains
            (:py:attr:`~creamas.core.artifact.type`) that can be evaluated with
            the feature.

        :param rtype:
            Value type returned by this feature. This can be combined with
            mappers accepting this type as the input parameter.
        """
        self.__domains = domains
        self.__rtype = rtype
        self.__name = name

    def __call__(self, artifact, mapper=None, **kwargs):
        if artifact.domain not in self.__domains:
            return None
        if mapper is None:
            return self.extract(artifact, **kwargs)
        return mapper(self.extract(artifact, **kwargs))

    def __str__(self):
        return self.__name

    @property
    def name(self):
        """Human readable name of the feature.
        """
        return self.__name

    @property
    def domains(self):
        """Set of acceptable artifact domains for this feature.

        When artifacts with other domains are used as parameters for
        :meth:`extract`, the function should return ``None``.
        """
        return self.__domains

    @property
    def rtype(self):
        """Value type returned by this feature.
        """
        return self.__rtype

    def extract(self, artifact, **kwargs):
        """Extract feature's value from an artifact.

        If artifact with a domain not in :attr:`domains` is used as a
        parameter, the function should return ``None``.

        .. note::
            Dummy implementation, override in a subclass.

        :returns: Value extracted from the artifact.
        :rtype: :attr:`rtype` or None
        :raises NotImplementedError: if not overridden in subclass
        """
        raise NotImplementedError('Override in subclass')
