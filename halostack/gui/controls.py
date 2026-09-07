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

"""The controls pane.

Every command line option has a control here, and the settings are carried
around in a dictionary keyed exactly as :mod:`halostack.cli` names them, so
that a configuration file written by one can be read by the other.

The enhancement controls are built from
:data:`halostack.enhancements.ENHANCEMENTS`: adding a method to that registry
makes it appear here, with its parameters and their defaults, without any
change to this module.
"""

import logging
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox,
                               QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QGridLayout,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton,
                               QSpinBox, QVBoxLayout, QWidget)

from halostack.enhancements import ENHANCEMENTS
from halostack.stack import Stack

LOGGER = logging.getLogger(__name__)

#: Stack modes, their command line letters and the settings key of each.
STACK_MODES = (('mean', 'Average (-a)', 'avg_stack_file'),
               ('min', 'Minimum (-m)', 'min_stack_file'),
               ('max', 'Maximum (-M)', 'max_stack_file'),
               ('median', 'Median (-d)', 'median_stack_file'),
               ('sigma', 'Kappa-sigma (-S)', 'sigma_stack_file'))

IMAGE_FILTER = ("Images (*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.cr2 *.cr3 "
                "*.nef *.arw *.dng *.orf *.raf *.rw2);;All files (*)")
SAVE_FILTER = "PNG (*.png);;TIFF (*.tif);;JPEG (*.jpg);;All files (*)"


class EnhancementDialog(QDialog):
    """Pick one image processing method and fill in its arguments."""

    def __init__(self, parent=None, initial=''):
        super().__init__(parent)
        self.setWindowTitle("Image processing method")

        self._names = sorted(ENHANCEMENTS)
        self._fields = []

        self._combo = QComboBox()
        self._combo.addItems(self._names)
        self._combo.currentTextChanged.connect(self._rebuild)

        self._summary = QLabel()
        self._summary.setWordWrap(True)

        self._form = QFormLayout()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Method:"))
        layout.addWidget(self._combo)
        layout.addWidget(self._summary)
        layout.addLayout(self._form)
        layout.addStretch(1)
        layout.addWidget(buttons)

        name, args = _split_enhancement(initial)
        if name in self._names:
            self._combo.setCurrentText(name)
        self._rebuild(self._combo.currentText())
        for field, value in zip(self._fields, args):
            field.setText(str(value))

    def _rebuild(self, name):
        """Show one input per parameter of the selected method."""
        while self._form.rowCount():
            self._form.removeRow(0)
        self._fields = []

        enhancement = ENHANCEMENTS[name]
        self._summary.setText(enhancement.summary)
        for parameter in enhancement.parameters:
            field = QLineEdit()
            hint = ('required' if parameter.default is None
                    else 'default: %s' % parameter.default)
            field.setPlaceholderText(hint)
            field.setToolTip(parameter.description)
            self._form.addRow("%s:" % parameter.name, field)
            self._fields.append(field)

    def value(self):
        """Return the method as a command line style string.

        :rtype: str, for example ``'usm:25,2'``
        """
        name = self._combo.currentText()
        args = []
        for field in self._fields:
            text = field.text().strip()
            if not text:
                # Arguments are positional, so the first one left empty ends
                # the list; everything after it takes its default.
                break
            args.append(text)

        return '%s:%s' % (name, ','.join(args)) if args else name


def _split_enhancement(text):
    """Split ``'usm:25,2'`` into ``('usm', ['25', '2'])``."""
    name, _, arguments = str(text).partition(':')

    return name, [part for part in arguments.split(',') if part]


