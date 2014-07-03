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

import numpy as np

class Align(object):
    '''Class to coalign images
    '''
    def __init__(self, img, ref_loc=None, srch_area=None, mode='simple'):

        modes = {'simple': self._simple_match}

        self.img = img
        self.ref_loc = ref_loc
        self.srch_area = srch_area
        self.ref = None
        try:
            self.align_func = modes[mode]
        except AttributeError:
            self.align_func = self._simple_match

        if ref_loc is not None:
            self._set_ref()
        if srch_area is None:
            y_size, x_size = self.img.shape
            self.srch_area = [0, 0, y_size, x_size]

    def set_reference(self, area):
        '''Set the reference area *area*.
        param area: 3-tuple of the form (x, y, radius)
        '''
        self.ref_loc = area

    def set_search_area(self, area):
        '''Set the reference search area *area*.
        param area: 4-tuple of the form (x1, x2, y1, y2)
        '''
        self.srch_area = area

    def align(self, img):
        '''Align the given image with the reference image.
        '''

        # Get the correlation and the location of the best match
        corr, y_loc, x_loc = self.align_func(img)
        # Shift the image

        return img

    def _set_ref(self):
        '''Set reference values.
        '''
        self.ref = self.img[self.ref_loc[0]-self.ref_loc[2]:\
                                self.ref_loc[0]+self.ref_loc[2]+1,
                            self.ref_loc[1]-self.ref_loc[2]:\
                                self.ref_loc[1]+self.ref_loc[2]+1]

    def _find_reference(self, img):
        '''Find the reference area from the given image.
        '''
        pass

    def _fft_match(self, img):
        '''Use FFT to find the best alignment.
        '''
        pass

    def _simple_match(self, img):
        '''Use least squared difference to find the best alignment. Slow.
        '''

        # Image and reference sizes
        img_shp = list(img.shape)
        # loop is from {x,y} +- ref_{x,y} so divide by two
        ref_shp = [x/2 for x in self.ref.shape]

        ylims, xlims = [0, 0], [0, 0]
        ylims[0], xlims[0], ylims[1], xlims[1] = self.srch_area

        # Check area limits
        if xlims[0] < ref_shp[1]:
            xlims[0] = ref_shp[1]
        if ylims[0] < ref_shp[0]:
            ylims[0] = ref_shp[0]
        if xlims[1] >= img_shp[1] - ref_shp[1]:
            xlims[1] = img_shp[1] - ref_shp[1] - 1
        if ylims[1] >= img_shp[0] - ref_shp[0]:
            ylims[1] = img_shp[0] - ref_shp[0] - 1

        best_res = [2**64, None, None]

        for i in range(xlims[0], xlims[1]):
            xran = range(i-ref_shp[1], i+ref_shp[1]+1)
            for j in range(ylims[0], ylims[1]):
                sqdif = ((img[j-ref_shp[0]:j+ref_shp[0]+1,
                              xran]-self.ref)**2).sum()
                if sqdif < best_res[0]:
                    best_res = [sqdif, i, j]

        # Calculate correlation coeff for the best fit
        best_fit_data = img[best_res[2]-ref_shp[0]:best_res[2]+ref_shp[0]+1,
                            best_res[1]-ref_shp[1]:best_res[1]+ref_shp[1]+1]
        best_fit_data = best_fit_data.flatten()
        ref_flat = self.ref.flatten()
        best_corr = np.corrcoef(best_fit_data, ref_flat)**2

        return (best_corr[0, 1], best_res[1], best_res[2]) # corr, x, y

    def _calc_shift(self, img):
        '''Calculate how much the images need to be shifted.
        '''
        pass

    def _shift(self, img, x_sift, y_sift):
        '''Shift the image by x_sift and y_sift pixels.
        '''
        pass
