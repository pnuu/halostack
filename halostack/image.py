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

'''Module for image I/O and conversions'''

from PythonMagick import Image as PMImage
from PythonMagick import Blob
import numpy as np
import itertools
import logging
from multiprocessing import Pool

LOGGER = logging.getLogger(__name__)

class Image(object):
    '''Class for handling images.

    :param img: array holding image data
    :type img: ndarray or None
    :param fname: image filename
    :type fname: str or None
    :param enhancements: image processing applied to the image
    :type enhancements: dictionary or None
    :param nprocs: number or parallel processes
    :type nprocs: int
    '''

    def __init__(self, img=None, fname=None, enhancements=None,
                 nprocs=1):
        self.img = img
        self.fname = fname
        self._nprocs = nprocs

        self._pool = None

        if fname is not None:
            self._read()
        if enhancements:
            LOGGER.info("Preprocessing image.")
            self.enhance(enhancements)
        self.shape = None
        self._to_numpy()

    def __add__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img.to_numpy()
            return Image(img=self.img+img.img, nprocs=self._nprocs)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img+img, nprocs=self._nprocs)

    def __radd__(self, img):
        return self.__add__(img)

    def __sub__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img.to_numpy()
            return Image(img=self.img-img.img, nprocs=self._nprocs)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img-img, nprocs=self._nprocs)

    def __rsub__(self, img):
        return self.__sub__(img)

    def __isub__(self, img):
        self.img = self.__sub__(img)

    def __mul__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img.to_numpy()
            return Image(img=self.img*img.img, nprocs=self._nprocs)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img*img, nprocs=self._nprocs)

    def __rmul__(self, img):
        return self.__mul__(img)

    def __div__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            self._to_numpy()
            img.to_numpy()
            return Image(img=self.img/img.img, nprocs=self._nprocs)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img/img, nprocs=self._nprocs)

    def __abs__(self):
        self._to_numpy()
        return Image(img=np.abs(self.img), nprocs=self._nprocs)

    def __lt__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img.to_numpy()
            img = img.img
        return self.img < img

    def __le__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img.to_numpy()
            img = img.img
        return self.img <= img

    def __gt__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img.to_numpy()
            img = img.img
        return self.img > img

    def __ge__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img.to_numpy()
            img = img.img
        return self.img >= img

    def __eq__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img.to_numpy()
            img = img.img
        return self.img == img

    def __getitem__(self, idx):
        self._to_numpy()
        return self.img[idx]

    def __setitem__(self, idx, val):
        self._to_numpy()
        self.img[idx] = val

    def _read(self):
        '''Read the image.
        '''
        LOGGER.info("Reading image %s.", self.fname)
        self.img = PMImage(self.fname)

    def set_dtype(self, dtype):
        '''Set image data dtype.

        :param dtype: Convert to this Numpy dtype
        :type dtype: Numpy dtype
        '''
        self._to_numpy()
        LOGGER.debug('Changing dtype from %s to %s.',
                     self.img.dtype, str(dtype))
        self.img = self.img.astype(dtype)

    def to_numpy(self):
        '''Convert from PMImage to Numpy ndarray.
        '''
        self._to_numpy()

    def _to_numpy(self):
        '''Convert from PMImage to numpy.
        '''
        if isinstance(self.img, PMImage):
            self.img = to_numpy(self.img)
            self.shape = self.img.shape

    def _to_imagemagick(self, bits=16):
        '''Convert from numpy to PMImage.
        '''
        self.img = to_imagemagick(self.img, bits=bits)

    def save(self, fname, bits=16, enhancements=None):
        '''Save the image data.

        :param fname: output filename
        :type fname: str
        :param bits: output bit-depth
        :type bits: int
        :param enhancements: image processing applied to the image before saving
        :type enhancements: dictionary or None
        '''

        if enhancements:
            LOGGER.info("Postprocessing output image.")
            self.enhance(enhancements)
        self._to_imagemagick(bits=bits)
        LOGGER.info("Saving %s.", fname)
        self.img.write(fname)

    def min(self):
        '''Return the minimum value in the image.

        :rtype: float
        '''
        self._to_numpy()
        return np.min(self.img)

    def max(self):
        '''Return the maximum value in the image.

        :rtype: float
        '''
        self._to_numpy()
        return np.max(self.img)

    def luminance(self):
        '''Return luminance (channel average) as Numpy ndarray.

        :rtype: Numpy ndarray
        '''
        self._to_numpy()
        if len(self.img.shape) == 3:
            return Image(img=np.mean(self.img, 2), nprocs=self._nprocs)
        else:
            return Image(img=self.img, nprocs=self._nprocs)

    def enhance(self, enhancements):
        '''Enhance the image with the given function(s) and argument(s).

        :param enhancements: image processing methods
        :type enhancements: dictionary

        Available image processing methods:

        * ``br``: Blue - Red

          * possible calls:

            * ``{'br': None}``
            * ``{'br': float}``

          * optional arguments:

            * ``float``: multiplier for blue channel [``mean(red/green)``]

        * ``gr``: Green - Red

          * possible calls:

            * ``{'gr': None}``
            * ``{'gr': float}``

          * optional arguments:

            * ``float``: multiplier for red channel [``mean(green/red)``]

        * ``bg``: Blue - Green

          * possible calls:

            * ``{'bg': None}``
            * ``{'bg': float}``

          * optional arguments:

            * ``float``: multiplier for blue channel [``mean(blue/green)``]

        * ``emboss``: emboss image using *ImageMagick*

          * possible calls:

            * ``{'emboss': None}``
            * ``{'emboss': float}``
            * ``{'emboss': [float, float]}``

          * optional arguments:

            * ``float``: light source azimuth in degrees [``90``]
            * ``float``: light source elevation in degrees [``45``]

        * ``gamma``: gamma correction

          * possible calls:

            * ``{'gamma': float}``

          * required arguments:

            * ``float``: gamma value

        * ``gradient``: remove image gradient

          * possible calls:

            * ``{'gradient': None}``
            * ``{'gradient': float}``

          * optional arguments:

            * ``float`` (blur radius) [``min(image dimensions)/20``]

        * ``rgb_sub``: Subtract luminance from each color channel

          * possible calls:

            ``{'rgb_sub': None}``

        * ``rgb_mix``: Subtract luminance from each color channel and mix it
          back to the original image

          * possible calls:

            ``{'rgb_mix': None}``
            ``{'rgb_mix': float}``

          * optional arguments:

            * ``float``: mixing ratio [``0.7``]

        * ``stretch``: linear histogram stretch

          * possible calls:

            * ``{'stretch': None}``
            * ``{'stretch': float}``
            * ``{'stretch': [float, float]}``

          * optional arguments:

            * ``float``: low cut threshold [``0.01``]
            * ``float``: high cut threshold [``1 - <low cut threshold>``]

        * ``usm``: unsharp mask using *ImageMagick*

          * possible calls:

            * ``{'usm': [float, float]}``
            * ``{'usm': [float, float, float]}``
            * ``{'usm': [float, float, float, float]}``

          * required arguments:

            * ``float``: radius
            * ``float``: amount

          * optional arguments:

            * ``float``: standard deviation of the gaussian [``sqrt(radius)``]
            * ``float``: threshold [``0``]

        '''

        functions = {'usm': self._usm,
                     'emboss': self._emboss,
                     'blur': self._blur,
                     'gamma': self._gamma,
                     'br': self._blue_red_subtract,
                     'gr': self._green_red_subtract,
                     'bg': self._blue_green_subtract,
                     'rgb_sub': self._rgb_subtract,
                     'rgb_mix': self._rgb_mix,
                     'gradient': self._remove_gradient,
                     'stretch': self._stretch}

        for key in enhancements:
            LOGGER.info("Apply \"%s\".", key)
            func = functions[key]
            func(enhancements[key])

    def _channel_difference(self, chan1, chan2, multiplier=None):
        '''Calculate channel difference: chan1 * multiplier - chan2.
        '''
        self._to_numpy()
        chan1 = self.img[:, :, chan1].copy()
        chan2 = self.img[:, :, chan2].copy()
        if multiplier is None:
            idxs = np.logical_and(np.logical_and(1.5*chan1 < chan2,
                                                 2.5*chan1 > chan2),
                                  chan1 > 0)
            if np.all(np.invert(idxs)):
                multiplier = 2
            else:
                multiplier = np.mean(chan2[idxs]/chan1[idxs])
        else:
            if isinstance(multiplier, list):
                multiplier = multiplier[0]
        LOGGER.debug("Multiplier: %.3lf", multiplier)
        self.img = multiplier * chan1 - chan2


    def _blue_red_subtract(self, args):
        '''Subtract red channel from the blue channel after scaling
        the blue channel using the supplied multiplier.
        '''
        LOGGER.debug("Calculating channel difference, Blue - Red.")
        self._channel_difference(2, 0, multiplier=args)

    def _green_red_subtract(self, args):
        '''Subtract red channel from the green channel after scaling
        the green channel using the supplied multiplier.
        '''
        LOGGER.debug("Calculating channel difference, Green - Red.")
        self._channel_difference(1, 0, multiplier=args)

    def _blue_green_subtract(self, args):
        '''Subtract green channel from the blue channel after scaling
        the green channel using the supplied multiplier.
        '''
        LOGGER.debug("Calculating channel difference, Blue - Green.")
        self._channel_difference(2, 1, multiplier=args)

    def _rgb_subtract(self, args):
        '''Subtract mean(r,g,b) from all the channels.
        '''
        LOGGER.debug("Subtracting luminance from color channels.")
        del args
        self._to_numpy()
        luminance = self.luminance().img
        for i in range(3):
            self.img[:, :, i] -= luminance
        self.img -= self.img.min()


    def _rgb_mix(self, args):
        '''Subtract mean(r,g,b) from all the channels, and blend it
        back to the original image.

        :param args: mixing factor [0.7]
        :type args: float
        '''

        if args is None:
            args = 0.7
        else:
            args = args[0]

        LOGGER.debug("Mixing factor: %.2lf", args)
        self._to_numpy()
        img = Image(img=self.img.copy(), nprocs=self._nprocs)
        img.enhance({'rgb_sub': None})

        self.img *= (1-args)
        self.img += args * img.img


    def _stretch(self, args):
        '''Apply a linear stretch to the image.
        '''

        self._to_numpy()
        self.img -= self.img.min()

        if args is None:
            args = []
        if not isinstance(args, list):
            args = [args]
        if len(args) == 0:
            args.append(0.01)
        if len(args) == 1:
            args.append(1-args[0])

        LOGGER.debug("low cut: %.0f %%, high cut: %.0f %%",
                     100*args[0], 100*args[1])

        hist_num_points = 2**16 - 1

        # Use luminance
        if len(self.img.shape) == 3:
            lumin = np.mean(self.img, 2)
        else:
            lumin = self.img.copy()

        # histogram
        hist, _ = np.histogram(lumin.flatten(), hist_num_points,
                               normed=True)
        # cumulative distribution function
        cdf = hist.cumsum()
        # normalize to image maximum
        cdf = self.img.max() * cdf / cdf[-1]

        # find lower end truncation point
        start = 0
        csum = 0
        while csum < cdf[-1]*args[0]:
            csum = cdf[start]
            start += 1
        # higher end truncation point
        end = cdf.size - 1
        csum = cdf[-1]
        while csum > cdf[-1]*args[1]:
            csum = cdf[end]
            end -= 1

        LOGGER.debug("Truncation points: %d and %d", start, end)

        # calculate the corresponding data values
        start_val = start * self.img.max() / hist_num_points
        end_val = end * self.img.max() / hist_num_points

        # truncate
        self.img[self.img < start_val] = start_val
        self.img[self.img > end_val] = end_val


    def _remove_gradient(self, args):
        '''Calculate the gradient from the image, subtract from the
        original, scale back to full bit depth and return the result.
        '''
        self._to_numpy()

        args = {'method': {'blur': args}}

        gradient = self._calculate_gradient(args)
        self.img -= gradient.img

        if self.img.min() < 0:
            self.img -= self.img.min()


    def _calculate_gradient(self, args):
        '''Calculate gradient from the image using the given method.
        :param method: name of the method for calculating the gradient
        '''
        methods = {'blur': self._gradient_blur,
                   'random': self._gradient_random_points,
                   'grid': self._gradient_grid_points}
        # 'user': self._gradient_get_user_points,
        # 'mask': self._gradient_mask_points,
        # 'all': self._gradient_all_points

        LOGGER.debug("Calculating gradient.")
        try:
            func = methods[args['method'].keys()[0]]
        except TypeError:
            LOGGER.error("Method \"%s\" not available, using method \"blur\"",
                         args['method'].keys()[0])
            args = {}
            args['method'] = {'blur': None}
            func = methods['blur']
        result = func(args['method'])
        shape = self.img.shape

        if args['method'].keys()[0] in ['blur']:
            return result

        x_pts, y_pts = result
        if len(shape) == 2:
            return Image(img=self._gradient_fit_surface(x_pts, y_pts,
                                                        order=args['order']),
                         nprocs=self._nprocs)
        else:
            gradient = np.empty(shape)
            for i in range(shape[2]):
                gradient[:, :, i] = \
                    self._gradient_fit_surface(x_pts, y_pts,
                                               order=args['order'],
                                               chan=i)
            return Image(img=gradient, nprocs=self._nprocs)

    def _gradient_blur(self, args):
        '''Blur the image to get the approximation of the background
        gradient.
        '''
        gradient = Image(img=self.img.copy(), nprocs=self._nprocs)
        gradient.enhance(args)

        return gradient

    def _gradient_random_points(self, args):
        '''Automatically extract background points for gradient estimation.
        '''
        shape = self.img.shape
        y_pts = np.random.randint(shape[0], size=(args['points'],))
        x_pts = np.random.randint(shape[1], size=(args['points'],))

        return (x_pts, y_pts)

    def _gradient_grid_points(self, args):
        '''Get uniform sampling of image locations.
        '''
        shape = self.img.shape
        y_locs = np.arange(0, shape[0], args['points'])
        x_locs = np.arange(0, shape[1], args['points'])
        x_mat, y_mat = np.meshgrid(x_locs, y_locs, indexing='ij')

        return (x_mat.ravel(), y_mat.ravel())

    def _gradient_fit_surface(self, x_pts, y_pts, order=2, chan=None):
        '''Fit a surface to the given channel.
        '''
        shape = self.img.shape
        x_locs, y_locs = np.meshgrid(np.arange(shape[0]),
                                     np.arange(shape[1]))
        if chan is not None:
            poly = polyfit2d(x_pts, y_pts, self.img[y_pts, x_pts, chan].ravel(),
                             order=order)
            return polyval2d(x_locs, y_locs, poly)
        else:
            poly = polyfit2d(x_pts, y_pts, self.img[y_pts, x_pts].ravel(),
                             order=order)
            return polyval2d(x_locs, y_locs, poly).T


    def _rotate(self, *args):
        '''Rotate image.
        '''
        # use scipy.ndimage.interpolation.rotate()
        del args
        LOGGER.error("Image rotation not implemented.")

    def _usm(self, args):
        '''Use unsharp mask to enhance the image contrast.  Uses ImageMagick.
        '''

        self._to_imagemagick()
        if len(args) == 2:
            args.append(np.sqrt(args[0]))
        if len(args) == 3:
            args.append(0)
        LOGGER.debug("Radius: %.0lf, amount: %.1lf, "
                     "sigma: %.1lf, threshold: %.0lf.", args[0], args[1],
                     args[2], args[3])
        self.img.unsharpmask(*args)

    def _emboss(self, args):
        '''Emboss filter the image. Actually uses shade() from
        ImageMagick.
        '''

        if args is None:
            args = []
        if len(args) == 0:
            args.append(90)
        if len(args) == 1:
            args.append(10)
        LOGGER.debug("Azimuth: %.1lf, elevation: %.1lf.", args[0], args[1])
        self._to_imagemagick()
        self.img.shade(*args)

    def _blur_im(self, args):
        '''Blur the image using ImageMagick.
        '''
        self._to_imagemagick()
        # args['radius'], args['weight'])
        self.img.blur(*args)

    def _blur(self, args):
        '''Blur the image using 1D convolution for each column and
        row. Data borders are padded with mean of the border area
        before convolution to reduce the edge effects.
        '''
        self._to_numpy()

        shape = self.img.shape
        if args is None:
            radius = int(np.min(shape[:2])/20.)
            sigma = radius/3.
        else:
            radius = args[0]
            if len(args) > 1:
                sigma = args[1]
            else:
                sigma = radius/3.

        def form_blur_data(data, radius):
            '''Form vectors for blur.
            '''
            vect = np.zeros(2*radius+data.size-1, dtype=data.dtype)
            vect[:radius] = np.mean(data[:radius])
            vect[radius:radius+data.size] = data
            vect[-radius:] = np.mean(data[-radius:])

            return vect

        def gaussian_kernel(radius, sigma):
            ''' Generate a gaussian convolution kernel.

            'param radius: kernel radius in pixels
            'type radius: int
            'param sigma': standard deviation of the gaussian in pixels
            'type sigma: float
            '''

            sigma2 = sigma**2

            half_kernel = map(lambda x: 1/(2 * np.pi * sigma2) * \
                                  np.exp(-x**2 / (2 * sigma2)),
                              range(radius+1))
            kernel = np.zeros(2*radius+1)
            kernel[radius:] = half_kernel
            kernel[:radius+1] = half_kernel[::-1]
            kernel /= np.sum(kernel)

            return kernel

        kernel = gaussian_kernel(radius, sigma)

        LOGGER.debug("Blur radius is %.0lf pixels and sigma is %.3lf.",
                     radius, sigma)
        LOGGER.debug("Using %d threads.", self._nprocs)

        if self._nprocs > 1:
            self._pool = Pool(self._nprocs)

        for i in range(shape[-1]):
            # rows
            data = []
            for j in range(shape[0]):
                data.append([kernel, form_blur_data(self.img[j, :, i],
                                                    radius)])
            if self._nprocs > 1:
                result = self._pool.map(_blur_worker, data)
            else:
                result = map(_blur_worker, data)

            # compile result data
            for j in range(shape[0]):
                self.img[j, :, i] = result[j][2*radius:2*radius+shape[1]]

            data = []
            # columns
            for j in range(shape[1]):
                data.append([kernel, form_blur_data(self.img[:, j, i],
                                                    radius)])
            if self._nprocs > 1:
                result = self._pool.map(_blur_worker, data)
            else:
                result = map(_blur_worker, data)

            # compile result data
            for j in range(shape[1]):
                self.img[:, j, i] = result[j][2*radius:2*radius+shape[0]]

        self.img -= np.min(self.img)


    def _gamma(self, args):
        '''Apply gamma correction to the image.
        '''
        if args is None:
            return
        if not isinstance(args, list):
            args = [args]
        self._to_numpy()
        LOGGER.debug("Apply gamma correction, gamma: %.2lf.", args[0])
        self.img /= self.img.max()
        self.img **= args[0]

