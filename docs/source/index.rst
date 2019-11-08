
.. image:: _static/creamas-logo-triangle-rainbow.png
    :align: center
    :width: 80%
    :alt: Creamas logo

|

Introduction
============

Creamas is a library to develop, research and teach agent-based systems that exhibit emergent and/or creative behavior
in some ways. Its main implementations are quite general so that it could be used for diverse needs. See :doc:`overview`
for an introduction to the library's main components. Creamas is developed for Python 3.5+ and its main repository is in
`github <https://github.com/assamite/creamas>`_.

Features, etc.
--------------

   * Built on top of `aiomas <https://aiomas.readthedocs.io/en/latest/>`_
   * Agents are designed to produce creative artifacts
   * Each agent lives in an environment
   * Environment acts also as a communication route between the agents
   * Support for multiple cores
   * Support for distributed systems running on multiple nodes
   * Easy made iterative simulations for agents
   * Social decision making using voting
   * NetworkX integration to generate agent connections from NetworkX structures and vice versa



.. toctree::
   :hidden:
   :maxdepth: 3

   overview
   install
   create_agent
   create_sim
   using_mp_ds
   using_gp
   api