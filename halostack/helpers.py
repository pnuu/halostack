#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014

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

'''Misc helper functions'''

import logging
from glob import glob

LOGGER = logging.getLogger(__name__)

def get_filenames(fnames):
    '''Get filenames to a list. Expand wildcards etc.
    '''

    fnames_out = []

    # Ensure that all files are used also on Windows, as the command
    # prompt does not automatically parse wildcards to a list of images
    for fname in fnames:
        if '*' in fname:
            all_fnames = glob(fname)
            for fname2 in all_fnames:
                fnames_out.append(fname2)
                LOGGER.info("Added %s to the image list", fname2)
        else:
            fnames_out.append(fname)
            LOGGER.info("Added %s to the image list", fname)

    return fnames_out
