#!/usr/bin/env python3
from pathlib import Path

import pytest


@pytest.fixture(name='fixtures_dir', scope='session')
def fixture_fixtures_dir():
    """Given: path to test fixtures directory."""
    return Path(__file__).parent / 'fixtures'
