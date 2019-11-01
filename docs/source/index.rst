.. Creamas documentation master file, created by
   sphinx-quickstart on Wed Nov 11 17:34:41 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Creamas - Creative Multi-Agent Systems
======================================

.. image:: _static/python-powered-w-70x28.png

Creamas is Python (3.5+) library for (creative) multi-agent systems. It was
created as a tool to research and implement multi-agent systems that exhibit
emergent and/or creative behavior in some ways. However, its main
implementations are general enough to be used for multi-agent systems with
other purposes.

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

See :doc:`overview` for a more detailed introduction to the library's main components.
Project's main repository is in `github <https://github.com/assamite/creamas>`_.

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