Installation
============

Creamas is developed with `Python 3.5 <https://docs.python.org/3.5/>`_,
the easiest way to install the latest distribution of Creamas is using
`pip <https://pip.pypa.io/en/stable/>`_::

	pip install creamas

We encourage the use of `virtual environments <https://virtualenv.readthedocs.org/en/latest/>`_ to avoid conflicting package requirements in your projects.

Installing the development version
----------------------------------

If you want to use the latest development version, you can clone the repository
from git::

	$>git clone https://github.com/assamite/creamas.git creamas
	$>cd creamas
	$>pyvenv-3.5 venv # create venv for python 3.5
	$>source venv/bin/activate # start virtualenv
	$>pip install -r requirements.txt
	$>pip install -r c_reqs.txt # packages using C are in different file for readthedocs
