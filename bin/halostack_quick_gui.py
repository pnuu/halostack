#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Quick tool to apply B-R, G-R and USM processing to halo images.
'''

from halostack.image import Image, to_numpy
import numpy as np
import sys
import os
import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

def output_name(fname, oper):
    '''Form the output filename.
    '''
    head, tail = os.path.split(str(fname))
    tail = tail.split('.')[:-1]
    tail.append('png')
    tail = ('_' + oper + '.').join(tail)
    return os.path.join(head, tail)

class EnhanceWorker(core.QThread):
    '''EhanceWorker.
    '''

    filename = None
    outname = None
    enhancement = None

    result_image = core.pyqtSignal(Image)

    def __init__(self, parent=None, fname=None, outname=None, ench=None):
        super(EnhanceWorker, self).__init__(parent)

        self.filename = fname
        self.outname = outname
        self.enhancement = ench

    def run(self):
        '''Run enhancements.
        '''
        if not self.filename:
            return
        if not self.outname:
            return
        if not self.enhancement:
            return

        # read image
        img = Image(fname=str(self.filename))
        # enhance
        img.enhance(self.enhancement)
        self.result_image.emit(img)

class ImageWidget(widgets.QWidget):
    '''ImageWidget.
    '''
    image = None
    img = None
    data = None

    def __init__(self, parent=None):
        widgets.QWidget.__init__(self, parent)

    def update_from_hs_image(self, image):
        '''Update from hs image.
        '''
        self.image = image
        if image.img is None:
            return

        img = to_numpy(image.img)

        if img.dtype == np.uint8:
            self.data = img.data
            self.img = gui.QImage(self.data, img.shape[1], img.shape[0],
                                  img.strides[0], gui.QImage.Format_RGB888)
            self.update()
            return

        # mmm, need to figure out if this scaling affects image quality
        if len(img.shape) == 3:
            arr = ((img - img.min()) / (img.ptp() / 255.0)).astype(np.uint8)
        else:
            arr = ((img - img.min()) / (img.ptp() / 255.0)).\
                astype(np.uint8).repeat(3, axis=1).reshape(img.shape[0],
                                                           img.shape[1], 3)

        self.data = arr.data
        self.img = gui.QImage(self.data, arr.shape[1], arr.shape[0],
                              arr.strides[0], gui.QImage.Format_RGB888)
        self.update()

    def update_from_file(self, filename):
        '''Update image from file.
        '''
        self.img = gui.QImage(filename)
        self.update()

    def paintEvent(self, event):
        '''Paint event.
        '''
        painter = gui.QPainter(self)

        if self.img is None:
            painter.eraseRect(event.rect())
            return

        geo = self.geometry()
        waspect = float(geo.width()) / float(geo.height())
        aspect = float(self.img.width()) / float(self.img.height())

        if waspect > aspect:
            geo.setWidth(geo.height()*aspect)
        else:
            geo.setHeight(geo.width()/aspect)

        painter.drawImage(geo, self.img)

    def save(self, filename):
        '''Save image.
        '''
        if self.image is None:
            return

        self.image.save(str(filename))

class EnhanceWidget(widgets.QWidget):
    '''EnhanceWidget.
    '''
    buttons = None
    image = None
    fileName = None
    outname = None
    oper_name = None
    enhancement = None

    def __init__(self, parent=None, operation="unknown"):
        widgets.QWidget.__init__(self, parent)
        self.oper_name = operation

        box = widgets.QVBoxLayout(self)
        self.buttons = widgets.QHBoxLayout()
        box.addLayout(self.buttons)
        self.image = ImageWidget()
        box.addWidget(self.image)

    def update_image(self, image=None):
        '''Update image.
        '''
        if image is not None:
            self.image.update_from_hs_image(image)
        elif self.outname:
            self.image.update_from_file(self.outname)

    def set_enhancement(self, enhancement):
        '''Set enhancement.
        '''
        self.enhancement = enhancement

    def enhance(self, filename=None):
        '''Enhance image.
        '''
        if filename:
            self.filename = filename
            self.outname = output_name(filename, self.oper_name)

        if self.enhancement is None:
            return

        worker = EnhanceWorker(self, self.filename, self.outname,
                               self.enhancement)
        worker.result_image.connect(self.update_image)
        worker.start(core.QThread.LowPriority)

    def save_image(self, filename):
        '''Save image.
        '''
        self.image.save(filename)


class USMWidget(EnhanceWidget):
    '''USMWidget.
    '''

    radius = 40.0
    sigma = 20.0
    gain = 2.5
    rspin = None
    sspin = None
    gspin = None

    def __init__(self, parent=None):
        EnhanceWidget.__init__(self, parent, "usm")

        lbl = widgets.QLabel("Radius")
        self.buttons.addWidget(lbl)
        self.rspin = widgets.QDoubleSpinBox()
        self.rspin.setMinimum(0.0)
        self.rspin.setMaximum(1000.0)
        self.rspin.setSingleStep(10)
        self.rspin.setValue(self.radius)
        self.rspin.valueChanged.connect(self.update_radius)
        self.buttons.addWidget(self.rspin)
        lbl = widgets.QLabel("Sigma")
        self.buttons.addWidget(lbl)
        self.sspin = widgets.QDoubleSpinBox()
        self.sspin.setMinimum(0.0)
        self.sspin.setMaximum(1000.0)
        self.sspin.setSingleStep(1)
        self.sspin.setValue(self.sigma)
        self.sspin.valueChanged.connect(self.update_sigma)
        self.buttons.addWidget(self.sspin)
        lbl = widgets.QLabel("Amount")
        self.buttons.addWidget(lbl)
        self.gspin = widgets.QDoubleSpinBox()
        self.gspin.setMinimum(0.0)
        self.gspin.setMaximum(100.0)
        self.gspin.setSingleStep(0.1)
        self.gspin.setValue(self.gain)
        self.gspin.valueChanged.connect(self.update_gain)
        self.buttons.addWidget(self.gspin)
        self.buttons.addStretch(1)
        btn = widgets.QPushButton("Apply")
        btn.clicked.connect(self.enhance)
        self.buttons.addWidget(btn)
        self.update_enhancement()

    def update_enhancement(self):
        '''Update enhancements.
        '''
        self.set_enhancement({'usm': [self.radius, self.sigma, self.gain]})

    def update_radius(self, value):
        '''Update USM radius.
        '''
        self.radius = value
        self.update_enhancement()

    def update_sigma(self, value):
        '''Update USM sigma (standard deviation of the Gaussian).
        '''
        self.sigma = value
        self.update_enhancement()

    def update_gain(self, value):
        '''Update USM gain (or amount).
        '''
        self.gain = value
        self.update_enhancement()


class BRWidget(EnhanceWidget):
    '''BRWidget
    '''

    oper = "br"
    multiplier = None
    spin = None

    def __init__(self, parent=None):
        EnhanceWidget.__init__(self, parent, "br")

        btn = widgets.QCheckBox("Red - Green")
        btn.setCheckState(0)
        btn.stateChanged.connect(self.update_operation)
        self.buttons.addWidget(btn)
        btn = widgets.QCheckBox("Automatic multiplier")
        btn.setCheckState(2)
        btn.stateChanged.connect(self.update_automultiplier)
        self.buttons.addWidget(btn)
        self.spin = widgets.QDoubleSpinBox()
        self.spin.setMinimum(0.0)
        self.spin.setMaximum(10.0)
        self.spin.setSingleStep(0.1)
        self.spin.setValue(1.0)
        self.spin.valueChanged.connect(self.update_multiplier)
        self.spin.setEnabled(False)
        self.buttons.addWidget(self.spin)
        btn = widgets.QPushButton("Apply")
        btn.clicked.connect(self.enhance)
        self.buttons.addWidget(btn)
        self.update_enhancement()

    def update_enhancement(self):
        '''Update enhancement.
        '''
        self.set_enhancement({'gradient': None, self.oper: self.multiplier})

    def update_operation(self, state):
        '''Update operation (switch between rg and br).
        '''
        if state == 0:
            self.oper = 'br'
        else:
            self.oper = 'gr'

        self.update_enhancement()
        self.enhance()

    def update_automultiplier(self, state):
        '''Update automatick multiplier.
        '''
        if state == 0:
            self.multiplier = self.spin.value()
            self.spin.setEnabled(True)
        else:
            self.multiplier = None
            self.spin.setEnabled(False)
        self.update_enhancement()

    def update_multiplier(self, mul):
        '''Update user-set multiplier.
        '''
        self.multiplier = mul
        self.update_enhancement()


class HaloWindow(widgets.QWidget):
    '''HaloWindow Widget.
    '''
    filename = None
    orig_image = None
    usm_widget = None
    usm_worker = None
    br_image = None
    br_box = None
    br_worker = None
    combo = None
    save_button = None
    vahti_button = None

    def __init__(self, parent=None):
        widgets.QWidget.__init__(self, parent)

        vsplit = widgets.QVBoxLayout(self)
        htop = widgets.QHBoxLayout()
        hbot = widgets.QHBoxLayout()
        vsplit.addLayout(htop)
        vsplit.addSpacing(16)
        vsplit.addLayout(hbot)

        buttons = widgets.QGridLayout()
        htop.addLayout(buttons)
        btn = widgets.QPushButton("Open..")
        btn.clicked.connect(self.run_dialog)
        buttons.addWidget(btn)
        self.save_button = widgets.QPushButton("Save...")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save)
        buttons.addWidget(self.save_button)
        btn = widgets.QPushButton("Exit")
        btn.clicked.connect(sys.exit)
        buttons.addWidget(btn)
        buttons.addWidget(widgets.QLabel("Enhancements:"))
        self.combo = widgets.QComboBox()
        self.combo.addItem("Select...")
        self.combo.addItem("Unsharp Mask")
        self.combo.addItem("Blue - Red")
        self.combo.currentIndexChanged.connect(self.do_enhancement)
        buttons.addWidget(self.combo)

        self.orig_image = widgets.QLabel(self)
        htop.addSpacing(16)
        htop.addWidget(self.orig_image)

        self.stack = widgets.QStackedWidget()
        self.stack.setMinimumSize(600, 400)
        hbot.addWidget(self.stack)

        self.usm_widget = USMWidget()
        self.stack.addWidget(self.usm_widget)
        self.usm_widget.hide()

        self.br_widget = BRWidget()
        self.stack.addWidget(self.br_widget)
        self.br_widget.hide()


    def set_file(self, filename):
        '''Set file.
        '''
        self.filename = filename
        # HACK
        low_name = self.filename.lower()
        if low_name.endswith(".cr2") or low_name.endswith(".dng"):
            png_name = self.filename[:-3] + "png"
            os.system("dcraw -q 1 -M -c " + self.filename + \
                          " | convert - -resize 1000x-1 " + png_name)
            self.filename = png_name
        self.setWindowTitle(self.filename)
        self.orig_image.setPixmap(gui.QPixmap(self.filename).\
                                      scaledToHeight(128))
        self.combo.setCurrentIndex(0)
        self.stack.currentWidget().hide()

    def run_dialog(self, path=None):
        '''Run dialog.
        '''
        dialog = widgets.QFileDialog()

        if path:
            if os.path.isfile(path):
                self.set_file(path)
                self.show()
                return
            elif os.path.isdir(path):
                dialog.setDirectory(path)

        dialog.exec_()

        if dialog.result() == 0 and not self.isVisible():
            sys.exit(1)

        if len(dialog.selectedFiles()) > 0:
            self.set_file(dialog.selectedFiles()[0])

        self.show()

    def do_enhancement(self, index):
        '''Apply the enhancement.
        '''
        if index == 0:
            self.save_button.setEnabled(False)
            return

        self.stack.setCurrentIndex(index-1)
        self.stack.currentWidget().enhance(self.filename)
        self.stack.currentWidget().show()
        self.save_button.setEnabled(True)

    def save(self):
        '''Save image.
        '''
        dialog = widgets.QFileDialog()
        dialog.setAcceptMode(1)
        dialog.selectFile(self.stack.currentWidget().outName)

        dialog.exec_()

        if dialog.result() == 0:
            return

        if len(dialog.selectedFiles()) < 1:
            return

        self.stack.currentWidget().save_image(dialog.selectedFiles()[0])

def main():
    '''Main function.
    '''
    app = widgets.QApplication(sys.argv)
    win = HaloWindow()
    if len(sys.argv) > 1:
        win.run_dialog(sys.argv[1])
    else:
        win.run_dialog()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