def _blur_worker(data_in):
    '''Worker for blurring rows in parallel.
    '''
    kernel = data_in[0]
    data = data_in[1]

    return np.convolve(data, kernel, mode='full')

def to_numpy(img):
    '''Convert ImageMagick data to numpy array.

    :param img: image to convert
    :type img: PythonMagick.Image
    :rtype: Numpy ndarray
    '''
    if not isinstance(img, np.ndarray):
        LOGGER.debug("Converting from ImageMagick to Numpy.")
        img.magick('RGB')
        blob = Blob()
        img.write(blob)
        out_img = np.fromstring(blob.data, dtype='uint'+str(img.depth()))

        height, width, chans = img.rows(), img.columns(), 3
        if img.monochrome():
            chans = 1

        return out_img.reshape(height, width, chans)

    return img

def to_imagemagick(img, bits=16):
    '''Convert numpy array to Imagemagick format.

    :param img: image to convert
    :type img: Numpy ndarray
    :rtype: PythonMagick.Image
    '''

    if not isinstance(img, PMImage):

        img = _scale(img, bits=bits)

        LOGGER.debug("Converting from Numpy to ImageMagick.")
        out_img = PMImage()
        if img.dtype == np.uint8:
            out_img.depth(8)
        else:
            out_img.depth(16)

        shape = img.shape
        # Convert also B&W images to 3-channel arrays
        if len(shape) == 2:
            tmp = np.empty((shape[0], shape[1], 3), dtype=img.dtype)
            tmp[:, :, 0] = img
            tmp[:, :, 1] = img
            tmp[:, :, 2] = img
            img = tmp
        out_img.magick('RGB')
        out_img.size(str(shape[1])+'x'+str(shape[0]))
        blob = Blob()
        blob.data = img.tostring()

        out_img.read(blob)
        out_img.magick('PNG')

        return out_img
    return img


