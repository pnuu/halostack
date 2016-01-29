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

'''Halostack CLI main.'''

from halostack.stack import Stack
from halostack.image import Image
from halostack.align import Align
from halostack.helpers import (get_filenames, parse_enhancements,
                               get_two_points, read_config, intermediate_fname)
from halostack import __version__

import argparse
import logging
import platform

# log pattern
LOG_FMT = '%(asctime)s - %(name)s - %(levelname)s: %(message)s'

# Assemble dictionary config
LOG_CONFIG = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'normal'
            },
        'file': {
            'class': 'logging.FileHandler',
            'filename': "halostack_cli.log",
            'level': 'DEBUG',
            'formatter': 'normal',
            'mode': 'w'}
        },
    'formatters': {
        'normal': {'format': LOG_FMT}
        },
    'loggers': {
        'halostack_cli': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
            },
        'halostack.image': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
            },
        'halostack.align': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
            },
        'halostack.stack': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
            },
        'halostack.helpers': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
            },
        }
    }

LOGGER = logging.getLogger("halostack_cli")


def halostack_cli(args):
    '''Commandline interface.'''

    images = args['fname_in']

    stacks = []
    for i in range(len(args['stacks'])):
        stacks.append(Stack(args['stacks'][i], len(images),
                            nprocs=args['nprocs'],
                            kwargs=args['stack_kwargs'][i]))

    base_img_fname = images[0]
    base_img = Image(fname=base_img_fname, nprocs=args['nprocs'])
    LOGGER.debug("Using %s as base image.", base_img.fname)
    images.remove(images[0])

    if not args['no_alignment'] and len(images) > 0:
        view_img = base_img.luminance()
        if isinstance(args['view_gamma'], float):
            view_img.enhance({'gamma': args['view_gamma']})
        print "\nClick tight area (two opposite corners) for "\
            "reference location.\n"
        args['focus_reference'] = get_two_points(view_img)
        LOGGER.debug("Reference area: (%d, %d) with radius %d.",
                     args['focus_reference'][0],
                     args['focus_reference'][1],
                     args['focus_reference'][2])
        print "Click two corner points for the area where alignment "\
            "reference will be in every image.\n"
        args['focus_area'] = get_two_points(view_img)

        LOGGER.debug("User-selected search area: (%d, %d) with radius %d.",
                    args['focus_area'][0],
                    args['focus_area'][1],
                    args['focus_area'][2])
        del view_img

    aligner = None
    if not args['no_alignment'] and len(images) > 0:
        LOGGER.debug("Initializing alignment.")
        aligner = Align(base_img,
                        cor_th=args['correlation_threshold'],
                        nprocs=args['nprocs'])
        aligner.set_reference(args['focus_reference'])
        aligner.set_search_area(args['focus_area'])
        LOGGER.debug("Alignment initialized.")

    if args['save_prefix'] is not None:
        fname = intermediate_fname(args['save_prefix'], base_img_fname)
        base_img.save(fname)

    if len(args['enhance_images']) > 0:
        LOGGER.info("Preprocessing image.")
        base_img.enhance(args['enhance_images'])

    for stack in stacks:
        stack.add_image(base_img)

    # memory management
    del base_img
    base_img = None

    skipped_images = []
    for img_fname in images:
        # Read image
        img = Image(fname=img_fname, nprocs=args['nprocs'])

        if not args['no_alignment'] and len(images) > 1:
            # align image
            img = aligner.align(img)

        if img is None:
            LOGGER.warning("Skipping image.")
            skipped_images.append(img_fname)
            continue

        if args['save_prefix'] is not None:
            fname = intermediate_fname(args['save_prefix'], img_fname)
            img.save(fname)

        if len(args['enhance_images']) > 0:
            LOGGER.info("Preprocessing image.")
            img.enhance(args['enhance_images'])

        for stack in stacks:
            stack.add_image(img)

        del img
        img = None

    if aligner is not None:
        del aligner
        aligner = None

    for i in range(len(stacks)):
        img = stacks[i].calculate()
        img.save(args['stack_fnames'][i],
                 enhancements=args['enhance_stacks'])

    if len(images) > 1:
        LOGGER.info("Stacked %d/%d images.", len(images)+1-len(skipped_images),
                    len(images)+1)
    if len(skipped_images) > 0:
        LOGGER.warning("Images that were not used: %s",
                       '\n\t' + '\n\t'.join(skipped_images))


