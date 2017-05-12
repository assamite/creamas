Implementing Agent Classes
==========================

All agents used in Creamas must inherit from 
:py:class:`~creamas.core.agent.CreativeAgent`. They should also accept one 
parameter that is passed down to :py:meth:`super().__init__`:

* **environment**: :py:class:`~creamas.core.environment.Environment` where the 
  agent lives


Each agent class should call :py:meth:`super().__init__` first thing in 
:py:meth:`__init__`, for example:

.. code-block:: python

	from creamas.core.agent import CreativeAgent
	
	class MyAgent(CreativeAgent):
	
		def __init__(self, environment, *args, **kwargs):
			super().__init__(environment)
			# Your own initialization code