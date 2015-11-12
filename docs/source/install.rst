Installation
============

MASSACRE is developed with `Python 3.5 <https://docs.python.org/3.5/>`_ and the 
cleanest way to start working with it is to create 
`virtualenv <https://virtualenv.readthedocs.org/en/latest/>`_ dedicated for it::

	$>git clone https://github.com/assamite/mas.git mas # clone repo to mas/-subfolder
	$>cd mas
	$>pyvenv env # create virtualenv, make sure python 3.5 is used for env
	$>source env/bin/activate # start virtualenv
	$>pip install requirements.txt
	$>pip install c_reqs.txt # packages using C are in different file for readthedocs

That's it! Now you are ready to use MASSACRE.