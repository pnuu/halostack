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

"""Running the pipeline without freezing the window.

Stacking takes seconds to minutes, so it runs on a worker thread and reports
back through signals.  Exactly one worker exists at a time: the window
disables Run until the current one has finished.
"""

import logging
import threading

from PySide6.QtCore import QThread, Signal

from halostack.pipeline import Cancelled, stack_images

LOGGER = logging.getLogger(__name__)


class StackWorker(QThread):
    """Runs :func:`halostack.pipeline.stack_images` on a worker thread.

    :param settings: keyword arguments for the pipeline
    :type settings: dict

    :signal progressed: ``(stage, done, total, message)`` from the pipeline
    :signal succeeded: the :class:`~halostack.pipeline.StackingResult`
    :signal failed: a message describing what went wrong
    :signal stopped: the run was cancelled
    """

    progressed = Signal(str, int, int, str)
    succeeded = Signal(object)
    failed = Signal(str)
    stopped = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = dict(settings)
        self._cancel = threading.Event()

    def cancel(self):
        """Ask the run to stop at the next frame or stack boundary."""
        LOGGER.info("Cancellation requested.")
        self._cancel.set()

    def cancelled(self):
        """Whether cancellation has been requested."""
        return self._cancel.is_set()

    def run(self):
        """Run the pipeline; called by Qt on the worker thread."""
        try:
            result = stack_images(progress=self._progress, cancel=self._cancel,
                                  **self._settings)
        except Cancelled:
            self.stopped.emit()
        except Exception as err:                      # noqa: BLE001
            # Anything the pipeline raises has to reach the window rather
            # than killing the thread silently.
            LOGGER.exception("Stacking failed.")
            self.failed.emit(str(err) or err.__class__.__name__)
        else:
            self.succeeded.emit(result)

    def _progress(self, stage, done, total, message):
        """Forward the pipeline's progress callback as a signal."""
        self.progressed.emit(stage, int(done), int(total), str(message))
