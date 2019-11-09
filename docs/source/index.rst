
.. image:: _static/creamas-logo-triangle-rainbow.png
    :align: center
    :width: 80%
    :alt: Creamas logo

|

Introduction
============

Creamas is a Python (3.5+) library to develop, research and teach agent-based systems that exhibit emergent and/or
creative behavior in some ways. Its main implementations are quite general so that it could be used for diverse needs.
The main features include:

   * Built on top of `aiomas <https://aiomas.readthedocs.io/en/latest/>`_
   * Agents are designed to produce creative artifacts
   * Each agent lives in an environment
   * Environment acts also as a communication route between the agents
   * Support for multiple cores
   * Support for distributed systems running on multiple nodes
   * Easy made iterative simulations for agents
   * Social decision making using voting
   * NetworkX integration to generate agent connections from NetworkX structures and vice versa

See :doc:`overview` to get familiar with the library's main components.

Installation
------------

The easiest way to install the latest distribution of Creamas is using
`pip <https://pip.pypa.io/en/stable/>`_. Install the bare-boned version
using::

	pip install creamas

Or preferably install all the requirements using::

    pip install creamas[extras]

We encourage the use of `virtual environments <https://virtualenv.readthedocs.org/en/latest/>`_
to avoid conflicting package requirements in your projects.

Installing the Development Version
..................................

The project's main repository is in `github <https://github.com/assamite/creamas>`_. If you want to use the latest
development version, you can clone the repository from git::

    $>git clone https://github.com/assamite/creamas.git creamas
    $>cd creamas
    $>python3.7 -m venv env # create venv for python 3.7
    $>source env/bin/activate # start virtualenv
    $>pip install -r requirements.txt





.. toctree::
   :hidden:
   :maxdepth: 3

   overview
   create_agent
   create_sim
   using_mp_ds
   using_gp
   api