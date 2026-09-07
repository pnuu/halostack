# -*- mode: python ; coding: utf-8 -*-

"""PyInstaller build of Halostack.

One executable provides both interfaces: it opens the window unless the
arguments call for the command line, which halostack.launcher decides.

Used by .github/workflows/windows-executable.yml to produce a standalone
Windows executable, and usable on any platform with::

    pyinstaller --clean --noconfirm packaging/halostack.spec

Most of what is below deals with imports that PyInstaller's static analysis
cannot see, and with imports it would otherwise follow too far.
"""

import importlib.util
import os

from PyInstaller.utils.hooks import collect_all, copy_metadata

# Relative paths in a spec file are resolved against the working directory the
# build was started from, which is not necessarily the repository. SPECPATH is
# injected by PyInstaller and always points at this file.
REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))

datas = []
binaries = []
hiddenimports = [
    # The window is imported lazily, so that the command line never pays for
    # Qt. Name the modules to be sure they are collected anyway.
    'halostack.gui',
    'halostack.gui.main_window',
    'halostack.gui.controls',
    'halostack.gui.preview',
    'halostack.gui.worker',
    # Matplotlib picks its backend at run time from a string, so nothing
    # imports this. Tk ships with the python.org and actions/setup-python
    # builds of Python.
    'matplotlib.backends.backend_tkagg',
    # imageio finds its plugins by scanning a registry rather than by
    # importing them. Halostack only reaches imageio for the formats Pillow
    # handles: PNG, TIFF and raw files go to dedicated backends.
    'imageio.plugins.pillow',
    'imageio.plugins.pillow_legacy',
]

# imagecodecs keeps one compiled extension module per codec and imports them
# by name at run time, so none of them is reachable from an import graph.
# rawpy ships the LibRaw shared library beside its extension module. Both have
# to be collected wholesale; nothing else does.
REQUIRED_PACKAGES = ('imagecodecs',)
OPTIONAL_PACKAGES = ('rawpy',)

for package in REQUIRED_PACKAGES + OPTIONAL_PACKAGES:
    if importlib.util.find_spec(package) is None:
        if package in REQUIRED_PACKAGES:
            raise SystemExit(
                "Cannot build: the required package %r is not installed in "
                "the build environment." % package)
        print("PyInstaller spec: optional package %r is not installed, so the "
              "executable will not read camera raw files." % package)
        continue
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

# imageio looks up its own version through importlib.metadata, which fails
# with "No package metadata was found" unless the .dist-info goes into the
# bundle. The others are cheap insurance against the same pattern.
for distribution in ('imageio', 'tifffile', 'matplotlib', 'numpy', 'scipy',
                     'pillow', 'imagecodecs'):
    try:
        datas += copy_metadata(distribution)
    except Exception as err:                 # not installed, or no metadata
        print("PyInstaller spec: no metadata for %r (%s)" % (distribution, err))

# Collecting every imageio plugin drags in bindings for PyAV, OpenCV, GDAL and
# ITK, whose shared libraries are large, frequently absent, and in some cases
# fail to load with an OSError that imageio's plugin search does not catch --
# which breaks reading an ordinary JPEG. Excluding them leaves the plugins
# named above, which are the ones Halostack uses.
# Halostack's window uses QtCore, QtGui and QtWidgets and nothing else.
# Excluding the rest of Qt roughly halves what PySide6 adds to the bundle.
UNUSED_QT_MODULES = [
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
    'PySide6.QtQuickControls2', 'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets', 'PySide6.QtSql', 'PySide6.QtTest',
    'PySide6.QtDesigner', 'PySide6.QtUiTools', 'PySide6.QtHelp',
    'PySide6.QtWebChannel', 'PySide6.QtWebSockets', 'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
    'PySide6.QtPositioning', 'PySide6.QtSensors', 'PySide6.QtSerialPort',
    'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtTextToSpeech',
    'PySide6.QtScxml', 'PySide6.QtStateMachine', 'PySide6.QtRemoteObjects',
    'PySide6.QtSpatialAudio', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'PySide6.Qt3DCore',
    'PySide6.Qt3DRender', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic',
    'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras', 'PySide6.QtNetworkAuth',
]

UNUSED_IMAGEIO_PLUGINS = [
    'imageio.plugins.ffmpeg', 'imageio.plugins.freeimage',
    'imageio.plugins.freeimagemulti', 'imageio.plugins.gdal',
    'imageio.plugins.grab', 'imageio.plugins.opencv',
    'imageio.plugins.pyav', 'imageio.plugins.simpleitk',
]

analysis = Analysis(
    # packaging/entry.py, not bin/halostack.py: see the note in that file
    # about the entry script shadowing the package it imports.
    [os.path.join(SPECPATH, 'entry.py')],
    # Put the repository itself on the search path, so that the build works
    # from a plain checkout as well as from an installed copy.
    pathex=[REPO_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=UNUSED_IMAGEIO_PLUGINS + UNUSED_QT_MODULES + [
        # Backends for those plugins, in case they are installed alongside.
        'av', 'cv2', 'osgeo', 'SimpleITK',
        # Nothing here is imported by Halostack; excluding them keeps the
        # executable to a size that is reasonable to download.
        'pytest', 'sphinx', 'IPython', 'jupyter', 'notebook', 'pandas',
        # PySide6 itself is NOT excluded: the window needs it. The other
        # bindings are, so that having one installed cannot pull a second
        # copy of Qt into the bundle.
        'PyQt5', 'PyQt6', 'PySide2',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_webagg',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name='halostack',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Console, because the same executable is the command line interface.
    # On Windows this means the window opens with a console behind it; a
    # windowed build would have no usable command line at all.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
