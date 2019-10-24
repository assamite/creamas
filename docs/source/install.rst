Installation
============

Creamas is developed with `Python 3.7 <https://docs.python.org/3.7/>`_,
the easiest way to install the latest distribution of Creamas is using
`pip <https://pip.pypa.io/en/stable/>`_::

	pip install creamas

We encourage the use of `virtual environments <https://virtualenv.readthedocs.org/en/latest/>`_
to avoid conflicting package requirements in your projects.

Installing the Development Version
----------------------------------

If you want to use the latest development version, you can clone the repository
from git::

	$>git clone https://github.com/assamite/creamas.git creamas
	$>cd creamas
	$>python3.7 -m venv env # create venv for python 3.7
	$>source env/bin/activate # start virtualenv
	$>pip install -r requirements.txt
	$>pip install -r c_reqs.txt # packages using C are in different file for readthedocs
