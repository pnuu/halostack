#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Panu Lahtinen

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

"""The tests package.
"""

import unittest
import doctest
from . import test_helpers
from . import test_image
from . import test_align
from . import test_stack
from . import test_halostack

def suite():
    """The global test suite.
    """
    mysuite = unittest.TestSuite()
    # Use the unittests also
    mysuite.addTests(test_helpers.suite())
    mysuite.addTests(test_image.suite())
    mysuite.addTests(test_align.suite())
    mysuite.addTests(test_stack.suite())
    mysuite.addTests(test_halostack.suite())
    
    return mysuite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
