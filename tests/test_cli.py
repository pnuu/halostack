"""Tests for the command line interface."""

import pytest

from halostack import cli


def parse(argv):
    """Parse *argv* and return the settings dictionary."""
    return cli.parse_arguments(argv)[0]


def test_every_documented_option_is_accepted():
    """The command line has not changed, so all of these must still parse."""
    args = parse(['-a', 'avg.png', '-m', 'min.png', '-M', 'max.png',
                  '-d', 'med.png', '-S', 'sig.png', '-k', '2.5,4',
                  '-t', '0.8', '-s', 'al', '-n', '-e', 'gradient',
                  '-E', 'usm:25,2', '-g', '0.45', '-p', '4', 'a.jpg'])

    assert args['avg_stack_file'] == 'avg.png'
    assert args['min_stack_file'] == 'min.png'
    assert args['max_stack_file'] == 'max.png'
    assert args['median_stack_file'] == 'med.png'
    assert args['sigma_stack_file'] == 'sig.png'
    assert args['correlation_threshold'] == pytest.approx(0.8)
    assert args['save_prefix'] == 'al'
    assert args['no_alignment'] is True
    assert args['view_gamma'] == pytest.approx(0.45)
    assert args['nprocs'] == 4


def test_stacks_are_requested_in_the_documented_order():
    """min, max, mean, median then sigma, as the old CLI built them."""
    args = parse(['-a', 'a.png', '-m', 'm.png', '-M', 'M.png',
                  '-d', 'd.png', '-S', 'S.png', 'in.jpg'])

    assert [request.mode for request in cli.collect_requests(args)] == [
        'min', 'max', 'mean', 'median', 'sigma']


def test_kappa_sigma_parameters_reach_the_sigma_stack():
    """-k sets kappa and the iteration count."""
    args = parse(['-S', 'sig.png', '-k', '2.2,3', 'in.jpg'])
    request = cli.collect_requests(args)[0]

    assert request.options == {'kappa': 2.2, 'max_iters': 3}


def test_defaults_match_the_documentation():
    """Threshold 0.7, one worker, alignment on."""
    args = parse(['-a', 'avg.png', 'in.jpg'])

    assert args['correlation_threshold'] == pytest.approx(0.7)
    assert args['nprocs'] == 1
    assert args['no_alignment'] is False


def test_enhancements_can_be_repeated():
    """-e and -E accumulate, and run in the order given."""
    args = parse(['-a', 'a.png', '-e', 'gradient', '-e', 'br',
                  '-E', 'usm:25,2', '-E', 'stretch', 'in.jpg'])

    assert list(args['enhance_images']) == ['gradient', 'br']
    assert list(args['enhance_stacks']) == ['usm', 'stretch']


def test_config_file_is_read(tmp_path):
    """-C alone uses the [default] section."""
    config = tmp_path / 'c.ini'
    config.write_text("[default]\navg_stack_file = from_config.png\n")

    assert parse(['-C', str(config), 'in.jpg'])['avg_stack_file'] == \
        'from_config.png'


def test_config_item_selects_a_section(tmp_path):
    """-c picks the section, as the documentation describes."""
    config = tmp_path / 'c.ini'
    config.write_text("[default]\navg_stack_file = wrong.png\n"
                      "[br]\navg_stack_file = right.png\n")

    assert parse(['-C', str(config), '-c', 'br', 'in.jpg'])['avg_stack_file'] \
        == 'right.png'


def test_config_item_without_a_file_is_an_error(capsys):
    """Regression: -c alone used to crash inside the config parser."""
    with pytest.raises(SystemExit):
        parse(['-c', 'br', 'in.jpg'])

    assert 'config-file' in capsys.readouterr().err


def test_underscored_option_names_still_work(tmp_path):
    """The old --config_file spelling is kept as an alias."""
    config = tmp_path / 'c.ini'
    config.write_text("[br]\navg_stack_file = out.png\n")

    args = parse(['--config_file', str(config), '--config_item', 'br', 'in.jpg'])
    assert args['avg_stack_file'] == 'out.png'


def test_nothing_to_do_returns_an_error_status(tmp_path, capsys):
    """With no stack requested there is nothing to compute."""
    assert cli.main(['in.jpg']) == 1


def test_full_run(tmp_path, frame_files):
    """The CLI end to end, with alignment turned off so nothing is clicked."""
    fnames, _ = frame_files
    out = str(tmp_path / 'avg.png')

    assert cli.main(['-n', '-a', out, '-E', 'stretch'] + fnames) == 0

    from halostack.image import Image
    assert Image(fname=out).shape == (60, 80, 3)
