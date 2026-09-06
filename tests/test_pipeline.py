"""End-to-end tests for the stacking pipeline."""

import numpy as np
import pytest

from halostack import io
from halostack.image import Image
from halostack.pipeline import StackRequest, stack_images
from halostack.ui import FixedPointSelector
from tests.conftest import synthetic_frame

# Two clicks per area: the reference around the blob, then the wider search
# area it is looked for in.
CORNERS = [(32, 22), (48, 38), (20, 10), (60, 50)]


def selector():
    """A selector that answers both area questions without a display."""
    return FixedPointSelector(CORNERS)


def test_stacks_are_written(tmp_path, frame_files):
    """The requested files appear and can be read back."""
    fnames, _ = frame_files
    out = str(tmp_path / 'avg.png')

    result = stack_images(fnames, [StackRequest('mean', out)],
                          selector=selector())

    assert result.used == 3
    assert Image(fname=out).shape == (60, 80, 3)


def test_two_images_are_aligned(tmp_path, frame_files):
    """Regression: with exactly two inputs alignment was silently skipped.

    The prompts were shown, the aligner was built, and then never used.
    """
    fnames, offsets = frame_files
    calls = []

    result = stack_images(fnames[:2], [StackRequest('mean', None)],
                          selector=selector(),
                          progress=lambda *args: calls.append(args))

    assert result.used == 2
    # The blob is in the same place in the stack as in the reference frame,
    # which can only happen if the second frame really was shifted back.
    stacked = result.stacks[0][1].img
    reference = synthetic_frame()
    assert np.argmax(stacked.mean(axis=2)) == np.argmax(reference.mean(axis=2))
    assert offsets[1] != (0, 0)          # the second frame really was offset


def test_alignment_can_be_switched_off(tmp_path, frame_files):
    """-n stacks the frames where they lie, and needs no selector."""
    fnames, _ = frame_files

    result = stack_images(fnames, [StackRequest('mean', None)], align=False)

    assert result.used == 3


def test_areas_can_be_given_instead_of_asked_for(frame_files):
    """A GUI supplies the areas directly rather than through a selector."""
    fnames, _ = frame_files

    result = stack_images(fnames, [StackRequest('mean', None)],
                          reference=(40, 30, 8), search_area=(40, 30, 20))

    assert result.used == 3


def test_unmatched_frames_are_skipped(tmp_path, frame_files):
    """A frame that does not correlate is reported, not stacked."""
    fnames, _ = frame_files
    noise = tmp_path / 'noise.png'
    io.write(str(noise), np.random.default_rng(3).random((60, 80, 3)).astype(np.float32))

    result = stack_images(fnames + [str(noise)], [StackRequest('mean', None)],
                          reference=(40, 30, 8), search_area=(40, 30, 20))

    assert result.skipped == [str(noise)]
    assert result.used == 3


def test_several_stacks_at_once_are_independent(tmp_path, frame_files):
    """Regression: min, max and mean together shared one buffer."""
    fnames, _ = frame_files
    requests = [StackRequest('min', str(tmp_path / 'min.png')),
                StackRequest('max', str(tmp_path / 'max.png')),
                StackRequest('mean', str(tmp_path / 'avg.png'))]

    result = stack_images(fnames, requests, reference=(40, 30, 8),
                          search_area=(40, 30, 20))

    images = {request.mode: img for request, img in result.stacks}
    # The blob is bright, so the maximum stack must be brighter than the
    # minimum one everywhere it appears.
    assert images['max'].img.mean() > images['mean'].img.mean()
    assert images['mean'].img.mean() > images['min'].img.mean()


def test_intermediate_images_are_saved(tmp_path, frame_files):
    """-s writes one aligned PNG per input frame."""
    fnames, _ = frame_files

    stack_images(fnames, [StackRequest('mean', None)], save_prefix='al',
                 reference=(40, 30, 8), search_area=(40, 30, 20))

    saved = sorted(tmp_path.glob('al_frame*.png'))
    assert len(saved) == 3


def test_enhancements_are_applied_to_frames_and_stacks(frame_files):
    """-e collapses the frames to 2-D, so the stack is 2-D too."""
    fnames, _ = frame_files

    result = stack_images(fnames, [StackRequest('mean', None)], align=False,
                          enhance_images={'br': None})

    assert result.stacks[0][1].shape == (60, 80)


def test_progress_is_reported(frame_files):
    """A GUI needs to know how far along the run is."""
    fnames, _ = frame_files
    seen = []

    stack_images(fnames, [StackRequest('mean', None)], align=False,
                 progress=lambda stage, done, total, message:
                 seen.append((stage, done, total)))

    stages = [stage for stage, _, _ in seen]
    assert 'stack' in stages and 'done' in stages
    assert seen[-1][1] == seen[-1][2] == 3


@pytest.mark.parametrize('nprocs', [1, 3])
def test_worker_count_does_not_change_the_result(frame_files, nprocs):
    """Threads are an optimisation; the stack must come out the same."""
    fnames, _ = frame_files
    result = stack_images(fnames, [StackRequest('mean', None)],
                          reference=(40, 30, 8), search_area=(40, 30, 20),
                          nprocs=nprocs)

    reference = stack_images(fnames, [StackRequest('mean', None)],
                             reference=(40, 30, 8), search_area=(40, 30, 20),
                             nprocs=1)
    assert result.stacks[0][1].img == pytest.approx(reference.stacks[0][1].img)


def test_no_inputs_is_reported():
    """An empty file list explains itself."""
    with pytest.raises(ValueError, match='No input images'):
        stack_images([], [StackRequest('mean', None)])


def test_nothing_to_do_is_reported(frame_files):
    """No stacks and no saving means there is nothing to compute."""
    fnames, _ = frame_files

    with pytest.raises(ValueError, match='Nothing to do'):
        stack_images(fnames, [])


def test_alignment_without_areas_or_selector_is_reported(frame_files):
    """The pipeline cannot invent the reference area."""
    fnames, _ = frame_files

    with pytest.raises(ValueError, match='selector'):
        stack_images(fnames, [StackRequest('mean', None)])
