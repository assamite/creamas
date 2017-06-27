"""
.. :py:module:: artifact
    :platform: Unix

Artifact module holds **Artifact**, a base class for artifacts created by
creative agents.
"""
__all__ = ['Artifact']


class Artifact():
    """Base class for artifacts.

    A wrapper around the actual artifact object
    (:attr:`~creamas.core.artifact.Artifact.obj`) which holds information about
    the creator, framings and evaluations of the artifact.
    """

    def __init__(self, creator, obj, domain=int):
        self._creator = creator.name
        self._obj = obj
        self._domain = domain
        self._evals = {}
        self._framings = {}

    @property
    def creator(self):
        """The name of the agent which created the artifact.
        """
        return self._creator

    @property
    def obj(self):
        """Artifact object itself.
        """
        return self._obj

    def domain(self):
        """Domain of the artifact. Domain must match feature's possible domains
        at evaluation time, or None is returned.
        """
        return self._domain

    @property
    def evals(self):
        """Dictionary of evaluations for the artifact.

        Keys are the names of the evaluating agents and values are their
        actual evaluations.
        """
        return self._evals

    @property
    def framings(self):
        """Dictionary of framings for the artifacts.

        Keys are the names of the framing agents and values are their
        actual framings.
        """
        return self._framings

    def add_eval(self, agent, e, fr=None):
        """Add or change agent's evaluation of the artifact with given framing
        information.

        :param agent: Name of the agent which did the evaluation.
        :param float e: Evaluation for the artifact.
        :param object fr: Framing information for the evaluation.
        """
        self._evals[agent.name] = e
        self._framings[agent.name] = fr

    def __str__(self):
        return "{}:{}".format(self.creator, self.obj)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))
