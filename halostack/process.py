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

'''Module for image processing'''

from halostack.gradients import Gradient

class Process(object):
    '''Class for processing images.
    '''

    def __init__(self):
        self.img = None

    def usm(self):
        '''Apply unsharp mask sharpening to the image.
        '''
        pass

    def emboss(self):
        '''Apply emboss filtering to the image.
        '''
        pass

    def gamma(self):
        '''Apply gamma correction to the image.
        '''
        pass

    def blue_red(self):
        '''Subtract red channel from the blue channel after scaling
        the blue channel using the multiplier supplied or calculated
        from the given pixel locations.
        '''
        pass

    def rgb_subtract(self):
        '''Subtract the mean(r,g,b) from all the channels.
        '''
        pass

    def gradient(self):
        '''Remove the gradient from the image.
        '''
        pass
