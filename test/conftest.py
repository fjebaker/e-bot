import pytest
from unittest.mock import MagicMock


@pytest.fixture(scope="session")
def bot():
    mockbot = MagicMock()
    yield mockbot
