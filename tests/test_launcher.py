"""Tests for choosing between the window and the command line."""

import pytest

from halostack.launcher import choose_mode


@pytest.mark.parametrize('argv, expected', [
    ([], 'gui'),
    (['--gui'], 'gui'),
    (['IMG_0001.jpg'], 'gui'),
    (['IMG_0001.jpg', 'IMG_0002.jpg'], 'gui'),
    (['--gui', '-a', 'avg.png', 'in.jpg'], 'gui'),
    (['-a', 'avg.png', 'in.jpg'], 'cli'),
    (['-n', 'in.jpg'], 'cli'),
    (['--cli'], 'cli'),
    (['--no-gui'], 'cli'),
    (['--cli', 'in.jpg'], 'cli'),
    (['--help'], 'cli'),
    (['-h'], 'cli'),
    (['--version'], 'cli'),
    (['-v'], 'cli'),
])
def test_mode_is_chosen_from_the_arguments(argv, expected):
    """No arguments opens the window; an option means do the work now."""
    assert choose_mode(argv)[0] == expected


def test_bare_filenames_open_the_window_with_them():
    """So that associating image files with Halostack does something useful."""
    mode, rest = choose_mode(['a.jpg', 'b.jpg'])

    assert mode == 'gui'
    assert rest == ['a.jpg', 'b.jpg']


def test_mode_flags_are_removed_from_the_arguments():
    """The parser downstream must not see the flags meant for the launcher."""
    assert choose_mode(['--gui', '-a', 'avg.png'])[1] == ['-a', 'avg.png']
    assert choose_mode(['--cli', 'in.jpg'])[1] == ['in.jpg']


def test_help_wins_over_bare_filenames():
    """--help has to reach the parser that can print it."""
    assert choose_mode(['in.jpg', '--help'])[0] == 'cli'


def test_asking_for_both_interfaces_is_an_error():
    """--gui and --cli together have no sensible meaning."""
    with pytest.raises(ValueError, match='only one'):
        choose_mode(['--gui', '--cli'])


def test_a_lone_dash_is_not_an_option():
    """'-' is a filename by convention, not a switch."""
    assert choose_mode(['-'])[0] == 'gui'
