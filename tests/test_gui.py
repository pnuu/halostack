"""Tests for the graphical interface.

These run headlessly through Qt's offscreen platform, so they need no
display; they are skipped when PySide6 is not installed.
"""

import os
import sys

import numpy as np
import pytest

# Has to be set before the first QApplication is created.
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

# Not pytest.importorskip: that only skips on ModuleNotFoundError, and a
# PySide6 whose Qt libraries are missing raises a plain ImportError naming the
# library. Both mean the same thing here -- there is no usable Qt -- and
# neither should turn into a collection error.
try:
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QApplication

    from halostack.gui.controls import ControlPanel
    from halostack.gui.main_window import MainWindow
    from halostack.gui.preview import PreviewView, to_qimage
except ImportError as err:                                  # pragma: no cover
    pytest.skip("no usable PySide6: %s" % err, allow_module_level=True)


@pytest.fixture(scope='session')
def qt_app():
    """One QApplication for the whole session; Qt allows only one."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qt_app, frame_files):
    """A window with the test frames loaded and the areas already picked."""
    fnames, _ = frame_files
    win = MainWindow()
    win.controls.files.add_files(fnames)
    win._area_selected(('reference', 40, 30, 8))
    win._area_selected(('search', 40, 30, 20))

    return win


def run_and_wait(window, timeout=30000):
    """Start a run and return when the worker thread has finished."""
    window.run()
    if window._worker is None:
        return
    loop = QEventLoop()
    window._worker.finished.connect(loop.quit)
    QTimer.singleShot(timeout, loop.quit)
    loop.exec()
    QApplication.processEvents()


# -- preview -------------------------------------------------------------

def test_colour_and_greyscale_both_convert(frame):
    """The preview has to cope with 2-D data, which br and friends produce."""
    assert to_qimage(frame).width() == frame.shape[1]
    assert to_qimage(frame[:, :, 0]).width() == frame.shape[1]


def test_preview_shows_and_clears(qt_app, frame):
    """An image can be put in and taken out again."""
    view = PreviewView()
    assert not view.has_image()

    view.set_image(frame)
    assert view.has_image()

    view.clear_image()
    assert not view.has_image()


def test_area_overlays_can_be_replaced(qt_app, frame):
    """Picking an area again must not leave the old outline behind."""
    view = PreviewView()
    view.set_image(frame)
    view.show_area('reference', (10, 10, 5))
    view.show_area('reference', (20, 20, 6))

    assert len(view._overlays) == 1


# -- controls ------------------------------------------------------------

def test_every_command_line_option_has_a_control(qt_app):
    """The GUI is meant to expose the whole command line."""
    settings = ControlPanel().settings()

    for key in ('fname_in', 'avg_stack_file', 'min_stack_file',
                'max_stack_file', 'median_stack_file', 'sigma_stack_file',
                'kappa_sigma_params', 'correlation_threshold', 'save_prefix',
                'no_alignment', 'enhance_images', 'enhance_stacks',
                'view_gamma', 'nprocs'):
        assert key in settings, key


def test_settings_survive_a_round_trip(qt_app):
    """What the panel reports must be what it can be given back."""
    panel = ControlPanel()
    wanted = {'fname_in': ['a.jpg', 'b.jpg'], 'correlation_threshold': 0.85,
              'view_gamma': 0.45, 'nprocs': 4, 'save_prefix': 'al',
              'enhance_images': ['gradient'], 'enhance_stacks': ['usm:25,2'],
              'kappa_sigma_params': '2.5,4', 'avg_stack_file': 'out.png'}
    panel.set_settings(wanted)
    got = panel.settings()

    for key, value in wanted.items():
        assert got[key] == value, key


def test_enhancement_dialog_lists_the_registry(qt_app):
    """The controls are built from ENHANCEMENTS, not from a hard-coded list."""
    from halostack.enhancements import ENHANCEMENTS
    from halostack.gui.controls import EnhancementDialog

    dialog = EnhancementDialog()
    listed = {dialog._combo.itemText(i) for i in range(dialog._combo.count())}

    assert listed == set(ENHANCEMENTS)


def test_enhancement_dialog_builds_the_command_line_form(qt_app):
    """A method and its arguments come out in the -e/-E syntax."""
    from halostack.gui.controls import EnhancementDialog

    dialog = EnhancementDialog(initial='usm:25,2')
    assert dialog.value() == 'usm:25,2'

    dialog = EnhancementDialog(initial='gradient')
    assert dialog.value() == 'gradient'


# -- the window ----------------------------------------------------------

def test_window_has_a_split_view(window):
    """The image and the controls sit either side of a splitter."""
    from PySide6.QtWidgets import QSplitter

    splitter = window.centralWidget()
    assert isinstance(splitter, QSplitter)
    assert splitter.count() == 2


def test_selecting_images_shows_the_reference(window):
    """With images loaded, the preview shows the one alignment refers to."""
    assert window.preview.has_image()
    assert window.controls.files.reference() is not None


def test_nothing_runs_until_run_is_pressed(window):
    """Changing settings must not start any processing."""
    window.controls.threshold.setValue(0.9)
    window.controls.enhance_stacks.set_values(['stretch'])

    assert not window.running()
    assert window._result is None


def test_run_produces_a_result(window, tmp_path):
    """The whole pipeline, driven from the window."""
    window.controls._stack_fields['mean'].setText(str(tmp_path / 'avg.png'))
    run_and_wait(window)

    assert window._result is not None
    assert (tmp_path / 'avg.png').exists()
    assert '6/6' in window.statusBar().currentMessage() or \
           '3/3' in window.statusBar().currentMessage()


def test_controls_are_disabled_while_running(window, tmp_path):
    """One operation at a time: Run is unavailable until it finishes."""
    window.controls._stack_fields['mean'].setText(str(tmp_path / 'avg.png'))
    window.run()
    try:
        assert window.running()
        assert not window.run_button.isEnabled()
        assert window.cancel_button.isEnabled()
        assert not window.controls.isEnabled()
    finally:
        loop = QEventLoop()
        window._worker.finished.connect(loop.quit)
        QTimer.singleShot(30000, loop.quit)
        loop.exec()
        QApplication.processEvents()

    assert window.run_button.isEnabled()
    assert not window.cancel_button.isEnabled()


def test_cancelling_leaves_no_result(window, tmp_path):
    """A cancelled run must not push anything onto the undo stack."""
    window.controls._stack_fields['mean'].setText(str(tmp_path / 'avg.png'))
    window.run()
    window.cancel()
    loop = QEventLoop()
    window._worker.finished.connect(loop.quit)
    QTimer.singleShot(30000, loop.quit)
    loop.exec()
    QApplication.processEvents()

    assert window._result is None
    assert not window.undo_action.isEnabled()
    assert window.run_button.isEnabled()
    assert 'ancel' in window.statusBar().currentMessage()


def test_undo_and_redo_step_through_results(window, tmp_path):
    """Undo takes back a run; redo puts it back."""
    window.controls._stack_fields['mean'].setText(str(tmp_path / 'avg.png'))
    run_and_wait(window)
    assert window._result is not None
    assert window.undo_action.isEnabled()

    window.undo_action.trigger()
    QApplication.processEvents()
    assert window._result is None
    assert window.redo_action.isEnabled()

    window.redo_action.trigger()
    QApplication.processEvents()
    assert window._result is not None


def test_running_without_images_is_refused(qt_app, monkeypatch):
    """An empty file list explains itself instead of raising."""
    from PySide6.QtWidgets import QMessageBox

    said = []
    monkeypatch.setattr(QMessageBox, 'information',
                        lambda *args, **kwargs: said.append(args[-1]))
    win = MainWindow()
    win.run()

    assert said and 'images' in said[0]
    assert not win.running()


def test_running_aligned_without_areas_is_refused(qt_app, frame_files, monkeypatch):
    """Alignment needs the two areas, and says so rather than failing later."""
    from PySide6.QtWidgets import QMessageBox

    said = []
    monkeypatch.setattr(QMessageBox, 'information',
                        lambda *args, **kwargs: said.append(args[-1]))
    fnames, _ = frame_files
    win = MainWindow()
    win.controls.files.add_files(fnames)
    win.run()

    assert said and 'area' in said[0]


def test_settings_can_seed_the_window(qt_app):
    """--gui with options opens the window already filled in."""
    win = MainWindow(settings={'correlation_threshold': 0.9, 'nprocs': 3})

    assert win.controls.settings()['correlation_threshold'] == pytest.approx(0.9)
    assert win.controls.settings()['nprocs'] == 3


# -- the libxcb-cursor pre-flight check -----------------------------------

def test_missing_xcb_cursor_is_detected(monkeypatch):
    """Qt 6.5 needs libxcb-cursor, and aborts from C++ when it is absent."""
    from halostack import gui

    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setenv('DISPLAY', ':0')
    monkeypatch.delenv('QT_QPA_PLATFORM', raising=False)
    monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)

    monkeypatch.setattr(gui.ctypes.util, 'find_library', lambda name: None)
    assert gui.missing_xcb_cursor()

    monkeypatch.setattr(gui.ctypes.util, 'find_library',
                        lambda name: 'libxcb-cursor.so.0')
    assert not gui.missing_xcb_cursor()


@pytest.mark.parametrize('environment', [
    {'QT_QPA_PLATFORM': 'offscreen'},     # a plugin was chosen explicitly
    {'WAYLAND_DISPLAY': 'wayland-0'},     # xcb is not the plugin in use
    {},                                   # no display at all
])
def test_xcb_check_stays_quiet_when_it_cannot_know(monkeypatch, environment):
    """A false alarm would be worse than the message it replaces."""
    from halostack import gui

    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.setattr(gui.ctypes.util, 'find_library', lambda name: None)
    for name in ('DISPLAY', 'QT_QPA_PLATFORM', 'WAYLAND_DISPLAY'):
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    if 'WAYLAND_DISPLAY' in environment:
        monkeypatch.setenv('DISPLAY', ':0')

    assert not gui.missing_xcb_cursor()


def test_xcb_check_is_linux_only(monkeypatch):
    """Windows and macOS have no xcb plugin to fail."""
    from halostack import gui

    monkeypatch.setattr(gui.ctypes.util, 'find_library', lambda name: None)
    monkeypatch.setenv('DISPLAY', ':0')
    for platform in ('win32', 'darwin'):
        monkeypatch.setattr(sys, 'platform', platform)
        assert not gui.missing_xcb_cursor()


def test_xcb_message_names_a_package_for_each_distribution():
    """Qt's own message names neither a package nor a distribution."""
    from halostack import gui

    message = gui.xcb_cursor_message()
    assert 'libxcb-cursor0' in message
    assert 'xcb-util-cursor' in message
    assert '--cli' in message
