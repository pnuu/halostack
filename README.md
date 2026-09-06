halostack
=========

[![Tests](https://github.com/pnuu/halostack/actions/workflows/tests.yml/badge.svg)](https://github.com/pnuu/halostack/actions/workflows/tests.yml)
[![Windows executable](https://github.com/pnuu/halostack/actions/workflows/windows-executable.yml/badge.svg)](https://github.com/pnuu/halostack/actions/workflows/windows-executable.yml)

Image stacking specifically for ice-crystal halo photographs.

Halostack aligns a series of exposures on a feature you pick — usually the Sun
behind a blocker — combines them into one or more stacks, and applies
enhancements that make faint halos visible.

Installation
------------

```
pip install halostack          # add [raw] for camera raw files
```

Runs on Windows, macOS and Linux with Python 3.9 or newer. Every dependency
ships as a binary wheel, so there is nothing to compile and no system package
to install first.

On Windows you can skip Python entirely: a standalone `halostack_cli.exe` is
attached to each [release](https://github.com/pnuu/halostack/releases).

Usage
-----

```
halostack_cli -a average_stack.png *.jpg
```

You are shown the first frame and asked to click two corners around the
alignment reference, then two corners around the area to search for it in
each of the remaining frames.

The documentation is available at http://halostack.readthedocs.org/
