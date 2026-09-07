.. .. sectnum::
..   :depth: 4
..   :start: 1
..   :suffix: .

Installation
------------

Windows: no installation at all
+++++++++++++++++++++++++++++++

A standalone ``halostack.exe`` is built for every release and can be
downloaded from the `releases page
<https://github.com/pnuu/halostack/releases>`_.  It contains Python, the
window and the command line, so there is nothing to install: put it wherever
you like and double-click it, or run it from a command prompt::

  C:\photos> halostack.exe                            # the window
  C:\photos> halostack.exe -a average_stack.png *.jpg  # straight to work

The executable is about 110 MB and takes a few seconds to start, because it
unpacks itself into a temporary directory on each run.  It is built only for
tagged releases, so there is no per-commit build to download.

Installing with pip
+++++++++++++++++++

Halostack runs on Windows, macOS and Linux, and needs nothing but Python
3.12 or newer.  Every dependency is available as a binary wheel, so there is
no compiler to install first, and on Windows and macOS no system package
either::

  $ pip install halostack

That gives both the window and the command line.  To leave out the window,
and Qt with it::

  $ pip install --no-deps halostack && pip install numpy scipy imageio \
      pillow tifffile imagecodecs matplotlib

To work from a source checkout instead::

  $ git clone https://github.com/pnuu/halostack.git
  $ cd halostack
  $ pip install -e .

Either way you get the ``halostack`` command, which works the same on all
three operating systems, along with ``halostack_cli`` and ``halostack_gui``
for the two interfaces on their own.  A source checkout can also be run
without installing::

  $ python -m halostack.launcher      # the window, or the command line
  $ python -m halostack.cli --help

Linux: one system library
+++++++++++++++++++++++++

The window needs one thing pip cannot install.  Qt 6.5 and later load their
X11 support from a plugin that requires ``libxcb-cursor``, which comes from
the distribution rather than from PyPI.  Without it Qt stops before the
window appears::

  qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load
  the Qt xcb platform plugin.
  Could not load the Qt platform plugin "xcb" in "" even though it was found.

Install it with whichever of these fits your system::

  $ sudo apt install libxcb-cursor0          # Debian, Ubuntu, Mint
  $ sudo dnf install xcb-util-cursor         # Fedora, RHEL
  $ sudo zypper install libxcb-cursor0       # openSUSE
  $ sudo pacman -S xcb-util-cursor           # Arch
  $ conda install -c conda-forge xcb-util-cursor

Halostack checks for the library before it opens the window and prints this
list if it is missing, rather than leaving you with Qt's message.  The
command line does not need it, and neither does the Windows executable.

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
Matplotlib    the command line's alignment preview
PySide6       the window
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
