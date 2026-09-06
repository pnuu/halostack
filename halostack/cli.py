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

"""Halostack command line interface.

Argument parsing, configuration files and logging only; the processing itself
is :func:`halostack.pipeline.stack_images`.
"""

import argparse
import logging
import logging.config
import sys

from halostack import __version__
from halostack.helpers import get_filenames, parse_enhancements, read_config
from halostack.pipeline import StackRequest, stack_images
from halostack.ui import MatplotlibSelector

LOG_FMT = '%(asctime)s - %(name)s - %(levelname)s: %(message)s'

LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'normal'},
        'file': {
            'class': 'logging.FileHandler',
            'filename': "halostack_cli.log",
            'level': 'DEBUG',
            'formatter': 'normal',
            'mode': 'w'}},
    'formatters': {
        'normal': {'format': LOG_FMT}},
    'loggers': {
        'halostack': {
            'level': 'DEBUG',
            'handlers': ['file', 'console']}},
}

LOGGER = logging.getLogger(__name__)

#: Command line option that selects each stack, in the order they are made.
STACK_OPTIONS = (('min_stack_file', 'min'),
                 ('max_stack_file', 'max'),
                 ('avg_stack_file', 'mean'),
                 ('median_stack_file', 'median'),
                 ('sigma_stack_file', 'sigma'))


def setup_logging():
    """Configure logging to the console and to ``halostack_cli.log``."""
    logging.config.dictConfig(LOG_CONFIG)


def build_parser():
    """Return the command line parser.

    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Stack and enhance photographs of ice crystal halos.")
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
                        help="Save aligned images as PNG with the given "
                             "filename prefix")
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
    parser.add_argument("-C", "--config-file", "--config_file",
                        dest="config_file",
                        metavar="FILE", default=None, help="Config file")
    parser.add_argument("-c", "--config-item", "--config_item",
                        dest="config_item",
                        metavar="STR", default=None,
                        help="Config item to select parameters")
    parser.add_argument("-p", "--nprocs", dest="nprocs", metavar="INT",
                        type=int, default=None,
                        help="Number of parallel workers")
    parser.add_argument("-v", "--version", action="version",
                        version="Halostack %s" % (__version__))
    parser.add_argument('fname_in', metavar="FILE", type=str, nargs='*',
                        help='List of files')

    return parser


def collect_requests(args):
    """Build the list of requested stacks from parsed arguments.

    :param args: parsed command line arguments
    :type args: dict
    :rtype: list of halostack.pipeline.StackRequest
    """
    options = None
    if args.get('kappa_sigma_params'):
        parts = str(args['kappa_sigma_params']).split(',')
        options = {'kappa': float(parts[0])}
        if len(parts) > 1:
            options['max_iters'] = int(parts[1])

    requests = []
    for key, mode in STACK_OPTIONS:
        if args.get(key):
            requests.append(StackRequest(mode=mode, filename=args[key],
                                         options=options if mode == 'sigma'
                                         else None))
            LOGGER.debug("Added %s stack", mode)

    return requests


def parse_arguments(argv=None):
    """Parse the command line and apply the configuration file.

    :param argv: arguments to parse, defaulting to ``sys.argv``
    :type argv: list of str or None
    :rtype: (dict of settings, argparse.ArgumentParser)
    """
    parser = build_parser()
    args = vars(parser.parse_args(argv))

    if args['config_item'] and not args['config_file']:
        parser.error("--config-item needs a configuration file, given with "
                     "--config-file.")
    if args['config_file']:
        args = read_config(args)

    args['enhance_images'] = parse_enhancements(args['enhance_images'])
    args['enhance_stacks'] = parse_enhancements(args['enhance_stacks'])

    # Wildcards reach us unexpanded on Windows, and from the config file
    # everywhere.
    if isinstance(args['fname_in'], str):
        args['fname_in'] = args['fname_in'].split()
    args['fname_in'] = get_filenames(args['fname_in'])
    LOGGER.debug(args['fname_in'])

    if not isinstance(args['nprocs'], int):
        args['nprocs'] = 1
    if not isinstance(args['correlation_threshold'], float):
        args['correlation_threshold'] = 0.7
    if not isinstance(args['no_alignment'], bool):
        args['no_alignment'] = False

    return args, parser


def main(argv=None):
    """Run the command line interface.

    :param argv: arguments to parse, defaulting to ``sys.argv``
    :type argv: list of str or None
    :rtype: process exit status
    """
    setup_logging()
    args, parser = parse_arguments(argv)

    requests = collect_requests(args)
    if (not requests and args['save_prefix'] is None) or not args['fname_in']:
        LOGGER.error("Nothing to do.")
        parser.print_help()
        return 1

    LOGGER.info("Starting stacking")
    try:
        stack_images(args['fname_in'], requests,
                     align=not args['no_alignment'],
                     selector=MatplotlibSelector(gamma=args['view_gamma']),
                     correlation_threshold=args['correlation_threshold'],
                     enhance_images=args['enhance_images'],
                     enhance_stacks=args['enhance_stacks'],
                     save_prefix=args['save_prefix'],
                     view_gamma=args['view_gamma'],
                     nprocs=args['nprocs'])
    except (ValueError, IOError) as err:
        LOGGER.error("%s", err)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
