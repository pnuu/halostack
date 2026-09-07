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

"""The stacking pipeline.

:func:`stack_images` is the whole of Halostack's processing, with no
dependency on how it was invoked: it takes filenames and settings, asks a
:class:`~halostack.ui.PointSelector` where the alignment reference is, reports
progress through a callback, and returns the finished stacks.  The command
line in :mod:`halostack.cli` is a thin layer on top of it, and a graphical
front end can use it the same way.
"""

import itertools
import logging
from collections import deque, namedtuple

from halostack.align import Align
from halostack.helpers import intermediate_fname
from halostack.image import Image
from halostack.stack import Stack

LOGGER = logging.getLogger(__name__)

#: One requested output.
#:
#: ``mode`` is a :data:`halostack.stack.Stack.MODES` entry, ``filename`` is
#: where to write it (``None`` to only return it), and ``options`` holds any
#: extra settings for the mode, such as ``kappa`` for ``sigma``.
StackRequest = namedtuple('StackRequest', ['mode', 'filename', 'options'])
StackRequest.__new__.__defaults__ = (None, None)

#: The outcome of a run.
StackingResult = namedtuple('StackingResult',
                            ['stacks', 'used', 'total', 'skipped'])


class Cancelled(Exception):
    """Raised when a run was stopped through its *cancel* callback."""


def _report(progress, stage, done, total, message=''):
    """Call the progress callback, if there is one."""
    if progress is not None:
        progress(stage, done, total, message)


def _check_cancelled(cancel):
    """Raise :class:`Cancelled` if the caller has asked the run to stop.

    *cancel* is either a callable returning true or a
    :class:`threading.Event`, so that a caller can use whichever it already
    has. Checks happen between frames and between stacks; a single NumPy
    reduction cannot be interrupted part way through.
    """
    if cancel is None:
        return
    stop = cancel.is_set() if hasattr(cancel, 'is_set') else cancel()
    if stop:
        LOGGER.info("Run cancelled.")
        raise Cancelled("The run was cancelled.")


def _bounded_map(func, items, workers):
    """Apply *func* to *items*, keeping only a few results in flight.

    Threads are enough here: the work is image I/O and NumPy or SciPy calls,
    both of which release the interpreter lock.  Unlike a process pool this
    needs no picklable globals and behaves identically on Windows, where the
    old process-based code had to fall back to a single core.
    """
    items = list(items)
    if workers is None or workers <= 1 or len(items) < 2:
        for item in items:
            yield func(item)
        return

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=workers) as pool:
        remaining = iter(items)
        futures = deque(pool.submit(func, item)
                        for item in itertools.islice(remaining, workers + 1))
        while futures:
            result = futures.popleft().result()
            for item in itertools.islice(remaining, 1):
                futures.append(pool.submit(func, item))
            yield result


def select_areas(base_img, selector, view_gamma=None):
    """Ask the user for the reference area and the area to search it in.

    :param base_img: the image the areas are picked from
    :type base_img: halostack.image.Image
    :param selector: how to ask
    :type selector: halostack.ui.PointSelector
    :param view_gamma: gamma applied to the preview only
    :type view_gamma: float or None
    :rtype: (reference area, search area), each an (x, y, radius) tuple
    """
    preview = base_img.luminance()
    if view_gamma is not None and hasattr(selector, 'gamma'):
        selector.gamma = view_gamma

    reference = selector.select_area(
        preview,
        "Click tight area (two opposite corners) for reference location.")
    LOGGER.debug("Reference area: (%d, %d) with radius %d.", *reference)

    search_area = selector.select_area(
        preview,
        "Click two corner points for the area where the alignment "
        "reference will be in every image.")
    LOGGER.debug("User-selected search area: (%d, %d) with radius %d.",
                 *search_area)

    return reference, search_area


