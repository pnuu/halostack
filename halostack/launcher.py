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

"""Choosing between the window and the command line.

One program provides both interfaces, which is what lets a single Windows
executable serve both.  It opens the window unless the arguments say
otherwise:

===============================  ==========================================
``halostack``                    the window
``halostack IMG_*.jpg``          the window, with those images loaded
``halostack -a avg.png *.jpg``   the command line, because an option is given
``halostack --gui -a avg.png``   the window, with the settings filled in
``halostack --cli``              the command line
``halostack --help``             the command line's help
===============================  ==========================================

Bare filenames open the window rather than the command line, so that
associating image files with Halostack does something useful.  It takes an
option to mean "do the work now and exit", which is what a script would
pass anyway.
"""

import logging
import sys

LOGGER = logging.getLogger(__name__)

#: Force the window even though options were given.
GUI_FLAGS = ('--gui',)

#: Force the command line even though nothing else was given.
CLI_FLAGS = ('--cli', '--no-gui')

#: Handled by the command line parser whatever else is on the line.
CLI_ONLY_FLAGS = ('-h', '--help', '-v', '--version')


def choose_mode(argv):
    """Decide which interface to use.

    :param argv: arguments, without the program name
    :type argv: list of str
    :rtype: ('gui' or 'cli', the remaining arguments)
    """
    argv = list(argv)
    forced_gui = [arg for arg in argv if arg in GUI_FLAGS]
    forced_cli = [arg for arg in argv if arg in CLI_FLAGS]
    rest = [arg for arg in argv if arg not in GUI_FLAGS + CLI_FLAGS]

    if forced_gui and forced_cli:
        raise ValueError("Asked for both the window and the command line; "
                         "pass only one of --gui and --cli.")
    if forced_gui:
        return 'gui', rest
    if forced_cli:
        return 'cli', rest
    if any(arg in CLI_ONLY_FLAGS for arg in rest):
        return 'cli', rest
    if not rest:
        return 'gui', rest
    # Options mean "do this now"; bare filenames mean "open these".
    if any(arg.startswith('-') and arg != '-' for arg in rest):
        return 'cli', rest

    return 'gui', rest


def main(argv=None):
    """Run Halostack, in whichever interface the arguments call for.

    :param argv: arguments, defaulting to ``sys.argv``
    :type argv: list of str or None
    :rtype: process exit status
    """
    argv = sys.argv[1:] if argv is None else list(argv)

    try:
        mode, rest = choose_mode(argv)
    except ValueError as err:
        sys.stderr.write("%s\n" % err)
        return 2

    if mode == 'cli':
        from halostack.cli import main as cli_main
        return cli_main(rest)

    from halostack.cli import parse_arguments, setup_logging
    from halostack.gui import main as gui_main

    settings = None
    if rest:
        # Fill the window in from the command line, so that
        # "halostack --gui -a avg.png *.jpg" starts where it left off.
        setup_logging()
        settings, _ = parse_arguments(rest)

    return gui_main(settings=settings)


if __name__ == "__main__":
    sys.exit(main())
