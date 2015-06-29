#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Halostack GUI"""

import sys
from PyQt4 import QtGui, QtCore
from halostack import __version__
#, Image, Align, Stack
from collections import deque
import os.path

class HalostackGui(QtGui.QWidget):
    '''Halostack main window.
    '''

    def __init__(self):
        super(HalostackGui, self).__init__()

        self.setWindowTitle('Halostack ' + __version__)
        self._screen = QtGui.QDesktopWidget().screenGeometry()
        # self.image_area = QtGui.QScrollArea()
        # self.image_area.setWidgetResizable(True)
        self.image = QtGui.QLabel()
        self.image.setAlignment(QtCore.Qt.AlignCenter)
        self.ref_button = None
        self.search_button = None
        self.ref_info = None
        self.search_info = None
        self.image_scale = 1.
        self.ref_points = deque([], 2)
        self.search_points = deque([], 2)
        self.fnames = []
        self.filelist = None
        self.log_window = None
        # self.image.setScaledContents(True)
        self.init_ui()

    def init_ui(self):
        '''Initialize GUI window.
        '''

        # Image area
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        img_box = QtGui.QVBoxLayout()
        img_box.addStretch(0)
        img_box.addWidget(self.image)
        img_box.addStretch(0)
        hbox.addLayout(img_box)
        hbox.addStretch(1)

        # Buttons
        vbox = QtGui.QVBoxLayout()
        # Load images
        open_images_button = QtGui.QPushButton("Open images...")
        open_images_button.clicked.connect(self.open_images)
        open_images_button.setShortcut('Ctrl+O')
        vbox.addWidget(open_images_button)
        # Radio buttons for deciding where pixel locations are stored
        pix_locations = QtGui.QButtonGroup()
        # Focus reference
        self.ref_button = QtGui.QRadioButton("Focus reference")
        pix_locations.addButton(self.ref_button)
        vbox.addWidget(self.ref_button)
        # Reference info
        self.ref_info = QtGui.QLabel()
        self.ref_info.setText("No reference area selected.")
        self.ref_info.setFixedWidth(200)
        vbox.addWidget(self.ref_info)
        # Search area
        self.search_button = QtGui.QRadioButton("Search area")
        pix_locations.addButton(self.search_button)
        # Set search area
        vbox.addWidget(self.search_button)
        # Search area information
        self.search_info = QtGui.QLabel()
        self.search_info.setText("No search area selected.")
        self.search_info.setFixedWidth(200)
        vbox.addWidget(self.search_info)
        # Stacking menu
        stack_button = QtGui.QPushButton("Align and stack...")
        stack_button.setShortcut('Ctrl+A')
        vbox.addWidget(stack_button)
        # List of image tags
        tag_list = QtGui.QComboBox(self)
        tag_list.addItem("<tags>")
        vbox.addWidget(tag_list)
        # Process menu
        process_button = QtGui.QPushButton("Process...")
        process_button.setShortcut('Ctrl+P')
        vbox.addWidget(process_button)
        # Save image menu
        save_button = QtGui.QPushButton("Save...")
        save_button.setShortcut('Ctrl+S')
        vbox.addWidget(save_button)
        # List of selected images
        file_list_label = QtGui.QLabel()
        file_list_label.setText("List of selected files")
        file_list_label.setFixedWidth(200)
        vbox.addWidget(file_list_label)
        self.filelist = QtGui.QTextEdit()
        self.filelist.setReadOnly(True)
        self.filelist.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        font = self.filelist.font()
        font.setFamily("Courier")
        font.setPointSize(10)
        vbox.addWidget(self.filelist)
        # Log window
        log_window_label = QtGui.QLabel()
        log_window_label.setText("Log")
        log_window_label.setFixedWidth(200)
        vbox.addWidget(log_window_label)
        self.log_window = QtGui.QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        # self.log_window.setFixedHeight(100)
        # self.log_window.setBaseSize(200, 100)
        self.log_window.setMaximumHeight(200)
        font = self.log_window.font()
        font.setFamily("Courier")
        font.setPointSize(10)
        vbox.addWidget(self.log_window)
        # vbox.addStretch(1)
        # Quit Halostack
        quit_button = QtGui.QPushButton("Quit")
        quit_button.clicked.connect(QtCore.QCoreApplication.instance().quit)
        quit_button.setShortcut('Ctrl+Q')
        vbox.addWidget(quit_button)
        vbox.setAlignment(QtCore.Qt.AlignRight)

        hbox.addLayout(vbox)
        self.setLayout(hbox)

        # self.set_image(fname='/tmp/_DSC4158.thumb.jpg') #pic.jpg')
        self.set_image(fname='/tmp/pic.jpg')
        self.image.mousePressEvent = self.get_position

    def get_position(self, event):
        '''Get pixel location
        '''
        x_loc = event.x()/self.image_scale
        y_loc = event.y()/self.image_scale
        if self.ref_button.isChecked():
            self.ref_points.append((int(x_loc), int(y_loc)))
            pt_str = ', '.join([str(self.ref_points[i]) for i in
                                range(len(self.ref_points))])
            self.ref_info.setText(pt_str)
        elif self.search_button.isChecked():
            self.search_points.append((int(x_loc), int(y_loc)))
            pt_str = ', '.join([str(self.search_points[i]) for i in
                                range(len(self.search_points))])
            self.search_info.setText(pt_str)

    def set_image(self, img=None, fname=None):
        '''Insert image in the window.
        '''
        if img is not None:
            pass
        elif fname is not None:
            img = QtGui.QPixmap(fname)

        # Original size of the input image
        orig_height, orig_width = img.height(), img.width()
        # Find maximum dimensions
        width = min(orig_width, self._screen.width()-200)
        height = min(orig_height, self._screen.height()-80)
        # Resize the image area
        self.image.resize(width, height)
        # Scale image for viewing
        img = img.scaled(QtCore.QSize(width, height),
                         QtCore.Qt.KeepAspectRatio,
                         QtCore.Qt.SmoothTransformation)
        # Calculate image scale
        self.image_scale = min(float(img.height())/orig_height,
                               float(img.width())/orig_width)
        # Show image
        self.image.setPixmap(img)
        # self.image_area.setWidget(self.image)

    def open_images(self):
        '''Open (select) images for stacking.'''
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Select files', '')
        self.fnames = [str(x) for x in fnames]
        base_names = [os.path.basename(x) for x in self.fnames]
        self.filelist.setText('\n'.join(base_names))


def main():
    '''Main function.
    '''
    app = QtGui.QApplication(sys.argv)
    gui = HalostackGui()
    gui.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
