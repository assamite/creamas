'''
.. py:module:: feature
    :platform: Unix

Feature module holds base implementation for features
(:py:class:`~creamas.core.feature.Feature`) that creative agents have in their
rulesets.
'''
_all__ = ['Feature']


class Feature():
    '''Base feature class that is callable after initialization.

    Each feature value takes as an input an artifact, and returns feature's
    value for that artifact. If artifact type is not supported, feature's
    evaluation should return None.

    Returned feature values can be of any type, but rules
    (:py:class:`~creamas.core.rule.Rule`) should have appropriate mappers to
    map possible feature's values to the interval [-1, 1].

    Usage example:

    .. code-block:: python

        from myfeat import MyFeature
        from myartifact import MyArtifact
        myart = MyArtifact(*myparams)
        myart.rtype == mytype # True
        f = MyFeature()
        ret = f(myart)
        type(ret) == mytype # True
    '''
    def __init__(self, name, domains, rtype):
        '''
        :param str name:
            feature's name

        :param list domains:
            all artifact domains (:py:attr:`~creamas.core.artifact.type`) that
            can be evaluated with the feature.

        :param rtype: value type returned by this feature
        '''
        self.__domains = domains
        self.__rtype = rtype
        self.__name = name

    def __call__(self, artifact, mapper=None):
        if artifact.domain not in self.__domains:
            return None
        if mapper is None:
            return self.extract(artifact)
        return mapper(self.extract(artifact))

    def __str__(self):
        return self.__name

    @property
    def name(self):
        '''Name of the feature.'''
        return self.__name

    @property
    def domains(self):
        '''Set of acceptable artifact domains for this feature. Other types of
        artifacts will return *None* when tried to extract with this feature.
        '''
        return self.__domains

    @property
    def rtype(self):
        '''Value type returned by this feature.'''
        return self.__rtype

    def extract(self, artifact):
        '''Extract feature from artifact. **Dummy implementation, override in
        subclass.**

        :returns: feature value extracted from the artifact
        :rtype: rtype
        :raises NotImplementedError: if not overridden in subclass
        '''
        raise NotImplementedError('Override in subclass')
