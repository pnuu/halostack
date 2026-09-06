"""Tests for the filename and configuration helpers."""

import os

import pytest

from halostack import helpers


def test_wildcards_are_expanded(tmp_path):
    """Windows shells do not expand patterns, so Halostack has to."""
    for name in ('a1.jpg', 'a2.jpg', 'b1.jpg'):
        (tmp_path / name).touch()

    found = helpers.get_filenames([str(tmp_path / 'a*.jpg')])
    assert [os.path.basename(name) for name in found] == ['a1.jpg', 'a2.jpg']


def test_question_mark_and_class_patterns_are_expanded(tmp_path):
    """Regression: only '*' used to count as a wildcard."""
    for name in ('c1.jpg', 'c2.jpg'):
        (tmp_path / name).touch()

    assert len(helpers.get_filenames([str(tmp_path / 'c?.jpg')])) == 2
    assert len(helpers.get_filenames([str(tmp_path / 'c[12].jpg')])) == 2


def test_plain_names_are_passed_through():
    """A name without wildcards is used as given, even if it does not exist."""
    assert helpers.get_filenames(['one.jpg', 'two.jpg']) == ['one.jpg', 'two.jpg']


def test_parse_enhancements_keeps_order_and_types():
    """Arguments become floats where possible; order decides what runs first."""
    parsed = helpers.parse_enhancements(['usm:25,5', 'gradient', 'br'])

    assert list(parsed) == ['usm', 'gradient', 'br']
    assert parsed['usm'] == [25.0, 5.0]
    assert parsed['gradient'] is None


def test_intermediate_fname_prepends_a_prefix():
    """The -s option is documented as a prefix, and behaves as one."""
    result = helpers.intermediate_fname('aligned', os.path.join('d', 'IMG_1.jpg'))

    assert result == os.path.join('d', 'aligned_IMG_1.png')


def write_config(tmp_path, text):
    """Write *text* to a config file and return its name."""
    fname = tmp_path / 'config.ini'
    fname.write_text(text)

    return str(fname)


def test_config_fills_in_missing_values(tmp_path):
    """Anything the command line left unset comes from the file."""
    fname = write_config(tmp_path, "[br]\navg_stack_file = out.png\n"
                                   "view_gamma = 0.45\nno_alignment = True\n")
    args = helpers.read_config({'config_file': fname, 'config_item': 'br',
                                'avg_stack_file': None, 'view_gamma': None,
                                'no_alignment': None})

    assert args['avg_stack_file'] == 'out.png'
    assert args['view_gamma'] == pytest.approx(0.45)
    assert args['no_alignment'] is True


def test_command_line_wins_over_the_config_file(tmp_path):
    """The documented rule: command line options override the file."""
    fname = write_config(tmp_path, "[br]\navg_stack_file = from_config.png\n")
    args = helpers.read_config({'config_file': fname, 'config_item': 'br',
                                'avg_stack_file': 'from_cli.png'})

    assert args['avg_stack_file'] == 'from_cli.png'


def test_command_line_enhancements_replace_configured_ones(tmp_path):
    """Regression: configured methods used to be appended to the given ones."""
    fname = write_config(tmp_path, "[br]\nenhance_stacks = gradient br\n")
    args = helpers.read_config({'config_file': fname, 'config_item': 'br',
                                'enhance_stacks': ['usm:25,2']})

    assert args['enhance_stacks'] == ['usm:25,2']


def test_configured_enhancements_are_used_when_none_are_given(tmp_path):
    """With nothing on the command line, the file's list is used."""
    fname = write_config(tmp_path, "[br]\nenhance_stacks = gradient br\n")
    args = helpers.read_config({'config_file': fname, 'config_item': 'br',
                                'enhance_stacks': []})

    assert args['enhance_stacks'] == ['gradient', 'br']


def test_default_section_is_used_without_an_item(tmp_path):
    """-C alone used to be accepted and then silently ignored."""
    fname = write_config(tmp_path, "[default]\navg_stack_file = out.png\n")
    args = helpers.read_config({'config_file': fname, 'config_item': None,
                                'avg_stack_file': None})

    assert args['avg_stack_file'] == 'out.png'


def test_missing_section_lists_the_available_ones(tmp_path):
    """A typo in -c should say what could have been meant."""
    fname = write_config(tmp_path, "[br]\navg_stack_file = out.png\n")

    with pytest.raises(ValueError, match='br'):
        helpers.read_config({'config_file': fname, 'config_item': 'nope'})


def test_missing_config_file_is_reported(tmp_path):
    """A missing file is named rather than silently ignored."""
    with pytest.raises(ValueError, match='No such'):
        helpers.read_config({'config_file': str(tmp_path / 'nope.ini')})
