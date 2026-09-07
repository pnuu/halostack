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

"""The main window.

A splitter divides the image from the controls, and nothing is computed until
Run is pressed.  Undo and redo step through the states the window has been
in, so a stack that turned out worse than the previous one can be taken back.
"""

import logging
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QUndoCommand, QUndoStack
from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLabel,
                               QMainWindow, QMessageBox, QProgressBar,
                               QPushButton, QScrollArea, QSplitter,
                               QVBoxLayout, QWidget)

from halostack.cli import STACK_OPTIONS
from halostack.helpers import parse_enhancements, read_config
from halostack.image import Image
from halostack.pipeline import StackRequest
from halostack.gui.controls import ControlPanel
from halostack.gui.preview import PreviewView
from halostack.gui.worker import StackWorker

LOGGER = logging.getLogger(__name__)

#: How many previous states undo can step back through. Each one may hold a
#: full-size stack, so this is a memory budget as much as a usability choice.
UNDO_LIMIT = 10


class StateCommand(QUndoCommand):
    """One undoable change of the window's state.

    :param window: the window to restore state on
    :type window: MainWindow
    :param before: state to go back to
    :type before: dict
    :param after: state to go forward to
    :type after: dict
    :param text: what the change was, shown in the Edit menu
    :type text: str
    """

    def __init__(self, window, before, after, text):
        super().__init__(text)
        self._window = window
        self._before = before
        self._after = after

    def undo(self):
        self._window.restore_state(self._before)

    def redo(self):
        self._window.restore_state(self._after)


