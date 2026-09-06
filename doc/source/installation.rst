.. .. sectnum::
..   :depth: 4
..   :start: 1
..   :suffix: .

Installation
------------

Halostack runs on Windows, macOS and Linux, and needs nothing but Python
3.9 or newer.  Every dependency is available as a binary wheel, so there is
no compiler and no system package to install first::

  $ pip install halostack

To work from a source checkout instead::

  $ git clone https://github.com/pnuu/halostack.git
  $ cd halostack
  $ pip install -e .

Either way you get the ``halostack_cli`` command, which works the same on all
three operating systems.  A source checkout can also be run without
installing, using the script in ``bin/``.

Camera raw files
++++++++++++++++

Reading raw files (CR2, NEF, ARW, DNG and so on) needs one extra package::

  $ pip install halostack[raw]

This replaces the old requirement for a separate UFRaw installation.  JPEG,
PNG and TIFF files work without it.

What gets installed
+++++++++++++++++++

============  =====================================================
NumPy         array handling
SciPy         filtering and the correlation used for alignment
imageio       reading and writing common image formats
Pillow        image format support behind imageio
tifffile      TIFF, at 8, 16 or 32 bits
imagecodecs   PNG, at 8 or 16 bits
Matplotlib    the interactive alignment preview
rawpy         camera raw files (optional, see above)
============  =====================================================

Halostack no longer uses ImageMagick or PythonMagick.  PythonMagick has to be
compiled against ImageMagick, which is what made Halostack awkward to install,
and it is no longer maintained; the image processing is now done with NumPy
and SciPy directly.

Testing
++++++++

To check that everything works, run the test suite from the source
directory::

  $ pip install -e ".[tests]"
  $ pytest

Any of the individual test modules can be run on its own, for example::

  $ pytest tests/test_stack.py
  $ pytest tests/test_stack.py::test_mean_is_a_mean_not_a_sum
