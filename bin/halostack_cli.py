#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, 2015 Panu Lahtinen

# Author(s):

# Panu Lahtinen <pnuu+git@iki.fi>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Halostack command line interface.

Installing Halostack also provides this as the ``halostack_cli`` command, on
every platform; this script is kept so that the documented way of running
Halostack straight from a source checkout keeps working.
"""

import os
import sys

try:
    from halostack.cli import main
except ImportError:                     # running from a source checkout
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from halostack.cli import main

if __name__ == "__main__":
    sys.exit(main())
