.. .. sectnum::
..   :depth: 4
..   :start: 1
..   :suffix: .

Installation
------------

Halostack requires the following additional software, and their own
requirements, to be installed::

  python
  numpy
  matplotlib
  imagemagick
  pythonmagick
  setuptools
  ufraw

UFRaw is needed only if RAW image formats are used.  PNG, JPG and TIFF
files can be used without it.  In Ubuntu, all these can be installed by::

  sudo apt-get install python python-numpy python-matplotlib imagemagick \
  python-pythonmagick python-setuptools ufraw

You can download the Halostack source code from github,::

  $ git clone https://github.com/pnuu/halostack.git

and then run::

  $ cd halostack
  $ python setup.py install --user

There is a command-line interface ``halostack_cli.py`` available in
the bin/ directory that can be used to interface the Halostack
libraries.

Testing
++++++++

To check if your python setup is compatible with halostack, you can
run the test suite in the halostack source directory using
nosetests,::

  $ nosetests -v tests/

or::

  $ python setup.py test
