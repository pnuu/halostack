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

'''Module for coaligning images'''

import numpy as np
import logging
from multiprocessing import Pool

LOGGER = logging.getLogger(__name__)

class Align(object):
    '''Class to coalign images

    :param img: reference image
    :type img: halostack.image
    :param ref_loc: reference location
    :type ref_loc: 3-tuple or None
    :param srch_area: reference search area
    :type srch_area: 3-tuple or None
    :param cor_th: correlation threshold
    :type cor_the: float
    :param mode: alignment method
    :type mode: str
    :param nprocs: number or parallel processes used for finding best fit
    :type nprocs: int

    Available alignment methods are::

    'simple'
    '''

    def __init__(self, img, cor_th=70.0, mode='simple', nprocs=1):

        LOGGER.debug("Initiliazing aligner using %s mode.", mode)
        modes = {'simple': self._simple_match}

        self.img = img
        self.correlation_threshold = cor_th
        self.nprocs = nprocs

        self.ref_loc = None
        self.srch_area = None
        self.ref = None

        self.pool = Pool(self.nprocs)

        try:
            self.align_func = modes[mode]
        except AttributeError:
            LOGGER.warning("Alignment mode %s not recognized, "
                           "using simple mode instead.",
                           mode)
            self.align_func = self._simple_match

        # default to search from the whole image
        y_size, x_size = self.img.shape[:2]
        self.srch_area = [0, 0, y_size, x_size]


    def set_reference(self, area):
        '''Set the reference area *area*.

        :param area: 3-tuple of the form (x, y, radius)
        :type area: list or tuple
        '''
        LOGGER.debug("Setting reference location: (%d, %d), radius: %d.",
                     area[0], area[1], area[2])
        self.ref_loc = area
        self._set_ref()

    def set_search_area(self, area):
        '''Set the reference search area *area*.

        :param area: 3-tuple of the form (x, y, radius)
        :type area: list or tuple
        '''
        LOGGER.debug("Setting search area to center: (%d, %d), radius: %d.",
                     area[0], area[1], area[2])
        self.srch_area = area


    def align(self, img):
        '''Align the given image with the reference image.

        :param img: image to align with the reference
        :type img: halostack.image.Image
        '''
        LOGGER.info("Calculating image alignment.")
        # Get the correlation and the location of the best match
        corr, x_loc, y_loc = self.align_func(img)
        if corr < self.correlation_threshold:
            LOGGER.warning("Correlation (%.3f) lower than the given " + \
                               "threshold (%.3f).",
                           corr, self.correlation_threshold)
            return None
        LOGGER.info("Match found, correlation: %.3lf.", corr)
        # Calculate shift
        x_shift, y_shift = self._calc_shift(x_loc, y_loc)
        LOGGER.debug("Shifting image: x = %d, y = %d.",
                    x_shift, y_shift)
        # Shift the image
        img = self._shift(img, x_shift, y_shift)

        return img


    def _set_ref(self):
        '''Set reference values.
        '''
        self.ref = self.img[self.ref_loc[1]-self.ref_loc[2]:\
                                self.ref_loc[1]+self.ref_loc[2]+1,
                            self.ref_loc[0]-self.ref_loc[2]:\
                                self.ref_loc[0]+self.ref_loc[2]+1]


    def _find_reference(self, img):
        '''Find the reference area from the given image.
        '''
        del img
        LOGGER.error("TODO: Reference search not implemented.")


    def _fft_match(self, img):
        '''Use FFT to find the best alignment.
        '''
        del img
        LOGGER.error("TODO: FFT alignment not implemented.")


    def _parallel_search(self, img, xlims, ylims, ref_shp):
        '''Search for the best match in parallel.
        '''

        data = []
        for i in range(xlims[0], xlims[1]):
            xran = range(i-ref_shp[1], i+ref_shp[1]+1)
            data.append((img[:, xran], ylims, self.ref))

        result = self.pool.map(_simple_search_worker, data)

        result = np.array(result)
        idx = np.argmin(result[:, 0])

        return [result[idx, 0], idx+xlims[0], int(result[idx, 1])]


    def _simple_match(self, img):
        '''Use least squared difference to find the best alignment. Slow.
        '''
        # Image and reference sizes
        img_shp = list(img.shape)
        # loop is from {x,y} - ref_{x,y} to {x,y} + ref_{x,y} so
        # divide reference dimensions by two
        ref_shp = [i/2 for i in self.ref.shape]

        xlims = [self.srch_area[0]-self.srch_area[2],
                 self.srch_area[0]+self.srch_area[2]]
        ylims = [self.srch_area[1]-self.srch_area[2],
                 self.srch_area[1]+self.srch_area[2]]

        # Check area limits
        # minimums
        if xlims[0] < ref_shp[1]:
            xlims[0] = ref_shp[1]
        if ylims[0] < ref_shp[0]:
            ylims[0] = ref_shp[0]
        # maximums
        if xlims[1] >= img_shp[1] - ref_shp[1]:
            xlims[1] = img_shp[1] - ref_shp[1] - 1
        if ylims[1] >= img_shp[0] - ref_shp[0]:
            ylims[1] = img_shp[0] - ref_shp[0] - 1

        LOGGER.debug("Search area is in x: %d-%d, in y: %d-%d",
                     xlims[0], xlims[1],
                     ylims[0], ylims[1])

        LOGGER.debug("Searching for best match using %d thread(s).",
                     self.nprocs)
        best_res = self._parallel_search(img, xlims, ylims, ref_shp)

        # Calculate correlation coeff for the best fit
        best_fit_data = img[best_res[2]-ref_shp[0]:best_res[2]+ref_shp[0]+1,
                            best_res[1]-ref_shp[1]:best_res[1]+ref_shp[1]+1]
        best_fit_data = best_fit_data.flatten()
        ref_flat = self.ref.flatten()
        best_corr = np.corrcoef(best_fit_data, ref_flat)**2

        return (best_corr[0, 1], best_res[1], best_res[2]) # corr, x, y


    def _calc_shift(self, x_loc, y_loc):
        '''Calculate how much the images need to be shifted.
        '''
        LOGGER.debug("Calculating shift.")
        return self.ref_loc[0] - x_loc, self.ref_loc[1] - y_loc


    def _shift(self, img, x_shift, y_shift):
        '''Shift the image by x_shift and y_shift pixels.
        '''
        LOGGER.debug("Shifting image.")
        new_img = 0*img
        output_x_range, output_y_range, input_x_range, input_y_range = \
            self._calc_shift_ranges(x_shift, y_shift)
        new_img[output_y_range[0]:output_y_range[1],
                output_x_range[0]:output_x_range[1], :] = \
                img[input_y_range[0]:input_y_range[1],
                    input_x_range[0]:input_x_range[1], :]

        return new_img


    def _calc_shift_ranges(self, x_shift, y_shift):
        '''Calculate shift indices for input and output arrays.
        '''
        LOGGER.debug("Calculating shift ranges.")
        # width of the portion to be moved
        width = self.img.shape[1] - int(np.fabs(x_shift))
        # height of the portion to be moved
        height = self.img.shape[0] - int(np.fabs(y_shift))

        # Calculate the corner indices of the area to be moved
        if x_shift < 0:
            n_x1, n_x2 = 0, width
            o_x1, o_x2 = -1*x_shift, -1*x_shift+width
        else:
            n_x1, n_x2 = x_shift, x_shift+width
            o_x1, o_x2 = 0, width
        if y_shift < 0:
            n_y1, n_y2 = 0, height
            o_y1, o_y2 = -1*y_shift, -1*y_shift+height
        else:
            n_y1, n_y2 = y_shift, y_shift+height
            o_y1, o_y2 = 0, height

        output_ranges = ((n_x1, n_x2), (n_y1, n_y2))
        input_ranges = ((o_x1, o_x2), (o_y1, o_y2))

        return (output_ranges[0], output_ranges[1],
                input_ranges[0], input_ranges[1])


def _simple_search_worker(data_in):
    '''Worker function for alignment search.
    '''

    def _sum_of_squares(data):
        '''Calculate sum of squares.

        :param data: array of values
        :type data: Numpy array
        :rtype: float
        '''
        return (data**2).sum()

    data = data_in[0]
    lims = data_in[1]
    ref = data_in[2]

    ref_shp = [i/2 for i in ref.shape]
    sqdiffs = 2**64 * np.ones(lims[1])
    for j in range(lims[0], lims[1]):
        sqdiffs[j] = _sum_of_squares(data[j-ref_shp[0]:j+ref_shp[0]+1, :] - ref)

    idx = np.argmin(sqdiffs)

    return [sqdiffs[idx], idx]