def main():
    '''Main. Only commandline and config file parsing is done here.'''
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--average-stack", dest="avg_stack_file",
                        default=None, metavar="FILE",
                        help="Output filename of the average stack")
    parser.add_argument("-m", "--min-stack", dest="min_stack_file",
                        default=None, metavar="FILE",
                        help="Output filename of the minimum stack")
    parser.add_argument("-M", "--max-stack", dest="max_stack_file",
                        default=None, metavar="FILE",
                        help="Output filename of the maximum stack")
    parser.add_argument("-d", "--median-stack", dest="median_stack_file",
                        default=None, metavar="FILE",
                        help="Output filename of the median stack")
    parser.add_argument("-S", "--sigma-stack", dest="sigma_stack_file",
                        default=None, metavar="FILE",
                        help="Output filename of the kappa-sigma stack")
    parser.add_argument("-k", "--kappa-sigma-params", dest="kappa_sigma_params",
                        default=None, metavar="KAPPA,ITERATIONS",
                        help="Kappa and iterations for the kappa-sigma stack")
    parser.add_argument("-t", "--correlation-threshold",
                        dest="correlation_threshold",
                        default=None, metavar="NUM", type=float,
                        help="Minimum required correlation [0.7]")
    parser.add_argument("-s", "--save-images", dest="save_prefix",
                        default=None, metavar="STR",
                        help="Save aligned images as PNG with the given " \
                            "filename postfix")
    parser.add_argument("-n", "--no-alignment", dest="no_alignment",
                        default=None, action="store_true",
                        help="Stack without alignment")
    parser.add_argument("-e", "--enhance-images", dest="enhance_images",
                        default=[], type=str, action="append",
                        help="Enhancement functions applied to each image")
    parser.add_argument("-E", "--enhance-stacks", dest="enhance_stacks",
                        default=[], type=str, action="append",
                        help="Enhancement function to apply to each stack")
    parser.add_argument("-g", "--view-gamma", dest="view_gamma",
                        default=None, type=float, metavar="GAMMA",
                        help="Adjust image gamma for alignment preview")
    parser.add_argument("-C", "--config_file", dest="config_file",
                        metavar="FILE", default=None, help="Config file")
    parser.add_argument("-c", "--config_item", dest="config_item",
                        metavar="STR", default=None,
                        help="Config item to select parameters")
    parser.add_argument("-p", "--nprocs", dest="nprocs", metavar="INT",
                        type=int, default=None,
                        help="Number of parallel processes")
    parser.add_argument("-v", "--version", action="version",
                        version="Halostack %s" % (__version__))
    parser.add_argument('fname_in', metavar="FILE", type=str, nargs='*',
                        help='List of files')

    # Parse commandline input
    args = vars(parser.parse_args())

    # Read configuration from the config file if one is given
    if args["config_item"] is not None:
        args = read_config(args)

    # Check which adjustments are made for each image, and then for
    # the resulting stacks
    args['enhance_images'] = parse_enhancements(args['enhance_images'])
    args['enhance_stacks'] = parse_enhancements(args['enhance_stacks'])

    # Workaround for windows for getting all the filenames with *.jpg syntax
    # that is expanded by the shell in linux
    args['fname_in'] = get_filenames(args['fname_in'])
    LOGGER.debug(args['fname_in'])

    # Check validity
    if not isinstance(args['nprocs'], int):
        args['nprocs'] = 1
    if not isinstance(args['correlation_threshold'], float):
        args['correlation_threshold'] = 0.7
    if not isinstance(args['no_alignment'], bool):
        args['no_alignment'] = False
    if platform.system() == 'Windows':
        LOGGER.warning("Your operating system is Windows, "
                       "so limiting to one processor.")
        args['nprocs'] = 1

    # Check which stacks will be made
    stacks = []
    stack_fnames = []
    stack_kwargs = []
    if args['min_stack_file']:
        stacks.append('min')
        stack_fnames.append(args['min_stack_file'])
        stack_kwargs.append(None)
        LOGGER.debug("Added minimum stack")
    if args['max_stack_file']:
        stacks.append('max')
        stack_fnames.append(args['max_stack_file'])
        stack_kwargs.append(None)
        LOGGER.debug("Added maximum stack")
    if args['avg_stack_file']:
        stacks.append('mean')
        stack_fnames.append(args['avg_stack_file'])
        stack_kwargs.append(None)
        LOGGER.debug("Added average stack")
    if args['median_stack_file']:
        stacks.append('median')
        stack_fnames.append(args['median_stack_file'])
        stack_kwargs.append(None)
        LOGGER.debug("Added median stack")
    if args['sigma_stack_file']:
        stacks.append('sigma')
        stack_fnames.append(args['sigma_stack_file'])
        if args['kappa_sigma_params']:
            tmp = args['kappa_sigma_params'].split(',')
            stack_kwargs.append({'kappa': float(tmp[0]),
                                 'max_iters': int(tmp[1])})
        else:
            stack_kwargs.append(None)
        LOGGER.debug("Added median stack")
    args['stacks'] = stacks
    args['stack_fnames'] = stack_fnames
    args['stack_kwargs'] = stack_kwargs

    # Check if there's anything to do
    if len(args['stacks']) == 0 and args['save_prefix'] is None or \
            len(args['fname_in']) == 0:
        LOGGER.error("Nothing to do.")
        parser.print_help()
        return

    LOGGER.info("Starting stacking")

    halostack_cli(args)


if __name__ == "__main__":
    # Setup logging
    import logging.config
    logging.config.dictConfig(LOG_CONFIG)
    main()
