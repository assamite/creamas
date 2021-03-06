Implementing Agent Classes
==========================

All agents used in Creamas must inherit from 
:py:class:`~creamas.core.agent.CreativeAgent`. They should also accept 
the agent's :class:`~creamas.core.environment.Environment` as the first
parameter in their :meth:`__init__`. The environment should then be passed on
to :py:meth:`super().__init__`.

Each agent class should call :py:meth:`super().__init__` as one of the first
things in :py:meth:`__init__`, for example:

.. code-block:: python

    from creamas import CreativeAgent, Environment

    class MyAgent(CreativeAgent):

        def __init__(self, environment, *args, **kwargs):
            self.my_arg = kwargs.pop('my_arg', None)
            super().__init__(environment, *args, **kwargs)
            # Your own initialization code

    env = Environment.create(('localhost', 5555))
    agent = MyAgent(env, my_arg=5)
    # do stuff
    env.close()


