.. .. sectnum::
..   :depth: 4
..   :start: 1
..   :suffix: .

Installation
------------

You can download the Halostack source code from github,::

  $ git clone https://github.com/pnuu/halostack.git

and then run::

  $ python setup.py install

Testing
++++++++

To check if your python setup is compatible with halostack,
you can run the test suite using nosetests,::

  $ cd halostack
  $ nosetests -v tests/

or::

  $ cd halostack
  $ python setup.py test
