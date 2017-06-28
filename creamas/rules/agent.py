"""
.. py:module:: rules/agent.py
    :platform: Unix

The module holdin :class:`RuleAgent`, an agent which evaluates artifacts using
its own rules.
"""
import aiomas

from creamas.core.agent import CreativeAgent
from creamas.rules.rule import Rule, RuleLeaf


__all__ = ['RuleAgent']


class RuleAgent(CreativeAgent):
    """Base class for agents using rules to evaluate artifacts.


    :ivar list ~creamas.core.agent.CreativeAgent.R:
        rules agent uses to evaluate artifacts

    :ivar list ~creamas.core.agent.CreativeAgent.W:
        Weight for each rule in **R**, in [-1,1].
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._R = []
        self._W = []

    @property
    def R(self):
        """Rules agent uses to evaluate artifacts. Each rule in **R** is
        expected to be a callable with a single parameter, the artifact to be
        evaluated. Callable should return a float in [-1,1]; where 1 means that
        rule is very prominent in the artifact; 0 means that there is none of
        that rule in the artifact; -1 means that the artifact shows
        traits opposite to the rule.
        """
        return self._R

    @property
    def W(self):
        """Weights for the rules.

        Each weight should be in [-1,1]."""
        return self._W

    def set_weight(self, rule, weight):
        """Set weight for rule in :attr:`R`.

        Adds the rule if it is not in :attr:`R`.
        """
        if not issubclass(rule.__class__, (Rule, RuleLeaf)):
            raise TypeError("Rule to set weight ({}) is not subclass "
                            "of {} or {}.".format(rule, Rule, RuleLeaf))
        assert (weight >= -1.0 and weight <= 1.0)
        try:
            ind = self._R.index(rule)
            self._W[ind] = weight
        except:
            self.add_rule(rule, weight)

    def get_weight(self, rule):
        """Get weight for rule.

        If rule is not in :attr:`R`, returns ``None``.
        """
        if not issubclass(rule.__class__, (Rule, RuleLeaf)):
            raise TypeError("Rule to get weight ({}) is not subclass "
                            "of {} or {}.".format(rule, Rule, RuleLeaf))
        try:
            ind = self._R.index(rule)
            return self._W[ind]
        except:
            return None

    def add_rule(self, rule, weight):
        """Add rule to :attr:`R` with initial weight.

        :param rule: rule to be added
        :type rule: `~creamas.core.rule.Rule`
        :param float weight: initial weight for the rule
        :raises TypeError: if rule is not subclass of :py:class:`Rule`
        :returns: ``True`` if rule was successfully added, otherwise ``False``.
        :rtype bool:
        """
        if not issubclass(rule.__class__, (Rule, RuleLeaf)):
            raise TypeError(
                "Rule to add ({}) must be derived from {} or {}."
                .format(rule.__class__, Rule, RuleLeaf))
        if rule not in self._R:
            self._R.append(rule)
            self._W.append(weight)
            return True
        return False

    def remove_rule(self, rule):
        """Remove rule from :attr:`R` and its corresponding weight from
        :attr:`W`.

        :param rule: rule to remove
        :type rule: `~creamas.core.rule.Rule`
        :raises TypeError: if rule is not subclass of :py:class:`Rule`
        :returns: true if rule was successfully removed, otherwise false
        :rtype bool:
        """
        if not issubclass(rule.__class__, (Rule, RuleLeaf)):
            raise TypeError(
                "Rule to remove ({}) is not subclass of {} or {}."
                .format(rule.__class__, Rule, RuleLeaf))
        try:
            ind = self._R.index(rule)
            del self._R[ind]
            del self._W[ind]
            return True
        except:
            return False

    @aiomas.expose
    def evaluate(self, artifact):
        r"""Evaluate artifact with agent's current rules and weights.

        :param artifact:
            :class:`~creamas.core.artifact.Artifact` to be evaluated

        :type artifact:
            :py:class:`~creamas.core.artifact.Artifact`

        :returns:
            Agent's evaluation of the artifact, in [-1,1], and framing. In this
            basic implementation framing is always ``None``.

        :rtype:
            tuple

        Actual evaluation formula in this basic implementation is:

        .. math::

            e(A) = \frac{\sum_{i=1}^{n} r_{i}(A)w_i}
            {\sum_{i=1}^{n} \lvert w_i \rvert},

        where :math:`r_{i}(A)` is the :math:`i` th rule's evaluation on
        artifact :math:`A`, and :math:`w_i` is the weight for rule
        :math:`r_i`.
        """
        s = 0
        w = 0.0
        if len(self.R) == 0:
            return 0.0, None

        for i in range(len(self.R)):
            s += self.R[i](artifact) * self.W[i]
            w += abs(self.W[i])

        if w == 0.0:
            return 0.0, None
        return s / w, None
