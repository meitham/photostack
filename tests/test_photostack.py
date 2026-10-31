#!/usr/bin/env python3

import pytest

import photostack


def test_version():
    # given: the package is installed

    # when: we access the version
    version = photostack.__version__

    # then: version is set correctly
    assert version == '0.1.0'


def test_cli_no_command_shows_help_and_exits():
    # given: no command arguments
    from photostack.cli import cli

    # when: cli is invoked without a command
    # then: it exits with code 1
    with pytest.raises(SystemExit) as exc_info:
        cli([])

    assert exc_info.value.code == 1
