#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Halostack's graphical interface.

Importing this package pulls in Qt, so nothing outside it may import it at
module level; the core stays usable without a GUI toolkit installed.
"""

import logging
import sys

LOGGER = logging.getLogger(__name__)


def main(argv=None, settings=None):
    """Open the Halostack window.

    :param argv: arguments passed to Qt itself
    :type argv: list of str or None
    :param settings: initial settings, keyed as :mod:`halostack.cli` names them
    :type settings: dict or None
    :rtype: process exit status
    """
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        sys.stderr.write(
            "The graphical interface needs PySide6, which is not installed.\n"
            "Install it with 'pip install halostack[gui]', or use the command "
            "line interface instead.\n")
        return 1

    from halostack.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication(argv or sys.argv[:1])
    window = MainWindow(settings=settings)
    window.show()

    return app.exec()