def stack_images(filenames, requests, align=True, reference=None,
                 search_area=None, selector=None, correlation_threshold=0.7,
                 enhance_images=None, enhance_stacks=None, save_prefix=None,
                 view_gamma=None, nprocs=1, bits=16, progress=None,
                 cancel=None):
    """Align and stack a series of images.

    :param filenames: images to stack; the first is the alignment reference
    :type filenames: list of str
    :param requests: the stacks to produce
    :type requests: list of StackRequest
    :param align: whether to align the images at all
    :type align: bool
    :param reference: (x, y, radius) of the reference feature; asked for if
                      not given
    :type reference: 3-element sequence or None
    :param search_area: (x, y, radius) searched in each frame; asked for if
                        not given
    :type search_area: 3-element sequence or None
    :param selector: used to ask for the areas when they are not given
    :type selector: halostack.ui.PointSelector or None
    :param correlation_threshold: minimum correlation for a frame to be used
    :type correlation_threshold: float
    :param enhance_images: processing applied to every input image
    :type enhance_images: dict or None
    :param enhance_stacks: processing applied to every finished stack
    :type enhance_stacks: dict or None
    :param save_prefix: save each aligned frame with this filename prefix
    :type save_prefix: str or None
    :param view_gamma: gamma applied to the preview shown by the selector
    :type view_gamma: float or None
    :param nprocs: number of worker threads used for the per-image work
    :type nprocs: int
    :param bits: bit depth of the written files
    :type bits: int
    :param progress: called as ``progress(stage, done, total, message)``
    :type progress: callable or None
    :param cancel: consulted between frames and between stacks; when it is
                   true the run stops and :class:`Cancelled` is raised
    :type cancel: callable, threading.Event or None
    :rtype: StackingResult
    :raises Cancelled: if *cancel* became true during the run
    """
    filenames = list(filenames)
    requests = list(requests)
    if not filenames:
        raise ValueError("No input images were given.")
    if not requests and save_prefix is None:
        raise ValueError("Nothing to do: no stacks were requested and no "
                         "aligned images are being saved.")

    enhance_images = enhance_images or {}
    enhance_stacks = enhance_stacks or {}
    total = len(filenames)

    stacks = [Stack(request.mode, total, kwargs=request.options)
              for request in requests]

    _check_cancelled(cancel)
    _report(progress, 'read', 0, total, filenames[0])
    base_img = Image(fname=filenames[0])
    LOGGER.debug("Using %s as base image.", filenames[0])

    aligner = None
    if align and total > 1:
        if reference is None or search_area is None:
            if selector is None:
                raise ValueError("Alignment needs a reference area and a "
                                 "search area, or a selector to ask for them.")
            picked_reference, picked_search = select_areas(base_img, selector,
                                                           view_gamma)
            reference = reference or picked_reference
            search_area = search_area or picked_search

        LOGGER.debug("Initializing alignment.")
        aligner = Align(base_img, cor_th=correlation_threshold)
        aligner.set_reference(reference)
        aligner.set_search_area(search_area)
        LOGGER.debug("Alignment initialized.")
    elif align and total == 1:
        LOGGER.debug("Only one image; nothing to align it to.")

    def prepare(item):
        """Read, align and enhance one frame. Returns None if it was rejected."""
        index, fname = item
        # Checked here as well as in the loop below, so that work already
        # queued on the thread pool stops as soon as it starts rather than
        # running to completion first.
        _check_cancelled(cancel)
        img = base_img if index == 0 else Image(fname=fname)

        if aligner is not None and index > 0:
            img = aligner.align(img)
            if img is None:
                return index, fname, None

        if save_prefix is not None:
            img.save(intermediate_fname(save_prefix, fname), bits=bits)

        if enhance_images:
            LOGGER.info("Preprocessing image.")
            img.enhance(enhance_images)

        return index, fname, img

    skipped = []
    used = 0
    for index, fname, img in _bounded_map(prepare, enumerate(filenames), nprocs):
        _check_cancelled(cancel)
        if img is None:
            LOGGER.warning("Skipping image %s.", fname)
            skipped.append(fname)
        else:
            for stack in stacks:
                stack.add_image(img)
            used += 1
        _report(progress, 'stack', index + 1, total, fname)

    if used == 0:
        raise ValueError("None of the %d images could be used." % total)

    results = []
    for number, (request, stack) in enumerate(zip(requests, stacks)):
        _check_cancelled(cancel)
        _report(progress, 'calculate', number, len(requests), request.mode)
        img = stack.calculate()
        if enhance_stacks:
            LOGGER.info("Postprocessing output image.")
            img.enhance(enhance_stacks)
        if request.filename is not None:
            img.save(request.filename, bits=bits)
        results.append((request, img))

    LOGGER.info("Stacked %d/%d images.", used, total)
    if skipped:
        LOGGER.warning("Images that were not used: %s",
                       '\n\t' + '\n\t'.join(skipped))
    _report(progress, 'done', total, total, '')

    return StackingResult(stacks=results, used=used, total=total,
                          skipped=skipped)
