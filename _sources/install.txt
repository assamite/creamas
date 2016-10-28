Installation
============

Creamas is developed with `Python 3.5 <https://docs.python.org/3.5/>`_ and the 
cleanest way to start working with it is to create 
`virtualenv <https://virtualenv.readthedocs.org/en/latest/>`_ dedicated for it::

	$>git clone https://github.com/assamite/creamas.git creamas
	$>cd creamas
	$>pyvenv-3.5 venv # create venv for python 3.5
	$>source venv/bin/activate # start virtualenv
	$>pip install -r requirements.txt
	$>pip install -r c_reqs.txt # packages using C are in different file for readthedocs

That's it! Now you are ready to use Creamas.