def _scale(img, bits=16):
    '''Scale image to cover the whole bit-range.
    '''

    if img.dtype.name == 'uint%d' % bits:
        return img

    LOGGER.debug("Scaling image to %d bits.", bits)

    img -= img.min()
    img_max = np.max(img)
    if img_max != 0:
        img = (2**bits - 1) * img / img_max

    if bits <= 8:
        return img.astype('uint8')
    else:
        return img.astype('uint16')


def polyfit2d(x_loc, y_loc, z_val, order=2):
    '''Fit a 2-D polynomial to the given data.

    Implementation from: http://stackoverflow.com/a/7997925

    :param x_loc: X coordinates
    :type x_loc: list or ndarray
    :param y_loc: Y coordinates
    :type y_loc: list or ndarray
    :param z_val: Z values at (X, Y)
    :type z_val: list or ndarray
    :param order: order of the polynomial
    :type order: integer
    :rtype: list of polynomial coefficients as floats
    '''

    LOGGER.debug("Calculating 2D polynomial fit.")
    ncols = (order + 1)**2
    g_mat = np.zeros((x_loc.size, ncols))
    ij_loc = itertools.product(range(order+1), range(order+1))
    for k, (i, j) in enumerate(ij_loc):
        g_mat[:, k] = x_loc**i * y_loc**j
    poly, _, _, _ = np.linalg.lstsq(g_mat, z_val)
    return poly

def polyval2d(x_loc, y_loc, poly):
    '''Evaluate 2-D polynomial *poly* at the given locations

    Implementation from: http://stackoverflow.com/a/7997925

    :param x_loc: X coordinates
    :type x_loc: list or Numpy array
    :param y_loc: Y coordinates
    :type y_loc: list or Numpy array
    :param poly: polynomial coefficients
    :type poly: list of floats

    '''
    LOGGER.debug("Evaluating 2D polynomial.")
    order = int(np.sqrt(len(poly))) - 1
    ij_loc = itertools.product(range(order+1), range(order+1))
    surf = np.zeros_like(x_loc)
    for arr, (i, j) in zip(poly, ij_loc):
        surf += arr * x_loc**i * y_loc**j
    return surf
