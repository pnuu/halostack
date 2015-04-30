#!/usr/bin/env python
 # -*- coding: utf8 -*-
 
from halostack.image import Image, to_numpy
from PythonMagick import Image as PMImage
from PythonMagick import Blob
import numpy as np
import sys
import os
import PyQt5.QtCore as core
import PyQt5.QtGui as gui
import PyQt5.QtWidgets as widgets

def outputName(fname, op):
  head, tail = os.path.split(str(fname))
  tail = tail.split('.')[:-1]
  tail.append('png')
  tail = ('_' + op + '.').join(tail)
  return os.path.join(head, tail)

class EnhanceWorker(core.QThread):
  fileName = None
  outName = None
  enhancement = None

  imageResult = core.pyqtSignal(Image)

  def __init__(self, parent=None, fname=None, outname=None, ench=None):
    super(EnhanceWorker, self).__init__(parent)
    self.fileName = fname
    self.outName = outname
    self.enhancement = ench

  def run(self):
    if not self.fileName:
      return
    if not self.outName:
      return
    if not self.enhancement:
      return

    # read image
    img = Image(fname=str(self.fileName))
    # enhance
    img.enhance(self.enhancement)
    self.imageResult.emit(img)

class ImageWidget(widgets.QWidget):
  image = None
  img = None
  data = None

  def __init__(self, parent=None):
    widgets.QWidget.__init__(self, parent)

  def updateFromHSImage(self, image):
    self.image = image
    if image.img is None:
      return

    img = to_numpy(image.img)

    if img.dtype == np.uint8:
      self.data = img.data
      self.img = gui.QImage(self.data, img.shape[1], img.shape[0], img.strides[0], gui.QImage.Format_RGB888)
      self.update()
      return

    # mmm, need to figure out if this scaling affects image quality
    if len(img.shape) == 3:
      arr = ((img - img.min()) / (img.ptp() / 255.0)).astype(np.uint8)
    else:
      arr = ((img - img.min()) / (img.ptp() / 255.0)).astype(np.uint8).repeat(3, axis=1).reshape(img.shape[0], img.shape[1], 3)

    self.data = arr.data
    self.img = gui.QImage(self.data, arr.shape[1], arr.shape[0], arr.strides[0], gui.QImage.Format_RGB888)
    self.update()
    
  def updateFromFile(self, filename):
    self.img = gui.QImage(filename)
    self.update()

  def paintEvent(self, event):
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
    if self.image is None:
      return

    self.image.save(str(filename))

class EnhanceWidget(widgets.QWidget):
  buttons = None
  image = None
  fileName = None
  outName = None
  opName = None
  enhancement = None

  def __init__(self, parent=None, operation="unknown"):
    widgets.QWidget.__init__(self, parent)

    self.opName = operation

    box = widgets.QVBoxLayout(self)
    self.buttons = widgets.QHBoxLayout()
    box.addLayout(self.buttons)
    self.image = ImageWidget()
    box.addWidget(self.image)

  def updateImage(self, image=None):
    if image is not None:
      self.image.updateFromHSImage(image)
    elif self.outName:
      self.image.updateFromFile(self.outName)

  def setEnhancement(self, enhancement):
    self.enhancement = enhancement

  def enhance(self, filename=None):
    if filename:
      self.fileName = filename
      self.outName = outputName(filename, self.opName)
    
    if self.enhancement is None:
      return

    worker = EnhanceWorker(self, self.fileName, self.outName, self.enhancement)
    worker.imageResult.connect(self.updateImage)
    worker.start(core.QThread.LowPriority)

  def saveImage(self, filename):
    self.image.save(filename)


class USMWidget(EnhanceWidget):
  radius = 40.0
  sigma = 20.0
  gain = 2.5
  rspin = None
  sspin = None
  gspin = None
  
  def __init__(self, parent=None):
    EnhanceWidget.__init__(self, parent, "usm")
    l = widgets.QLabel("Säde")
    self.buttons.addWidget(l)
    self.rspin = widgets.QDoubleSpinBox()
    self.rspin.setMinimum(0.0)
    self.rspin.setMaximum(1000.0)
    self.rspin.setSingleStep(10)
    self.rspin.setValue(self.radius)
    self.rspin.valueChanged.connect(self.updateRadius)
    self.buttons.addWidget(self.rspin)
    l = widgets.QLabel("Sigma")
    self.buttons.addWidget(l)
    self.sspin = widgets.QDoubleSpinBox()
    self.sspin.setMinimum(0.0)
    self.sspin.setMaximum(1000.0)
    self.sspin.setSingleStep(1)
    self.sspin.setValue(self.sigma)
    self.sspin.valueChanged.connect(self.updateSigma)
    self.buttons.addWidget(self.sspin)
    l = widgets.QLabel("Voimakkuus")
    self.buttons.addWidget(l)
    self.gspin = widgets.QDoubleSpinBox()
    self.gspin.setMinimum(0.0)
    self.gspin.setMaximum(100.0)
    self.gspin.setSingleStep(0.1)
    self.gspin.setValue(self.gain)
    self.gspin.valueChanged.connect(self.updateGain)
    self.buttons.addWidget(self.gspin)
    self.buttons.addStretch(1)
    b = widgets.QPushButton("Toteuta")
    b.clicked.connect(self.enhance)
    self.buttons.addWidget(b)
    self.updateEnhancement()

  def updateEnhancement(self):
    self.setEnhancement({'usm': [self.radius, self.sigma, self.gain]})

  def updateRadius(self, value):
    self.radius = value
    self.updateEnhancement()
    
  def updateSigma(self, value):
    self.sigma = value
    self.updateEnhancement()

  def updateGain(self, value):
    self.gain = value
    self.updateEnhancement()


