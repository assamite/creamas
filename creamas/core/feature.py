'''
.. py:module:: feature
    :platform: Unix

Feature module holds base implementation for features
(:py:class:`~creamas.core.feature.Feature`) that creative agents have in their
feature vector (:py:attr:`~creamas.core.agent.CreativeAgent.F`).
'''

_all__ = ['Feature']


class Feature():
    '''Feature class implements :py:meth:`__call__` that first c
    '''
    def __init__(self, name, artifact_types):
        '''Base feature.

        :param str name:
            feature's name

        :param list artifact_types:
            all artifact types (:py:attr:`~creamas.core.artifact.type`) that
            can be evaluated with the feature.
        '''
        self._artifact_types = artifact_types
        self._name = name

    def __call__(self, artifact):
        '''Call doc string.'''

        if artifact.type not in self._types:
            return 0.0

        return self.evaluate(artifact)

    @property
    def artifact_types(self):
        return self._artifact_types

    def evaluate(self, artifact):
        '''Evaluate artifact.

        **Override in subclass.**
        '''
        return 0.0
