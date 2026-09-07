#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Halostack's graphical interface.

Importing this package pulls in Qt, so nothing outside it may import it at
module level; the core stays usable without a GUI toolkit installed.
"""

import ctypes.util
import logging
import os
import sys

LOGGER = logging.getLogger(__name__)

#: How to install libxcb-cursor, which Qt 6.5 and later need before the "xcb"
#: platform plugin will load. Qt's own message names neither the package nor
#: the distribution, which is the whole reason for this list.
XCB_CURSOR_PACKAGES = (
    ("Debian, Ubuntu, Mint", "sudo apt install libxcb-cursor0"),
    ("Fedora, RHEL", "sudo dnf install xcb-util-cursor"),
    ("openSUSE", "sudo zypper install libxcb-cursor0"),
    ("Arch", "sudo pacman -S xcb-util-cursor"),
    ("conda, mamba", "conda install -c conda-forge xcb-util-cursor"),
)


def missing_xcb_cursor():
    """Whether Qt's X11 plugin will fail for want of a system library.

    Qt 6.5 added a dependency on ``libxcb-cursor`` to its "xcb" platform
    plugin.  When that library is absent Qt aborts the process from C++,
    before any Python exception handler can run, so the only way to say
    anything useful about it is to look before the QApplication exists.

    Returns false whenever the answer is not clearly yes: on other platforms,
    when a platform plugin has been chosen explicitly, and under Wayland,
    where the xcb plugin is not the one that will be used.

    :rtype: bool
    """
    if not sys.platform.startswith('linux'):
        return False
    if os.environ.get('QT_QPA_PLATFORM'):
        return False
    if os.environ.get('WAYLAND_DISPLAY') or not os.environ.get('DISPLAY'):
        return False

    return ctypes.util.find_library('xcb-cursor') is None


def xcb_cursor_message():
    """Return advice for a Linux system without libxcb-cursor.

    :rtype: str
    """
    lines = [
        "The window needs the X11 cursor library, and it does not look like "
        "it is installed.",
        "",
        "Qt 6.5 and later need libxcb-cursor before they can open a window, "
        "and it is a",
        "system package rather than something pip can install. Without it Qt "
        "stops with",
        '\'Could not load the Qt platform plugin "xcb"\'.',
        "",
        "Install it with whichever of these fits your system:",
        "",
    ]
    width = max(len(command) for _, command in XCB_CURSOR_PACKAGES)
    for distribution, command in XCB_CURSOR_PACKAGES:
        lines.append("    %-*s   (%s)" % (width, command, distribution))
    lines += [
        "",
        "The command line does not need it, and works either way:",
        "",
        "    halostack --cli -a average_stack.png *.jpg",
        "",
    ]

    return "\n".join(lines)


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

    if missing_xcb_cursor():
        # Printed rather than raised: the check can be wrong, and Qt starting
        # anyway is a better outcome than refusing to try.
        sys.stderr.write(xcb_cursor_message())
        sys.stderr.flush()

    from halostack.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication(argv or sys.argv[:1])
    window = MainWindow(settings=settings)
    window.show()

    return app.exec()
