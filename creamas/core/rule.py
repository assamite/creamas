'''
.. py:module:: creamas.core.rule
    :platform: Unix

Rule module holds :py:class:`~creamas.core.rule.Rule`.
'''
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
    def __init__(self, feats, weights, types):
        self._types = types
        self._F = feats
        self._W = weights
        self._mappers = []

    @property
    def F(self):
        '''Features in this rule.'''
        return self._F

    @property
    def W(self):
        '''Weights for features in this rule.'''
        return self._W

    @property
    def mappers(self):
        '''Mappers to map values of each feature into interval [-1, 1].'''
        return self._mappers

    @mappers.setter
    def mappers(self, value):
        self._mappers = value

    def __call__(self, artifact):
        if artifact.type not in self._types:
            return None
        return self.evaluate(artifact)

    def evaluate(self, artifact):
        '''Evaluate artifact with this rule. Implicitly called when called the
        instantiated object.
        '''
        e = 0
        w = 0
        for i in len(self.F):
            r = self.F[i](artifact)
            if r is not None:
                e += self.mappers[i](r) * self.W[i]
                w += self.W[i]
        if w == 0.0:
            return 0.0
        return e / w
