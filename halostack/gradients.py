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

'''Module for removing gradients from images'''

class Gradient(object):
    '''Gradient removel class'''

    def __init__(self):
        self.img = None
        self.method = None
        self._xloc = None
        self._yloc = None
        self._zval = None
        self.gradient = None

    def calculate_gradient(self, method):
        '''Calculate gradient from the image using the given method.
        param method: name of the method for calculating the gradient
        return gradient: array holding the calculated gradient
        '''
        # if-elif-else structure to handle the requested methods
        pass

    def remove_gradient(self):
        '''Subtract the precalculated(?) gradient from the image.
        '''
        pass

    def _blur(self):
        '''Blur the image to get the approximation of the background gradient.
        '''
        pass

    def _guess_points(self):
        '''Automatically extract background points for gradient estimation.
        '''
        # The points should not deviate too much from the surrounding
        # points, and the points "too far" should be left out.
        # Leave the exclusion to _fit_surface()?
        # The values should be quite close to median value?
        # Select the points uniformly?
        pass

    def _get_user_points(self):
        '''Get background points from the user input (clicking with
        mouse in the image? mask?)
        '''

    def _fit_surface(self):
        '''Fit a surface to the given (x,y,z) data.
        '''
        # Used surface is of form: z(x,y) = ax2 + by2 + cx + dy + f
        pass
