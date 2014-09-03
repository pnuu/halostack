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

'''Halostack main.'''

from halostack.stack import Stack
from halostack.image import Image
from halostack.align import Align
from halostack.helpers import (get_filenames, parse_enhancements,
                               get_two_points)
import argparse

def cli(args):
    '''Commandline interface.'''

    images = args['fname_in']

    if len(images) == 0:
        print "No images given."
        return

    stacks = []
    for stack in args['stacks']:
        stacks.append(Stack(stack, len(images)))

    base_img = Image(fname=images[0], enhancements=args['enhance_images'])
    images.remove(images[0])

    if not args['no_alignment'] and len(images) > 0:
        print "Click tight area (two opposite corners) for "\
            "reference location."
        args['focus_reference'] = get_two_points(base_img)
        print "Click two corner points for the area where alignment "\
            "reference will be in every image."
        args['focus_area'] = get_two_points(base_img)

#        print args['focus_reference'], args['focus_area']

    for stack in stacks:
        stack.add_image(base_img)

    aligner = Align(base_img, ref_loc=args['focus_reference'],
                    srch_area=args['focus_area'])

    for img in images:
        # Read image
        img = Image(fname=img, enhancements=args['enhance_images'])
        # align image
        img = aligner.align(img)

        for stack in stacks:
            stack.add_image(img)

    for i in range(len(stacks)):
        img = stacks[i].calculate()
        img.save(args['stack_fnames'][i])

def gui(args):
    '''GUI interface. No GUI available, will use CLI'''
    cli(args)

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
#    parser.add_argument("-g", "--view-gamma", dest="view_gamma",
#                        default=None, type=float, metavar="GAMMA",
#                        help="Adjust image gamma for alignment preview")
    parser.add_argument("-c", "--config", dest="config", metavar="FILE",
                        help="Config file")
    parser.add_argument("-C", "--cli", dest="cli", default=False,
                        action="store_true", help="Start CLI instead of GUI")
    parser.add_argument('fname_in', metavar="FILE", type=str, nargs='*',
                        help='List of files')

    # Parse commandline input
    args = vars(parser.parse_args())

    # Workaround for windows for getting all the filenames with *.jpg syntax
    # that is expanded by shell in linux
    args['fname_in'] = get_filenames(args['fname_in'])

    print args

    # Check which stacks will be made
    stacks = []
    stack_fnames = []
    if args['min_stack_file']:
        stacks.append('min')
        stack_fnames.append(args['min_stack_file'])
    if args['max_stack_file']:
        stacks.append('max')
        stack_fnames.append(args['max_stack_file'])
    if args['avg_stack_file']:
        stacks.append('mean')
        stack_fnames.append(args['avg_stack_file'])
    if args['median_stack_file']:
        stacks.append('median')
        stack_fnames.append(args['median_stack_file'])
    args['stacks'] = stacks
    args['stack_fnames'] = stack_fnames
    # Check which adjustments are made for each image, and then for
    # the resulting stacks
    args['enhance_images'] = parse_enhancements(args['enhance_images'])
    args['enhance_stacks'] = parse_enhancements(args['enhance_stacks'])

    if args['cli']:
        cli(args)
    else:
        gui(args)


if __name__ == "__main__":
    main()
