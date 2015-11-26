'''
.. py:module:: rule
    :platform: Unix

Rule module holds base implementation of rule
(:py:class:`~creamas.core.rule.Rule`). Rules combine features and mappers to
functional body, where each feature also has weight attached to it.
'''
from creamas.core.feature import Feature

__all__ = ['Rule']


class Rule():
    '''Rule has a collection of features (**F**), a mapping of features to the
    values in interval [-1, 1] (**mappers**) and weight for each feature
    (**W**).

    Like features, rules can be directly evaluated for artifacts by calling
    them with artifact as the only argument.

    .. code-block:: python

        from myrules import MyRule
        feats = [myfeat1, myfeat2]
        weights = [0.5, 0.3]
        types = [mytype]
        mr = MyRule(feats, weights, types)
        mr.mappers([feat1_mapper, feat2_mapper])
        rule_result = mr(myartifact)
    '''
    def __init__(self, feats, weights):
        for f in feats:
            if not issubclass(f.__class__, Feature):
                raise TypeError("Feature ({}) in rule is not subclass of {}."
                                .format(f, Feature))
        self._domains = set.union(*[f.domains for f in feats])
        self._F = feats
        self._W = weights
        self._mappers = []

    @property
    def F(self):
        '''list - features in this rule.'''
        return self._F

    @property
    def W(self):
        '''list - weights for features in this rule.'''
        return self._W

    @property
    def mappers(self):
        '''list - mappers for features in this rule.'''
        return self._mappers

    @mappers.setter
    def mappers(self, value):
        if len(value) != len(self._F):
            raise ValueError('mappers should have same length as F ({}), now '
                             'it was {}.'.format(len(self._F), len(value)))
        self._mappers = value

    @property
    def domains(self):
        '''Rule's acceptable artifact domains is the union of all its
        features acceptable domains. Each artifact is evaluated only with
        features that do not return *None* when the feature is extracted from
        it.
        '''
        return self._domains

    def __call__(self, artifact):
        if artifact.domain not in self._domains:
            return None
        return self.evaluate(artifact)

    def __str__(self):
        s = ""
        for i in range(len(self._F)):
            s += "{}:{}({})|".format(self._W[i], self._F[i], self._mappers[i])
        return s

    def evaluate(self, artifact):
        '''Evaluate artifact with this rule. Called when the instantiated
        object is called.
        '''
        e = 0
        w = 0
        for i in range(len(self.F)):
            r = self.F[i](artifact)
            if r is not None:
                e += self.mappers[i](r) * self.W[i]
                w += self.W[i]
        if w == 0.0:
            return 0.0
        return e / w
