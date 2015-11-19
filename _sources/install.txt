Installation
============

Creamas is developed with `Python 3.5 <https://docs.python.org/3.5/>`_ and the 
cleanest way to start working with it is to create 
`virtualenv <https://virtualenv.readthedocs.org/en/latest/>`_ dedicated for it::

	$>git clone https://github.com/assamite/creamas.git creamas
	$>cd creamas
	$>virtualenv -p `which python3.5` env # create venv for python 3.5
	$>source env/bin/activate # start virtualenv
	$>pip install requirements.txt
	$>pip install c_reqs.txt # packages using C are in different file for readthedocs

That's it! Now you are ready to use Creamas.