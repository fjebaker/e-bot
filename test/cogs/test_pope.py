from unittest.mock import MagicMock, patch

import pytest

from test.mocks import MockMessage, MockAuthor

from cogs.pope import PopeImage

_POPEFILE_CONTENT = ["popeitem1", "popeitem2", "popeitem3"]


@pytest.fixture(scope="module", autouse=True)
def populate_popelist(tmp_file):
    """ Fill `data/popelist.txt` with test content. """
    p = tmp_file("data", "popelist.txt")

    with open(p, "w") as f:
        f.write("\n".join(_POPEFILE_CONTENT))

    yield


@pytest.fixture(scope="module")
def _self():
    """ Mocked self instance """
    s = MagicMock()
    s.pope_uris = _POPEFILE_CONTENT
    s.bot = None
    s.logging = None
    return s


def test_constructor():
    """PopeImage needs to have read and populated `self.pope_uris`
    on construction."""
    p = PopeImage(None)

    assert p.pope_uris == _POPEFILE_CONTENT


def test__has_pope(_self):
    """ Ensure `_has_pope` correctly finds pope substrings. """
    # test function
    def tfunc(x):
        return PopeImage._has_pope(_self, x)

    assert tfunc("pope")
    assert tfunc("aoisfjoiasjfpopeoaisjfoia")
    assert tfunc("pOpE")

    assert not tfunc("P0pe")
    assert not tfunc("aoisdfjoasd")


@pytest.mark.asyncio
async def test_on_message(_self):
    """ Ensure response correct """
    ma_nobot = MockAuthor(bot=False)
    mm = MockMessage(author=ma_nobot)

    # test: no pope, no bot
    _self._has_pope.return_value = False
    with patch("random.randint", return_value=1) as _:
        await PopeImage.on_message(_self, mm)

    mm.assert_not_called()

    # test: has pope, is bot
    _self._has_pope.return_value = True
    ma_nobot.bot = True
    with patch("random.randint", return_value=1) as _:
        await PopeImage.on_message(_self, mm)

    mm.assert_not_called()

    # test: has pope, no bot
    ma_nobot.bot = False
    with patch("random.randint", return_value=1) as _:
        await PopeImage.on_message(_self, mm)
    mm.reply.assert_called_with(f"#1\n{_POPEFILE_CONTENT[1]}")
