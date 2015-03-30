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
                               get_two_points, read_config)
import argparse
import logging

# log pattern
LOG_FMT = '%(asctime)s - %(name)s - %(levelname)s: %(message)s'

# Assemble dictionary config
LOG_CONFIG = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
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

def logging_setup(args):
    '''Setup logging.
    '''

#    global LOGGER

    # Clear earlier handlers
    # LOGGER.handlers = []

    if args is None:
        loglevel = logging.DEBUG #INFO
    else:
        loglevel = args.get("loglevel", "DEBUG").upper()
        try:
            loglevel = getattr(logging, loglevel)
        except AttributeError:
            loglevel = logging.INFO

    LOGGER.setLevel(loglevel) # = logging.getLogger("halostack_cli")


def halostack_cli(args):
    '''Commandline interface.'''

    images = args['fname_in']

    if len(images) == 0:
        LOGGER.error("No images given.")
        LOGGER.error("Exiting.")
        return

    stacks = []
    for stack in args['stacks']:
        stacks.append(Stack(stack, len(images)))

    base_img = Image(fname=images[0], enhancements=args['enhance_images'])
    LOGGER.info("Using %s as base image.", base_img.fname)
    images.remove(images[0])

    if not args['no_alignment'] and len(images) > 0:
        view_img = base_img.luminance()
        if isinstance(args['view_gamma'], float):
            view_img.enhance({'gamma': args['view_gamma']})
        print "Click tight area (two opposite corners) for "\
            "reference location."
        args['focus_reference'] = get_two_points(view_img)
        LOGGER.info("Reference area: (%d, %d) with radius %d.",
                    args['focus_reference'][0],
                    args['focus_reference'][1],
                    args['focus_reference'][2])
        print "Click two corner points for the area where alignment "\
            "reference will be in every image."
        args['focus_area'] = get_two_points(view_img)
        print args['focus_area']
        LOGGER.info("User-selected search area: (%d, %d) with radius %d.",
                    args['focus_area'][0],
                    args['focus_area'][1],
                    args['focus_area'][2])
        del view_img

    for stack in stacks:
        LOGGER.debug("Adding %s to %s stack", base_img.fname, stack.mode)
        stack.add_image(base_img)

    LOGGER.debug("Initializing alignment.")
    aligner = Align(base_img, ref_loc=args['focus_reference'],
                    srch_area=args['focus_area'],
                    cor_th=args['correlation_threshold'])
    LOGGER.info("Alignment initialized.")

    for img in images:
        # Read image
        LOGGER.info("Reading %s.", img)
        img = Image(fname=img, enhancements=args['enhance_images'])
        # align image
        LOGGER.info("Aligning image.")
        img = aligner.align(img)

        if img is None:
            LOGGER.warning("Threshold was below threshold, skipping image.")
            continue

        for stack in stacks:
            LOGGER.info("Adding image to %s stack.", stack.mode)
            stack.add_image(img)

    for i in range(len(stacks)):
        LOGGER.info("Calculating %s stack", stacks[i].mode)
        img = stacks[i].calculate()
        LOGGER.info("Saving %s stack to %s.", stacks[i].mode,
                    args['stack_fnames'][i])
        img.save(args['stack_fnames'][i])

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
    parser.add_argument("-d", "--median", dest="median_stack_file",
                        default=None, metavar="FILE",
                        help="Output filename of the median stack")
    parser.add_argument("-t", "--correlation-threshold",
                        dest="correlation_threshold",
                        default=0.7, metavar="NUM", type=float,
                        help="Minimum required correlation [0.7]")
    parser.add_argument("-s", "--save-images", dest="save_postfix",
                        default=None, metavar="STR",
                        help="Save aligned images as PNG with the given " \
                            "filename postfix")
    parser.add_argument("-n", "--no-alignment", dest="no_alignment",
                        default=False, action="store_true",
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
    parser.add_argument('fname_in', metavar="FILE", type=str, nargs='*',
                        help='List of files')

    # Parse commandline input
    args = vars(parser.parse_args())

    # Read configuration from the config file if one is given
    if args["config_item"] is not None:
        args = read_config(args)

    # Re-adjust logging
    logging_setup(args)

    # Workaround for windows for getting all the filenames with *.jpg syntax
    # that is expanded by the shell in linux
    args['fname_in'] = get_filenames(args['fname_in'])
    LOGGER.debug(args['fname_in'])

    # Check which stacks will be made
    stacks = []
    stack_fnames = []
    if args['min_stack_file']:
        stacks.append('min')
        stack_fnames.append(args['min_stack_file'])
        LOGGER.debug("Added minimum stack")
    if args['max_stack_file']:
        stacks.append('max')
        stack_fnames.append(args['max_stack_file'])
        LOGGER.debug("Added maximum stack")
    if args['avg_stack_file']:
        stacks.append('mean')
        stack_fnames.append(args['avg_stack_file'])
        LOGGER.debug("Added average stack")
    if args['median_stack_file']:
        stacks.append('median')
        stack_fnames.append(args['median_stack_file'])
        LOGGER.debug("Added median stack")
    args['stacks'] = stacks
    args['stack_fnames'] = stack_fnames

    # Check which adjustments are made for each image, and then for
    # the resulting stacks
    args['enhance_images'] = parse_enhancements(args['enhance_images'])
    args['enhance_stacks'] = parse_enhancements(args['enhance_stacks'])

    LOGGER.info("Starting stacking")
    halostack_cli(args)


if __name__ == "__main__":
#    global LOGGER
    # Setup logging
    import logging.config
    logging.config.dictConfig(LOG_CONFIG)
    main()
