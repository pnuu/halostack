#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Entry point for the PyInstaller build.

Deliberately not named ``halostack.py``: PyInstaller registers the entry
script as a module under its own basename, so a script called
``halostack.py`` would shadow the ``halostack`` package and every
``halostack.something`` import would fail to resolve -- silently producing a
bundle with, for instance, no graphical interface in it.
"""

import sys

from halostack.launcher import main

if __name__ == '__main__':
    sys.exit(main())
