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

    Each feature value takes as an input a artifact, and returns feature's
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
        myart.type == 'mytype' # True
        f = MyFeature()
        f.
        ret = f(myart)
    '''

    def __init__(self, name, types):
        '''Base feature.

        :param str name:
            feature's name

        :param list types:
            all artifact types (:py:attr:`~creamas.core.artifact.type`) that
            can be evaluated with the feature.
        '''
        self._types = types
        self._name = name

    def __call__(self, artifact):
        if artifact.type not in self._types:
            return None
        return self.evaluate(artifact)

    def __str__(self):
        return self._name

    @property
    def name(self):
        '''Name of the feature.'''
        return self._name

    @property
    def types(self):
        return self._types

    def evaluate(self, artifact):
        '''Evaluate artifact. **Dummy implementation, override in subclass.**

        :raises NotImplementedError: if not overridden in subclass
        '''
        raise NotImplementedError
