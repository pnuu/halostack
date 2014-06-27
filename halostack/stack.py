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

'''Module for stacking images'''

import numpy as np

class Stack(object):
    '''Class for image stacks'''

    def __init__(self):
        self.stack = None

    def add_image(self, img, mode):
        '''Add a frame to the stack.
        '''
        # if-elif-else structure to handle different stack types
        # mean: sum, min and max: update, sigma-average and mean: collect
        if self.stack is None:
            self.stack = img
        else:
            self._update_stack(img, mode)

    def calculate(self):
        '''Calculate the resultant stack
        '''
        # if-elif-else structure to calculate the result image
        pass

    def _update_stack(self, img, mode):
        '''Update the stack
        '''
        if mode == 'mean':
            self._update_mean(img)
        elif mode == 'min':
            self._update_min(img)
        elif mode == 'max':
            self._update_max(img)
        elif mode == 'sigma':
            self._update_sigma_average(img)
        else:
            pass

    def _update_mean(self, img):
        '''Update average stack
        '''
        self.stack += img

    def _update_min(self, img):
        '''Minumum stack
        '''
        idxs = img < self.stack
        self.stack[idxs] = img[idxs]

    def _update_max(self, img):
        '''Maximum stack
        '''
        idxs = img > self.stack
        self.stack[idxs] = img[idxs]

    def _update_median(self, img):
        '''Median stack
        '''
        self.stack = np.dstack((self.stack, img))

    def _update_sigma_average(self, img):
        '''Sigma-reject average
        '''
        self.stack = np.dstack((self.stack, img))