class BRWidget(EnhanceWidget):
  op = "br"
  multiplier = None
  spin = None
  
  def __init__(self, parent=None):
    EnhanceWidget.__init__(self, parent, "br")

    b = widgets.QCheckBox("Red - Green")
    b.setCheckState(0)
    b.stateChanged.connect(self.updateOperation)
    self.buttons.addWidget(b)
    b = widgets.QCheckBox("Automaattinen kerroin")
    b.setCheckState(2)
    b.stateChanged.connect(self.updateAutomultiplier)
    self.buttons.addWidget(b)
    self.spin = widgets.QDoubleSpinBox()
    self.spin.setMinimum(0.0)
    self.spin.setMaximum(10.0)
    self.spin.setSingleStep(0.1)
    self.spin.setValue(1.0)
    self.spin.valueChanged.connect(self.updateMultiplier)
    self.spin.setEnabled(False)
    self.buttons.addWidget(self.spin)
    b = widgets.QPushButton("Toteuta")
    b.clicked.connect(self.enhance)
    self.buttons.addWidget(b)
    self.updateEnhancement()

  def updateEnhancement(self):
    self.setEnhancement({'gradient': None, self.op: self.multiplier})

  def updateOperation(self, state):
    if state == 0:
      self.op = 'br'
    else:
      self.op = 'rg'

    self.updateEnhancement()
    self.enhance()

  def updateAutomultiplier(self, state):
    if state == 0:
      self.multiplier = self.spin.value()
      self.spin.setEnabled(True)
    else:
      self.multiplier = None
      self.spin.setEnabled(False)
    self.updateEnhancement()
      
  def updateMultiplier(self, mul):
    self.multiplier = mul
    self.updateEnhancement()


class HaloWindow(widgets.QWidget):
  fileName = None
  origImage = None
  usmWidget = None
  usmWorker = None
  brImage = None
  brBox = None
  brWorker = None
  combo = None
  saveButton = None
  vahtiButton = None

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
    b = widgets.QPushButton("Avaa...")
    b.clicked.connect(self.runDialog)
    buttons.addWidget(b)
    self.saveButton = widgets.QPushButton("Tallenna...")
    self.saveButton.setEnabled(False)
    self.saveButton.clicked.connect(self.save)
    buttons.addWidget(self.saveButton)
    b = widgets.QPushButton("Lopeta")
    b.clicked.connect(sys.exit)
    buttons.addWidget(b)
    buttons.addWidget(widgets.QLabel("Käsittely:"))
    self.combo = widgets.QComboBox()
    self.combo.addItem("Valitse...")
    self.combo.addItem("Unsharp Mask")
    self.combo.addItem("Blue - Red")
    self.combo.currentIndexChanged.connect(self.doEnhancement)
    buttons.addWidget(self.combo)

    self.origImage = widgets.QLabel(self)
    htop.addSpacing(16)
    htop.addWidget(self.origImage)

    self.stack = widgets.QStackedWidget()
    self.stack.setMinimumSize(600, 400);
    hbot.addWidget(self.stack)

    self.usmWidget = USMWidget()
    self.stack.addWidget(self.usmWidget)
    self.usmWidget.hide()

    self.brWidget = BRWidget()
    self.stack.addWidget(self.brWidget)
    self.brWidget.hide()


  def setFile(self, filename):
    self.fileName = filename
    # HACK
    lowName = self.fileName.lower()
    if lowName.endswith(".cr2") or lowName.endswith(".dng"):
      pngName = self.fileName[:-3] + "png"
      os.system("dcraw -q 1 -M -c " + self.fileName + " | convert - -resize 1000x-1 " + pngName);
      self.fileName = pngName
    self.setWindowTitle(self.fileName)
    self.origImage.setPixmap(gui.QPixmap(self.fileName).scaledToHeight(128))
    self.combo.setCurrentIndex(0)
    self.stack.currentWidget().hide()

  def runDialog(self, path=None):
    dialog = widgets.QFileDialog()
    if path:
      if os.path.isfile(path):
        self.setFile(path)
        self.show()
        return
      elif os.path.isdir(path):
        dialog.setDirectory(path)

    dialog.exec_()

    if dialog.result() == 0 and not self.isVisible():
      sys.exit(1)

    if len(dialog.selectedFiles()) > 0:
      self.setFile(dialog.selectedFiles()[0])
    self.show()

  def doEnhancement(self, index):
    if index == 0:
      self.saveButton.setEnabled(False)
      return

    self.stack.setCurrentIndex(index-1)
    self.stack.currentWidget().enhance(self.fileName)
    self.stack.currentWidget().show()
    self.saveButton.setEnabled(True)

  def save(self):
    dialog = widgets.QFileDialog()
    dialog.setAcceptMode(1)
    dialog.selectFile(self.stack.currentWidget().outName)

    dialog.exec_()

    if dialog.result() == 0:
      return

    if len(dialog.selectedFiles()) < 1:
      return

    self.stack.currentWidget().saveImage(dialog.selectedFiles()[0])


if __name__ == "__main__":
    app = widgets.QApplication(sys.argv)
    w = HaloWindow()
    if len(sys.argv) > 1:
      w.runDialog(sys.argv[1])
    else:
      w.runDialog()
    sys.exit(app.exec_())

