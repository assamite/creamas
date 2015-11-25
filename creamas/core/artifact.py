'''
.. :py:module:: artifact
    :platform: Unix

Artifact module holds **Artifact**, a base class for artifacts created by
creative agents.
'''
__all__ = ['Artifact']


class Artifact():
    '''Base class for artifacts.'''

    domain = 'artifact'

    def __init__(self, creator, obj, e=0.0, fr=None):
        self._creator = creator.name
        self._obj = obj
        self._evals = {creator.name: e}
        self._framings = {creator.name: fr}

    @property
    def creator(self):
        ''':py:class:`~creamas.core.agent.CreativeAgent` who created the
        artifact.
        '''
        return self._creator

    @property
    def obj(self):
        '''Artifact itself.'''
        return self._obj

    @property
    def evals(self):
        '''*dict* - evaluations of the artifact.'''
        return self._evals

    @property
    def framings(self):
        '''*dict* - framings given for the evaluations.'''
        return self._framings

    def add_eval(self, agent, e, fr=None):
        '''Add or change agent's evaluation of the artifact with given framing
        information.

        :param agent: agent which did the evaluation
        :domain agent: :py:class:`~creamas.core.agent.CreativeAgent`
        :param float e: evaluation for the artifact
        :param object fr: framing information for the evaluation
        '''
        self._evals[agent.name] = e
        self._framings[agent.name] = fr

    def __str__(self):
        return "{}:{}".format(self.creator, self.obj)
