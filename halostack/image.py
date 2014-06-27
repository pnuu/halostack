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

'''Module for image I/O and conversions'''

class Image(object):
    '''Image class'''

    def __init__(self):
        self.red = None
        self.green = None
        self.blue = None

#    def __add__(self, img):
#        self.red += img.red
#        self.green += img.green
#        self.blue += img.blue#

#    def __stack__(self, img):

    def read(self):
        '''Read the image.
        '''
        pass

    def save(self):
        '''Save the image data.
        '''
        pass

    def _to_numpy(self):
        '''Convert the image data to numpy array.
        '''
        pass

    def _to_imagemagick(self):
        '''Convert the numpy array to Imagemagick format.
        '''
        pass

