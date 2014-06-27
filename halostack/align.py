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

'''Module for coaligning images'''

class Align(object):
    '''Class to coalign images
    '''
    def __init__(self, img):
        self.img = img
        self.ref = None
        self.srch_area = None

    def set_reference(self):
        '''Let the user select the reference area.
        '''
        pass

    def set_reference_area(self):
        '''Let the user select the reference search area
        '''
        pass

    def align(self, img):
        '''Align the given image with the reference image.
        '''
        pass

    def _find_reference(self, img):
        '''Find the reference area from the given image.
        '''
        pass

    def _fft_match(self, img):
        '''Use FFT to find the best alignment.
        '''
        pass

    def _correlation_match(self, img):
        '''Use correlation to find the best alignment. Slow.
        '''
        pass

    def _calc_shift(self, img):
        '''Calculate how much the images need to be shifted.
        '''
        pass

    def _shift(self, img, x_sift, y_sift):
        '''Shift the image by x_sift and y_sift pixels.
        '''
        pass
