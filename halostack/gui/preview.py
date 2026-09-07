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

"""The image pane.

Shows one image at a time and lets the user drag out the two areas that
alignment needs, which is the job the Matplotlib window used to do.  Unlike
that window this one stays open, redraws as the window is resized, and can be
zoomed and panned.
"""

import logging

import numpy as np
from PySide6.QtCore import QPoint, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPen, QPixmap
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsView, QRubberBand)

from halostack.ui import preview_data

LOGGER = logging.getLogger(__name__)

#: Colours of the two area overlays.
REFERENCE_COLOUR = QColor(80, 200, 120)
SEARCH_COLOUR = QColor(240, 180, 60)


def to_qimage(img, gamma=None):
    """Convert image data to a QImage for display.

    :param img: image data, any range
    :type img: numpy.ndarray or halostack.image.Image
    :param gamma: gamma applied to the preview only
    :type gamma: float or None
    :rtype: PySide6.QtGui.QImage
    """
    data = np.ascontiguousarray(preview_data(img, gamma))

    if data.ndim == 2:
        height, width = data.shape
        image = QImage(data.data, width, height, width, QImage.Format_Grayscale8)
    else:
        height, width, channels = data.shape
        if channels != 3:
            data = np.ascontiguousarray(data[:, :, :3])
            channels = 3
        image = QImage(data.data, width, height, width * channels,
                       QImage.Format_RGB888)

    # QImage does not take ownership of the buffer, and `data` is local.
    return image.copy()


class PreviewView(QGraphicsView):
    """Displays an image and collects the alignment areas from the user.

    :signal area_selected: emitted with an (x, y, radius) tuple when the user
                           finishes dragging out an area
    :signal status_message: emitted with text describing what to do next
    """

    area_selected = Signal(tuple)
    status_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        self.setRenderHints(self.renderHints())
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setBackgroundBrush(QBrush(QColor(32, 32, 32)))
        self.setAlignment(Qt.AlignCenter)

        self._fit_to_window = True
        self._selecting = None
        self._origin = QPoint()
        self._rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self._overlays = {}
        self._has_image = False

    # -- displaying ------------------------------------------------------

    def clear_image(self):
        """Remove the displayed image."""
        self._pixmap_item.setPixmap(QPixmap())
        self._has_image = False

    def set_image(self, img, gamma=None):
        """Show *img*, keeping the current zoom unless fitting to the window.

        :param img: image data
        :type img: numpy.ndarray or halostack.image.Image
        :param gamma: gamma applied to the preview only
        :type gamma: float or None
        """
        pixmap = QPixmap.fromImage(to_qimage(img, gamma))
        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self._has_image = True
        if self._fit_to_window:
            self.fit_to_window()

    def has_image(self):
        """Whether an image is currently displayed."""
        return self._has_image

    def fit_to_window(self):
        """Scale the image so that all of it is visible."""
        self._fit_to_window = True
        if self._has_image:
            self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    def reset_zoom(self):
        """Show the image at one screen pixel per image pixel."""
        self._fit_to_window = False
        self.resetTransform()

    def resizeEvent(self, event):
        """Keep the whole image visible while in fit-to-window mode."""
        super().resizeEvent(event)
        if self._fit_to_window:
            self.fit_to_window()

    def wheelEvent(self, event):
        """Zoom around the cursor."""
        if not self._has_image:
            return
        self._fit_to_window = False
        factor = 1.25 if event.angleDelta().y() > 0 else 1 / 1.25
        self.scale(factor, factor)

    # -- area selection --------------------------------------------------

    def start_area_selection(self, which, message=''):
        """Ask the user to drag out an area.

        :param which: name of the area, used to label the overlay
        :type which: str
        :param message: instruction shown to the user
        :type message: str
        """
        if not self._has_image:
            self.status_message.emit("Open some images first.")
            return
        self._selecting = which
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.CrossCursor)
        self.status_message.emit(message or "Drag out the %s area." % which)

    def cancel_area_selection(self):
        """Stop asking for an area."""
        self._selecting = None
        self._rubber_band.hide()
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.unsetCursor()

    def selecting(self):
        """The area currently being asked for, or None."""
        return self._selecting

    def mousePressEvent(self, event):
        if self._selecting and event.button() == Qt.LeftButton:
            self._origin = event.position().toPoint()
            self._rubber_band.setGeometry(QRect(self._origin, self._origin))
            self._rubber_band.show()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._selecting and self._rubber_band.isVisible():
            rect = QRect(self._origin, event.position().toPoint()).normalized()
            self._rubber_band.setGeometry(rect)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._selecting and self._rubber_band.isVisible():
            self._rubber_band.hide()
            first = self.mapToScene(self._origin)
            second = self.mapToScene(event.position().toPoint())
            which = self._selecting
            self.cancel_area_selection()
            area = self._area_from_corners(first, second)
            if area is None:
                self.status_message.emit("That area was too small; try again.")
                return
            self.show_area(which, area)
            self.area_selected.emit((which,) + area)
            return
        super().mouseReleaseEvent(event)

    @staticmethod
    def _area_from_corners(first, second):
        """Turn two scene points into an (x, y, radius) area."""
        x_c = int(round((first.x() + second.x()) / 2.0))
        y_c = int(round((first.y() + second.y()) / 2.0))
        radius = int(round(max(abs(first.x() - second.x()),
                               abs(first.y() - second.y())) / 2.0))
        if radius < 2:
            return None

        return (x_c, y_c, radius)

    # -- overlays --------------------------------------------------------

    def show_area(self, which, area):
        """Draw an outline around *area*.

        :param which: ``'reference'`` or ``'search'``
        :type which: str
        :param area: (x, y, radius)
        :type area: tuple or None
        """
        self.clear_area(which)
        if area is None:
            return
        x_c, y_c, radius = area
        colour = REFERENCE_COLOUR if which == 'reference' else SEARCH_COLOUR
        item = QGraphicsRectItem(x_c - radius, y_c - radius,
                                 2 * radius + 1, 2 * radius + 1)
        pen = QPen(colour)
        pen.setCosmetic(True)          # keep the outline thin at any zoom
        pen.setWidth(2)
        item.setPen(pen)
        self._scene.addItem(item)
        self._overlays[which] = item

    def clear_area(self, which):
        """Remove the outline for *which*, if there is one."""
        item = self._overlays.pop(which, None)
        if item is not None:
            self._scene.removeItem(item)

    def clear_areas(self):
        """Remove every area outline."""
        for which in list(self._overlays):
            self.clear_area(which)
