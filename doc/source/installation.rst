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
  ufraw

UFRaw is needed only if RAW image formats are used.  PNG, JPG and TIFF
files can be used without it.

You can download the Halostack source code from github,::

  $ git clone https://github.com/pnuu/halostack.git

and then run::

  $ python setup.py install

There is a command-line interface ``halostack_cli.py`` available in
the bin/ directory that can be used to interface the Halostack
libraries.

Testing
++++++++

To check if your python setup is compatible with halostack,
you can run the test suite using nosetests,::

  $ cd halostack
  $ nosetests -v tests/

or::

  $ cd halostack
  $ python setup.py test