class EnhancementList(QWidget):
    """An ordered list of image processing methods."""

    changed = Signal()

    def __init__(self, title, parent=None):
        super().__init__(parent)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.setToolTip("Applied in this order.")
        self._list.itemDoubleClicked.connect(lambda _: self._edit())

        buttons = QHBoxLayout()
        for label, slot in (("Add", self._add), ("Edit", self._edit),
                            ("Remove", self._remove), ("Up", self._up),
                            ("Down", self._down)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            buttons.addWidget(button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(title))
        layout.addWidget(self._list)
        layout.addLayout(buttons)

    def _add(self):
        dialog = EnhancementDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._list.addItem(QListWidgetItem(dialog.value()))
            self.changed.emit()

    def _edit(self):
        item = self._list.currentItem()
        if item is None:
            return
        dialog = EnhancementDialog(self, item.text())
        if dialog.exec() == QDialog.Accepted:
            item.setText(dialog.value())
            self.changed.emit()

    def _remove(self):
        row = self._list.currentRow()
        if row >= 0:
            self._list.takeItem(row)
            self.changed.emit()

    def _move(self, delta):
        row = self._list.currentRow()
        target = row + delta
        if row < 0 or not 0 <= target < self._list.count():
            return
        item = self._list.takeItem(row)
        self._list.insertItem(target, item)
        self._list.setCurrentRow(target)
        self.changed.emit()

    def _up(self):
        self._move(-1)

    def _down(self):
        self._move(1)

    def values(self):
        """Return the methods as command line style strings.

        :rtype: list of str
        """
        return [self._list.item(row).text() for row in range(self._list.count())]

    def set_values(self, values):
        """Replace the list with *values*."""
        self._list.clear()
        for value in values or []:
            self._list.addItem(QListWidgetItem(str(value)))


class FileList(QWidget):
    """The images to stack, in order; the first is the alignment reference."""

    changed = Signal()
    reference_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._list.setTextElideMode(Qt.ElideLeft)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.currentRowChanged.connect(lambda _: self.reference_changed.emit())

        buttons = QHBoxLayout()
        for label, slot in (("Add...", self._add), ("Remove", self._remove),
                            ("Clear", self._clear), ("Up", self._up),
                            ("Down", self._down)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            buttons.addWidget(button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("The first image is the alignment reference."))
        layout.addWidget(self._list)
        layout.addLayout(buttons)

    def _add(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Select images", '',
                                                 IMAGE_FILTER)
        if fnames:
            self.add_files(fnames)

    def add_files(self, fnames):
        """Append *fnames*, skipping ones already in the list."""
        existing = set(self.values())
        added = False
        for fname in fnames:
            if fname not in existing:
                self._list.addItem(QListWidgetItem(fname))
                added = True
        if added:
            self.changed.emit()
            self.reference_changed.emit()

    def _remove(self):
        for item in self._list.selectedItems():
            self._list.takeItem(self._list.row(item))
        self.changed.emit()
        self.reference_changed.emit()

    def _clear(self):
        self._list.clear()
        self.changed.emit()
        self.reference_changed.emit()

    def _move(self, delta):
        row = self._list.currentRow()
        target = row + delta
        if row < 0 or not 0 <= target < self._list.count():
            return
        item = self._list.takeItem(row)
        self._list.insertItem(target, item)
        self._list.setCurrentRow(target)
        self.changed.emit()
        self.reference_changed.emit()

    def _up(self):
        self._move(-1)

    def _down(self):
        self._move(1)

    def values(self):
        """Return the filenames, in order.

        :rtype: list of str
        """
        return [self._list.item(row).text() for row in range(self._list.count())]

    def set_values(self, values):
        """Replace the list with *values*."""
        self._list.clear()
        for value in values or []:
            self._list.addItem(QListWidgetItem(str(value)))

    def reference(self):
        """The image the preview shows: the selected one, else the first.

        :rtype: str or None
        """
        item = self._list.currentItem()
        if item is not None:
            return item.text()
        values = self.values()

        return values[0] if values else None


class ControlPanel(QWidget):
    """Every setting the pipeline takes, as widgets.

    :signal changed: emitted whenever any setting changes
    :signal reference_changed: emitted when the image to preview changes
    :signal pick_area_requested: emitted with ``'reference'`` or ``'search'``
    """

    changed = Signal()
    reference_changed = Signal()
    pick_area_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.files = FileList()
        self.enhance_images = EnhancementList("Applied to every input image (-e)")
        self.enhance_stacks = EnhancementList("Applied to every finished stack (-E)")

        self._stack_boxes = {}
        self._stack_fields = {}

        layout = QVBoxLayout(self)
        layout.addWidget(self._files_group())
        layout.addWidget(self._alignment_group())
        layout.addWidget(self._stacks_group())
        layout.addWidget(self._enhancements_group())
        layout.addWidget(self._output_group())
        layout.addStretch(1)

        for widget in (self.files, self.enhance_images, self.enhance_stacks):
            widget.changed.connect(self.changed)
        self.files.reference_changed.connect(self.reference_changed)

    # -- groups ----------------------------------------------------------

    def _files_group(self):
        group = QGroupBox("Images")
        layout = QVBoxLayout(group)
        layout.addWidget(self.files)

        return group

    def _alignment_group(self):
        group = QGroupBox("Alignment")
        layout = QGridLayout(group)

        self.align_box = QCheckBox("Align the images before stacking")
        self.align_box.setChecked(True)
        self.align_box.setToolTip("Unchecking this is the -n option.")
        self.align_box.toggled.connect(self._alignment_toggled)
        layout.addWidget(self.align_box, 0, 0, 1, 3)

        self.pick_reference = QPushButton("Pick reference area...")
        self.pick_reference.setToolTip(
            "Drag a tight box around the Sun, including some of the blocker.")
        self.pick_reference.clicked.connect(
            lambda: self.pick_area_requested.emit('reference'))
        self.pick_search = QPushButton("Pick search area...")
        self.pick_search.setToolTip(
            "Drag a larger box covering where that feature moves to in the "
            "other images.")
        self.pick_search.clicked.connect(
            lambda: self.pick_area_requested.emit('search'))
        layout.addWidget(self.pick_reference, 1, 0)
        layout.addWidget(self.pick_search, 2, 0)

        self.reference_label = QLabel("not set")
        self.search_label = QLabel("not set")
        layout.addWidget(self.reference_label, 1, 1)
        layout.addWidget(self.search_label, 2, 1)

        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0.0, 1.0)
        self.threshold.setSingleStep(0.05)
        self.threshold.setDecimals(2)
        self.threshold.setValue(0.7)
        self.threshold.setToolTip("Minimum correlation, the -t option.")
        self.threshold.valueChanged.connect(self.changed)
        layout.addWidget(QLabel("Correlation threshold (-t):"), 3, 0)
        layout.addWidget(self.threshold, 3, 1)

        self.view_gamma = QDoubleSpinBox()
        self.view_gamma.setRange(0.05, 5.0)
        self.view_gamma.setSingleStep(0.05)
        self.view_gamma.setDecimals(2)
        self.view_gamma.setValue(1.0)
        self.view_gamma.setToolTip(
            "Brightens the preview only, the -g option. It does not affect "
            "the stack.")
        self.view_gamma.valueChanged.connect(self.changed)
        self.view_gamma.valueChanged.connect(self.reference_changed)
        layout.addWidget(QLabel("Preview gamma (-g):"), 4, 0)
        layout.addWidget(self.view_gamma, 4, 1)

        return group

    def _alignment_toggled(self, enabled):
        """Grey out what only matters when aligning."""
        for widget in (self.pick_reference, self.pick_search, self.threshold):
            widget.setEnabled(enabled)
        self.changed.emit()

    def _stacks_group(self):
        group = QGroupBox("Stacks to produce")
        layout = QGridLayout(group)

        for row, (mode, label, key) in enumerate(STACK_MODES):
            box = QCheckBox(label)
            box.toggled.connect(self.changed)
            field = QLineEdit()
            field.setMinimumWidth(90)
            field.setPlaceholderText("output file")
            field.textChanged.connect(self.changed)
            browse = QPushButton("...")
            browse.setMaximumWidth(32)
            browse.clicked.connect(lambda _=False, f=field: self._browse_save(f))
            layout.addWidget(box, row, 0)
            layout.addWidget(field, row, 1)
            layout.addWidget(browse, row, 2)
            self._stack_boxes[mode] = box
            self._stack_fields[mode] = field
        self._stack_boxes['mean'].setChecked(True)

        self.kappa = QDoubleSpinBox()
        self.kappa.setRange(0.1, 20.0)
        self.kappa.setSingleStep(0.1)
        self.kappa.setValue(2.0)
        self.kappa.valueChanged.connect(self.changed)
        self.iterations = QSpinBox()
        self.iterations.setRange(0, 100)
        self.iterations.setSpecialValueText("auto")
        self.iterations.setValue(0)
        self.iterations.setToolTip("0 uses the default, one eighth of the "
                                   "number of images.")
        self.iterations.valueChanged.connect(self.changed)
        row = len(STACK_MODES)
        layout.addWidget(QLabel("Kappa, iterations (-k):"), row, 0)
        kappa_row = QHBoxLayout()
        kappa_row.addWidget(self.kappa)
        kappa_row.addWidget(self.iterations)
        layout.addLayout(kappa_row, row, 1)

        return group

    def _browse_save(self, field):
        """Ask for an output filename and put it in *field*."""
        fname, _ = QFileDialog.getSaveFileName(self, "Output file", field.text(),
                                               SAVE_FILTER)
        if fname:
            field.setText(fname)

    def _enhancements_group(self):
        group = QGroupBox("Image processing")
        layout = QVBoxLayout(group)
        layout.addWidget(self.enhance_images)
        layout.addWidget(self.enhance_stacks)

        return group

    def _output_group(self):
        group = QGroupBox("Output")
        layout = QGridLayout(group)

        self.save_prefix = QLineEdit()
        self.save_prefix.setPlaceholderText("not saving aligned images")
        self.save_prefix.setToolTip(
            "Save each aligned image as PNG with this prefix, the -s option.")
        self.save_prefix.textChanged.connect(self.changed)
        layout.addWidget(QLabel("Aligned image prefix (-s):"), 0, 0)
        layout.addWidget(self.save_prefix, 0, 1)

        self.bits = QComboBox()
        self.bits.addItems(["16", "8"])
        self.bits.currentTextChanged.connect(self.changed)
        layout.addWidget(QLabel("Bits per channel:"), 1, 0)
        layout.addWidget(self.bits, 1, 1)

        self.nprocs = QSpinBox()
        self.nprocs.setRange(1, 64)
        self.nprocs.setValue(1)
        self.nprocs.setToolTip("Worker threads, the -p option.")
        self.nprocs.valueChanged.connect(self.changed)
        layout.addWidget(QLabel("Workers (-p):"), 2, 0)
        layout.addWidget(self.nprocs, 2, 1)

        return group

    # -- settings --------------------------------------------------------

    def set_area_labels(self, reference, search):
        """Show which alignment areas have been picked."""
        self.reference_label.setText(
            "not set" if reference is None else "(%d, %d) r=%d" % tuple(reference))
        self.search_label.setText(
            "not set" if search is None else "(%d, %d) r=%d" % tuple(search))

    def settings(self):
        """Return every setting, keyed as :mod:`halostack.cli` names them.

        :rtype: dict
        """
        iterations = self.iterations.value()
        kappa_sigma = '%g,%d' % (self.kappa.value(), iterations) if iterations \
            else '%g' % self.kappa.value()

        settings = {
            'fname_in': self.files.values(),
            'no_alignment': not self.align_box.isChecked(),
            'correlation_threshold': self.threshold.value(),
            'view_gamma': self.view_gamma.value(),
            'kappa_sigma_params': kappa_sigma,
            'save_prefix': self.save_prefix.text().strip() or None,
            'bits': int(self.bits.currentText()),
            'nprocs': self.nprocs.value(),
            'enhance_images': self.enhance_images.values(),
            'enhance_stacks': self.enhance_stacks.values(),
        }
        for mode, _, key in STACK_MODES:
            enabled = self._stack_boxes[mode].isChecked()
            settings[key] = self._stack_fields[mode].text().strip() or None \
                if enabled else None
            settings[mode + '_enabled'] = enabled

        return settings

    def set_settings(self, settings):
        """Apply *settings*, ignoring keys that have no control."""
        settings = dict(settings or {})

        if 'fname_in' in settings:
            self.files.set_values(settings['fname_in'])
        if settings.get('no_alignment') is not None:
            self.align_box.setChecked(not settings['no_alignment'])
        if settings.get('correlation_threshold') is not None:
            self.threshold.setValue(float(settings['correlation_threshold']))
        if settings.get('view_gamma') is not None:
            self.view_gamma.setValue(float(settings['view_gamma']))
        if settings.get('save_prefix') is not None:
            self.save_prefix.setText(str(settings['save_prefix']))
        if settings.get('bits') is not None:
            self.bits.setCurrentText(str(settings['bits']))
        if settings.get('nprocs') is not None:
            self.nprocs.setValue(int(settings['nprocs']))
        if settings.get('enhance_images') is not None:
            self.enhance_images.set_values(settings['enhance_images'])
        if settings.get('enhance_stacks') is not None:
            self.enhance_stacks.set_values(settings['enhance_stacks'])
        if settings.get('kappa_sigma_params'):
            parts = str(settings['kappa_sigma_params']).split(',')
            self.kappa.setValue(float(parts[0]))
            self.iterations.setValue(int(parts[1]) if len(parts) > 1 else 0)

        for mode, _, key in STACK_MODES:
            fname = settings.get(key)
            enabled = settings.get(mode + '_enabled',
                                   fname is not None and fname != '')
            self._stack_boxes[mode].setChecked(bool(enabled))
            if fname:
                self._stack_fields[mode].setText(str(fname))
