# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Halostack stacks and enhances photographs of ice-crystal halos: it coaligns a
series of exposures on a user-picked reference feature (usually the Sun behind a
blocker), combines them into one or more stacks, and applies enhancements that
make faint halos visible. `doc/source/usage.rst` is the reference for CLI
options, config-file syntax and every enhancement, and is the file to update
when any of those change.

## Commands

```bash
pip install -e ".[tests]"            # install with test dependencies
pytest                               # run the test suite
pytest tests/test_stack.py::test_mean_is_a_mean_not_a_sum   # a single test
cd doc && python -m sphinx -b html source _build   # build the docs (must be warning-free)
halostack_cli -a avg.png *.jpg       # the CLI, installed as a console script
```

A prepared environment exists as the `hs-dev` micromamba env; recreate it with:

```bash
micromamba create -y -n hs-dev -c conda-forge python=3.12 numpy scipy imageio \
    pillow tifffile imagecodecs matplotlib pytest rawpy sphinx
```

## Dependencies

Everything must stay installable as a binary wheel on Windows, macOS and Linux —
that is the constraint that drove the port away from PythonMagick, which had to
be compiled against a system ImageMagick. Do not add a dependency that needs a
compiler, a system package, or a runtime download.

- **PNG goes through `imagecodecs`, deliberately.** Pillow cannot write 16-bit
  RGB PNG at all, and silently truncates one to 8 bits when *reading* it — with
  no error. That would throw away half the dynamic range of a stack. TIFF goes
  through `tifffile`, other formats through `imageio`/Pillow, raw files through
  the optional `rawpy`.
- `matplotlib` is only imported by `halostack/ui.py`, and `imagecodecs` only
  inside the `halostack/io.py` functions that need it. Keep it that way: the
  core modules import neither, which is what will let a future GUI be packaged
  without dragging in a plotting library.

## Architecture

The layering matters more than the individual modules: a GUI is planned, so
nothing about *how the user is asked something* may leak into the processing
code.

- **`io.py`** — the only module that knows about file formats. Everything above
  it sees float32 arrays scaled to `[0, 1]`, three channels, no alpha,
  regardless of the source bit depth or format. Add format support here alone.
- **`enhancements.py`** — every image processing method, as a plain function of
  a float array, in the `ENHANCEMENTS` registry. Each entry carries a summary
  and a `Parameter` description of every argument with its default, so a GUI can
  build its controls by enumeration. **Adding an enhancement means adding a
  function with an `@register` decorator and documenting it in
  `doc/source/usage.rst`** — nothing else, and no other file lists the methods.
- **`image.py`** — `Image` wraps one array and the arithmetic operators `Stack`
  needs. There is exactly one representation of the data; `save()` normalises to
  the full output range, which is what makes an arbitrary stack viewable.
- **`align.py`** — locates the reference patch by FFT normalized
  cross-correlation over the search area. `-t` compares against the *squared*
  correlation, preserving the meaning that option has always had.
- **`stack.py`** — the five modes. `min`/`max`/`mean` keep a running result;
  `median`/`sigma` hold every frame. A stack must never retain a reference to an
  image it was handed: several stacks are routinely fed the same frames, and
  sharing a buffer let one silently overwrite another's result.
- **`ui.py`** — `PointSelector` is the seam between processing and interaction.
  `MatplotlibSelector` serves the CLI, `FixedPointSelector` serves tests and
  scripts, and a GUI implements the same two methods against its own canvas.
- **`pipeline.py`** — `stack_images()` is the whole of the processing, with no
  knowledge of how it was invoked. It takes filenames and settings, asks a
  `PointSelector` for the areas, reports progress through a callback, and
  returns the stacks. **New functionality belongs here, not in `cli.py`**, or
  the GUI will not be able to reach it.
- **`cli.py`** — argparse, config files and logging only.

`-p/--nprocs` is a thread pool over the per-frame work (read, align, enhance).
Threads suffice because the work is I/O and NumPy/SciPy calls, both of which
release the GIL, and unlike the old process pool they behave identically on
Windows — which is why the old "Windows is limited to one processor" warning is
gone.

## Packaging

`.github/workflows/windows-executable.yml` builds a standalone
`halostack_cli.exe` with PyInstaller, driven by `packaging/halostack.spec`.
The spec can be run on any platform (`pyinstaller --clean --noconfirm
packaging/halostack.spec`), which is the way to check a packaging change
without waiting for CI.

Three things in that spec are load-bearing, each found by a build that
succeeded and then failed at run time:

- `imagecodecs` must be collected wholesale — it imports one compiled module
  per codec by name, so none is reachable from an import graph.
- `imageio` needs its `.dist-info` copied (`copy_metadata`); it looks up its
  own version at run time and otherwise dies with "No package metadata was
  found for imageio" the first time a JPEG is read.
- Its plugins must *not* be collected wholesale: that pulls in the PyAV,
  OpenCV, GDAL and ITK bindings, whose shared libraries fail to load in ways
  imageio's plugin search does not catch. Only the Pillow plugin is needed.

The workflow runs the test suite on Windows and then exercises the built
executable on generated images across all three image backends. Keep that
smoke test: a PyInstaller bundle that imports cleanly can still fail on the
first file it opens.

## Compatibility

The CLI is a stable interface: every option in `doc/source/usage.rst` must keep
working, including the `--config_file`/`--config_item` underscore spellings kept
as aliases. Changing what a stack computes is a behavioural change to be called
out, not a refactor.

`old/gradients.py.txt` is dead reference code, not part of the package.
