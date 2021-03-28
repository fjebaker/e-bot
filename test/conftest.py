# pylint: disable=global-statement
import tempfile
import shutil
import os
import sys

from typing import Callable

from unittest.mock import MagicMock

import pytest

# insert path of bot
sys.path.insert(0, os.path.abspath("./src"))


# configuration
import econfig  # noqa: E402; pylint: disable=import-error,wrong-import-position


@pytest.fixture(scope="session")
def bot() -> MagicMock:
    mockbot = MagicMock()
    yield mockbot


# use temporary directory

tmp_directory = tempfile.mkdtemp()
# set path extension to temporary directory
econfig.PATH_EXTENSION = tmp_directory

# create empty data directory
os.mkdir(os.path.join(tmp_directory, "data"))


@pytest.fixture(scope="session")
def tmp_file() -> Callable[[str], str]:
    """ Get a function for creating files in the temporary directory """
    global tmp_directory

    def _builder(*path: str) -> str:
        p = os.path.join(tmp_directory, *path)
        # touch file
        with open(p, "a"):
            ...

        return p

    return _builder


def pytest_sessionfinish(session, exitstatus):
    """ Called when full test run is finished to cleanup """
    # pylint: disable=unused-argument
    global tmp_directory
    # delete directory
    shutil.rmtree(tmp_directory)
