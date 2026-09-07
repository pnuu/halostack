halostack
=========

[![Tests](https://github.com/pnuu/halostack/actions/workflows/tests.yml/badge.svg)](https://github.com/pnuu/halostack/actions/workflows/tests.yml)

Image stacking specifically for ice-crystal halo photographs.

Halostack aligns a series of exposures on a feature you pick — usually the Sun
behind a blocker — combines them into one or more stacks, and applies
enhancements that make faint halos visible.

![The Halostack window: the stacked image on the left, the settings on the right](doc/source/images/gui.png)

*Six exposures aligned on the Sun and combined, with the background gradient
removed and an unsharp mask applied. The green box is the alignment
reference, the orange one the area it is searched for in each frame.*

Installation
------------

```
pip install halostack          # add [raw] for camera raw files
```

Runs on Windows, macOS and Linux with Python 3.12 or newer. Every dependency
ships as a binary wheel, so there is nothing to compile. On Linux the window
additionally needs `libxcb-cursor` from your distribution (`sudo apt install
libxcb-cursor0` on Debian and Ubuntu); Halostack says so if it is missing, and
the command line does not need it.

On Windows you can skip Python entirely: a standalone `halostack.exe`, with
both interfaces in it, is attached to each
[release](https://github.com/pnuu/halostack/releases).

Usage
-----

```
halostack                              # opens the window
halostack -a average_stack.png *.jpg   # command line, straight to work
```

An option means "do this now"; nothing but filenames opens the window with
them loaded. In either interface you mark the alignment reference on the
first frame, and the area to search for it in the remaining frames.

The documentation is available at http://halostack.readthedocs.org/