class MainWindow(QMainWindow):
    """Halostack's window.

    :param settings: initial settings, keyed as :mod:`halostack.cli` names them
    :type settings: dict or None
    """

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Halostack")
        self.resize(1200, 760)

        self.preview = PreviewView()
        self.controls = ControlPanel()
        self._worker = None
        self._running = False
        self._result = None
        self._result_label = ''
        self._reference_area = None
        self._search_area = None
        self._restoring = False

        self._undo_stack = QUndoStack(self)
        self._undo_stack.setUndoLimit(UNDO_LIMIT)

        self._build_layout()
        self._build_menu()
        self._connect()

        if settings:
            self.controls.set_settings(settings)
        self._state = self.capture_state()
        self._update_preview()
        self._update_actions()

    # -- construction ----------------------------------------------------

    def _build_layout(self):
        """Split the window into the image and the controls."""
        scroll = QScrollArea()
        scroll.setWidget(self.controls)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(400)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._image_pane())
        splitter.addWidget(scroll)
        # The image takes the space freed by widening the window; the
        # controls keep their width.
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([760, 440])
        self.setCentralWidget(splitter)

        self._progress = QProgressBar()
        self._progress.setMaximumWidth(260)
        self._progress.setVisible(False)
        self.statusBar().addPermanentWidget(self._progress)
        self.statusBar().showMessage("Add some images to begin.")

    def _image_pane(self):
        """The preview, with the view selector and Run/Cancel underneath."""
        self._view_selector = QComboBox()
        self._view_selector.addItems(["Reference image", "Result"])
        self._view_selector.currentIndexChanged.connect(
            lambda _: self._update_preview())

        self.run_button = QPushButton("Run")
        self.run_button.setDefault(True)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Showing:"))
        bar.addWidget(self._view_selector)
        bar.addStretch(1)
        bar.addWidget(self.run_button)
        bar.addWidget(self.cancel_button)
        bar_widget = QWidget()
        bar_widget.setLayout(bar)

        pane = QWidget()
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.preview, 1)
        layout.addWidget(bar_widget)

        return pane

    def _build_menu(self):
        """File, Edit and View menus."""
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self._action("&Open images...", self.controls.files._add,
                                         QKeySequence.Open))
        file_menu.addSeparator()
        file_menu.addAction(self._action("&Load settings...", self._load_config))
        file_menu.addAction(self._action("&Save settings...", self._save_config,
                                         QKeySequence.Save))
        file_menu.addSeparator()
        file_menu.addAction(self._action("&Quit", self.close, QKeySequence.Quit))

        edit_menu = self.menuBar().addMenu("&Edit")
        self.undo_action = self._undo_stack.createUndoAction(self, "&Undo")
        self.undo_action.setShortcut(QKeySequence.Undo)
        self.redo_action = self._undo_stack.createRedoAction(self, "&Redo")
        self.redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self._action("&Fit to window", self.preview.fit_to_window))
        view_menu.addAction(self._action("&Actual size", self.preview.reset_zoom))

    def _action(self, text, slot, shortcut=None):
        """Build a QAction wired to *slot*."""
        action = QAction(text, self)
        action.triggered.connect(lambda _=False: slot())
        if shortcut is not None:
            action.setShortcut(shortcut)

        return action

    def _connect(self):
        """Wire the widgets together."""
        self.run_button.clicked.connect(self.run)
        self.cancel_button.clicked.connect(self.cancel)
        self.controls.reference_changed.connect(self._reference_changed)
        self.controls.changed.connect(self._update_actions)
        self.controls.pick_area_requested.connect(self._pick_area)
        self.preview.area_selected.connect(self._area_selected)
        self.preview.status_message.connect(self.statusBar().showMessage)

    # -- state and undo --------------------------------------------------

    def capture_state(self):
        """Return everything undo has to restore.

        :rtype: dict
        """
        return {'settings': self.controls.settings(),
                'reference_area': self._reference_area,
                'search_area': self._search_area,
                'result': self._result,
                'result_label': self._result_label,
                'view': self._view_selector.currentIndex()}

    def restore_state(self, state):
        """Put the window back into *state*."""
        self._restoring = True
        try:
            self.controls.set_settings(state['settings'])
            self._reference_area = state['reference_area']
            self._search_area = state['search_area']
            self._result = state['result']
            self._result_label = state['result_label']
            self._view_selector.setCurrentIndex(state['view'])
            self._state = state
        finally:
            self._restoring = False
        self._refresh_areas()
        self._update_preview()
        self._update_actions()

    def _push_state(self, text):
        """Record the change from the last recorded state to the current one."""
        after = self.capture_state()
        self._undo_stack.push(StateCommand(self, self._state, after, text))
        self._state = after

    # -- alignment areas -------------------------------------------------

    def _pick_area(self, which):
        """Put the preview into area-picking mode."""
        if self._view_selector.currentIndex() != 0:
            self._view_selector.setCurrentIndex(0)
        message = ("Drag a tight box around the alignment reference."
                   if which == 'reference' else
                   "Drag a box covering where that feature appears in every image.")
        self.preview.start_area_selection(which, message)

    def _area_selected(self, area):
        """Store an area the user dragged out."""
        which, x_c, y_c, radius = area
        if which == 'reference':
            self._reference_area = (x_c, y_c, radius)
        else:
            self._search_area = (x_c, y_c, radius)
        self._refresh_areas()
        self.statusBar().showMessage(
            "%s area set to (%d, %d) with radius %d." % (which.capitalize(),
                                                         x_c, y_c, radius))
        self._update_actions()

    def _refresh_areas(self):
        """Redraw the area outlines and their labels."""
        self.preview.show_area('reference', self._reference_area)
        self.preview.show_area('search', self._search_area)
        self.controls.set_area_labels(self._reference_area, self._search_area)

    # -- preview ---------------------------------------------------------

    def _reference_changed(self):
        """Show the newly selected reference image."""
        if self._restoring:
            return
        if self._view_selector.currentIndex() == 0:
            self._update_preview()
        self._update_actions()

    def _update_preview(self):
        """Show whichever image the view selector asks for."""
        gamma = self.controls.view_gamma.value()
        gamma = None if abs(gamma - 1.0) < 1e-6 else gamma

        if self._view_selector.currentIndex() == 1:
            if self._result is None:
                self.preview.clear_image()
                self.statusBar().showMessage("No result yet; press Run.")
                return
            self.preview.set_image(self._result.img, gamma)
            self.statusBar().showMessage(self._result_label)
            return

        fname = self.controls.files.reference()
        if not fname:
            self.preview.clear_image()
            return
        try:
            self.preview.set_image(Image(fname=fname).img, gamma)
        except Exception as err:                      # noqa: BLE001
            self.preview.clear_image()
            self.statusBar().showMessage("Could not read %s: %s"
                                         % (os.path.basename(fname), err))
            return
        self._refresh_areas()

    # -- running ---------------------------------------------------------

    def _requests(self, settings):
        """Turn the settings into the list of stacks to produce."""
        options = None
        if settings.get('kappa_sigma_params'):
            parts = str(settings['kappa_sigma_params']).split(',')
            options = {'kappa': float(parts[0])}
            if len(parts) > 1 and int(parts[1]):
                options['max_iters'] = int(parts[1])

        requests = []
        for key, mode in STACK_OPTIONS:
            if settings.get(mode + '_enabled') or settings.get(key):
                if not settings.get(mode + '_enabled'):
                    continue
                requests.append(StackRequest(
                    mode=mode, filename=settings.get(key),
                    options=options if mode == 'sigma' else None))

        return requests

    def _pipeline_settings(self):
        """Build the keyword arguments for the pipeline, or raise ValueError."""
        settings = self.controls.settings()
        if not settings['fname_in']:
            raise ValueError("Add some images first.")

        requests = self._requests(settings)
        if not requests and not settings['save_prefix']:
            raise ValueError("Tick at least one stack, or set a prefix for the "
                             "aligned images.")

        align = not settings['no_alignment']
        if align and len(settings['fname_in']) > 1:
            if self._reference_area is None or self._search_area is None:
                raise ValueError("Pick the reference area and the search area, "
                                 "or switch alignment off.")

        return {'filenames': settings['fname_in'],
                'requests': requests,
                'align': align,
                'reference': self._reference_area,
                'search_area': self._search_area,
                'correlation_threshold': settings['correlation_threshold'],
                'enhance_images': parse_enhancements(settings['enhance_images']),
                'enhance_stacks': parse_enhancements(settings['enhance_stacks']),
                'save_prefix': settings['save_prefix'],
                'bits': settings['bits'],
                'nprocs': settings['nprocs']}

    def running(self):
        """Whether a run is in progress.

        Tracked with a flag rather than by asking the thread: QThread.isRunning
        is still false for a moment after start(), which would leave Run
        enabled and Cancel greyed out during that window.
        """
        return self._running

    def run(self):
        """Start stacking. Nothing happens until this is called."""
        if self.running():
            return
        try:
            settings = self._pipeline_settings()
        except ValueError as err:
            QMessageBox.information(self, "Halostack", str(err))
            return

        self._worker = StackWorker(settings, self)
        self._worker.progressed.connect(self._progressed)
        self._worker.succeeded.connect(self._succeeded)
        self._worker.failed.connect(self._failed)
        self._worker.stopped.connect(self._stopped)
        self._worker.finished.connect(self._finished)

        self._progress.setVisible(True)
        self._progress.setRange(0, len(settings['filenames']))
        self._progress.setValue(0)
        self.statusBar().showMessage("Stacking...")
        self._running = True
        self._update_actions()
        self._worker.start()

    def cancel(self):
        """Ask a running stack to stop."""
        if self.running():
            self.statusBar().showMessage("Cancelling...")
            self.cancel_button.setEnabled(False)
            self._worker.cancel()

    def _progressed(self, stage, done, total, message):
        """Show how far along the run is."""
        if stage in ('read', 'stack'):
            self._progress.setRange(0, total)
            self._progress.setValue(done)
            self.statusBar().showMessage("Stacking %d/%d: %s"
                                         % (done, total, os.path.basename(message)))
        elif stage == 'calculate':
            self._progress.setRange(0, 0)          # busy, length unknown
            self.statusBar().showMessage("Calculating the %s stack..." % message)

    def _succeeded(self, result):
        """Show the finished stack and make the step undoable."""
        request, image = result.stacks[0] if result.stacks else (None, None)
        if image is None:
            self.statusBar().showMessage(
                "Saved %d aligned images." % result.used)
            return

        self._result = image
        names = ', '.join(req.mode for req, _ in result.stacks)
        self._result_label = ("%s stack of %d/%d images"
                              % (names, result.used, result.total))
        if result.skipped:
            self._result_label += " (%d skipped)" % len(result.skipped)
        self._view_selector.setCurrentIndex(1)
        self._update_preview()
        self._push_state("run %s" % names)

    def _failed(self, message):
        """Tell the user what went wrong."""
        self.statusBar().showMessage("Failed: %s" % message)
        QMessageBox.warning(self, "Halostack", message)

    def _stopped(self):
        """The run was cancelled."""
        self.statusBar().showMessage("Cancelled.")

    def _finished(self):
        """Clean up after any outcome."""
        self._progress.setVisible(False)
        self._progress.setRange(0, 1)
        self._running = False
        self._worker = None
        self._update_actions()

    # -- configuration files ---------------------------------------------

    def _load_config(self):
        """Read settings from a configuration file."""
        fname, _ = QFileDialog.getOpenFileName(self, "Load settings", '',
                                               "Config files (*.ini *.cfg);;"
                                               "All files (*)")
        if not fname:
            return
        args = {key: None for key in ('avg_stack_file', 'min_stack_file',
                                      'max_stack_file', 'median_stack_file',
                                      'sigma_stack_file', 'save_prefix',
                                      'view_gamma', 'correlation_threshold',
                                      'no_alignment', 'nprocs',
                                      'kappa_sigma_params')}
        args.update({'config_file': fname, 'config_item': None,
                     'enhance_images': [], 'enhance_stacks': []})
        try:
            args = read_config(args)
        except ValueError as err:
            QMessageBox.warning(self, "Halostack", str(err))
            return
        self.controls.set_settings(args)
        self._push_state("load settings")
        self.statusBar().showMessage("Loaded %s." % os.path.basename(fname))

    def _save_config(self):
        """Write the current settings to a configuration file."""
        fname, _ = QFileDialog.getSaveFileName(self, "Save settings", '',
                                               "Config files (*.ini);;"
                                               "All files (*)")
        if not fname:
            return
        settings = self.controls.settings()
        lines = ["[default]"]
        for key in sorted(settings):
            if key.endswith('_enabled') or key == 'fname_in':
                continue
            value = settings[key]
            if value in (None, '', []):
                continue
            if isinstance(value, list):
                value = ' '.join(str(item) for item in value)
            lines.append("%s = %s" % (key, value))
        with open(fname, 'w') as fid:
            fid.write('\n'.join(lines) + '\n')
        self.statusBar().showMessage("Saved %s." % os.path.basename(fname))

    # -- housekeeping ----------------------------------------------------

    def _update_actions(self):
        """Enable and disable what can be used right now."""
        running = self.running()
        self.run_button.setEnabled(not running)
        self.cancel_button.setEnabled(
            running and self._worker is not None and not self._worker.cancelled())
        self.controls.setEnabled(not running)
        self.undo_action.setEnabled(not running and self._undo_stack.canUndo())
        self.redo_action.setEnabled(not running and self._undo_stack.canRedo())

    def closeEvent(self, event):
        """Stop a running stack before the window goes away."""
        if self.running() and self._worker is not None:
            self._worker.cancel()
            self._worker.wait(5000)
        super().closeEvent(event)
