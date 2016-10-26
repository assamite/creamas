'''
.. py:module:: rule
    :platform: Unix

Rule module holds base implementation of rule
(:py:class:`~creamas.core.rule.Rule`). Rules combine features and mappers to
functional body, where each feature also has weight attached to it.

TODO: write rule to accept other rules in F also.
'''
import copy
from functools import partial

__all__ = ['Rule']


class RuleLeaf():
    '''Leaf implementation for rules.

    Combines feature and mapper into one functional unit. Adding two RuleLeafs
    together will result in a Rule instance. Two RuleLeafs are equal if their
    features are equal, mappers are *not* considered.
    '''
    def __init__(self, feat, mapper):
        '''
        :param feat: Feature for this leaf rule.
        :type feat: py:class:`~creamas.core.feature.Feature`
        :param mapper: Mapper for this leaf rule
        :type mapper: py:class:`~creamas.core.mapper.Mapper`
        '''
        self.__domains = feat.domains
        self.__feat = feat
        self.__mapper = mapper

    def __call__(self, artifact):
        if artifact.domain not in self.__domains:
            return None
        return self.__mapper(self.__feat.extract(artifact))

    def __str__(self):
        return "RuleLeaf({}:{}))".format(self.__feat, self.__mapper)

    def __add__(self, leaf):
        rule = Rule([self, leaf], [1.0, 1.0], evaluation='ave')
        return rule

    def __eq__(self, other):
        if isinstance(other, RuleLeaf):
            return self.__feat == other.feat
        return NotImplemented

    def __ne__(self, other):
        ret = self.__eq__(other)
        if ret is NotImplemented:
            return ret
        return not ret

    @property
    def domains(self):
        return self.__domains

    @property
    def feat(self):
        return self.__feat

    @property
    def mapper(self):
        return self.__mapper


class Rule():
    '''Rule is a treelike data structure consisting of other Rules and RuleLeaf
    instances. Rules are used by agents to evaluate artifacts.

    Like features, rules offer a simple interface where
    artifact can be evaluated by calling a rule instance with artifact as the
    only argument. Rules should return a float in [-1, 1] when evaluated.

    .. code-block:: python

        from creamas.core.rule import Rule
        rule = Rule([myleaf, myleaf2, myrule], [1.0, 1.0, 1.0])
        res = rule(myartifact)
    '''
    def __init__(self, rules, weights, evaluation='ave'):
        '''
        :param list rules:
            Subrules for this rule. Subrule can be either an iterable of length
            2, the (Feature, Mapper)-pair, or another Rule instance.

        :param list weights:
            Weights for the subrules.

        :param evaluation:
            How rule's internal evaluation is done. Either one of the
            predefined functions, or user defined callable which takes two
            arguments: rule and artifact (in that order). Predefined functions
            and their keywords are:

            * 'ave': :py:func:`~creamas.core.rule.weighted_average`
            * 'min': :py:func:`~creamas.core.rule.minimum`
            * 'max': :py:func:`~creamas.core.rule.maximum`

        '''
        assert len(rules) == len(weights)
        self.__domains = set()
        self.__R = []
        self.__W = []

        for i in range(len(rules)):
            self.add_subrule(rules[i], weights[i])

        if evaluation == 'ave':
            self.evaluate = partial(weighted_average, self)
        elif evaluation == 'min':
            self.evaluate = partial(minimum, self)
        elif evaluation == 'max':
            self.evaluate = partial(maximum, self)
        elif hasattr(evaluation, '__call__'):
            self.evaluate = partial(evaluation, self)
        else:
            raise ValueError("'evaluation' keyword must be one of the "
                             "recognized types or callable, got {}."
                             .format(evaluation))

    @property
    def R(self):
        '''list - subrules in this rule.'''
        return self.__R

    @property
    def W(self):
        '''list - weights for subrules in this rule.'''
        return self.__W

    @property
    def domains(self):
        '''Rule's acceptable artifact domains is the union of all its
        subrules acceptable domains. Each artifact is evaluated only with
        subrules that do not return *None* when the feature is evaluated with
        it.
        '''
        return self.__domains

    def add_subrule(self, subrule, weight):
        '''Add subrule to the rule.

        :param subrule:
            Subrule to add to this rule. Subrule can be either an iterable of
            length 2, the (Feature, Mapper)-pair, or another Rule instance.

        :param float weight: weight of the subrule
        :returns: false if subrule already in rule, true otherwise
        :rtype: bool
        '''
        if not (issubclass(subrule.__class__, Rule) or
                issubclass(subrule.__class__, RuleLeaf)):
            raise TypeError("Rule's class must be (subclass of) {} or {}, got "
                            "{}.".format(Rule, RuleLeaf, subrule.__class__))
        self.__domains = set.union(self.__domains, subrule.domains)
        self.R.append(subrule)
        self.W.append(weight)
        return True

    def __call__(self, artifact):
        if artifact.domain not in self.__domains:
            return None
        return self.evaluate(artifact)

    def __str__(self):
        s = "Rule("
        if len(self.__R) == 0:
            return s + "empty)"
        for i in range(len(self.__R)):
            s += "{}:{}-".format(self.__W[i], self.__R[i])
        return s + ")"

    def __iadd__(self, rule):
        ind = []
        for i in range(len(rule.R)):
            if rule.R[i] not in self.__R:
                ind.append(i)
        for i in ind:
            self.add_subrule(rule.R[i], rule.W[i])
        return self

    def __add__(self, rule):
        new_rule = copy.deepcopy(self)
        ind = []
        for i in range(len(rule.R)):
            if rule.R[i] not in self.R:
                ind.append(i)
        for i in ind:
            new_rule.add_subrule(rule.R[i], rule.W[i])
        return new_rule

    def __bool__(self):
        if len(self.R) == 0:
            return True
        return False


def weighted_average(rule, artifact):
    '''Evaluate artifact's value to be weighted average of values returned by
    rule's subrules.
    '''
    e = 0
    w = 0
    for i in range(len(rule.R)):
        r = rule.R[i](artifact)
        if r is not None:
            e += r * rule.W[i]
            w += abs(rule.W[i])
    if w == 0.0:
        return 0.0
    return e / w


def minimum(rule, artifact):
    '''Evaluate artifact's value to be minimum of values returned by rule's
    subrules.

    This evaluation function ignores subrule weights.
    '''
    m = 1.0
    for i in range(len(rule.R)):
        e = rule.R[i](artifact)
        if e is not None:
            if e < m:
                m = e
    return m


def maximum(rule, artifact):
    '''Evaluate artifact's value to be maximum of values returned by rule's
    subrules.

    This evaluation function ignores subrule weights.
    '''
    m = -1.0
    for i in range(len(rule.R)):
        e = rule.R[i](artifact)
        if e is not None:
            if e > m:
                m = e
    return m
