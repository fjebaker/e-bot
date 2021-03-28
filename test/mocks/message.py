"""
Mocks the discord api Message class.

Add functionality as needed -- no point mocking things we never use.
"""
# pylint: disable=too-many-ancestors
from unittest.mock import AsyncMock

from test.mocks._baseclass import MockDiscordBase

_default_values = {"author": None, "content": ""}


class MockMessage(MockDiscordBase):
    """Mock Message Class

    :param **kwargs: Keyword arguments to give values to :py:class:`discord.ext.commands.Context`
        attributes
    """

    def __init__(self, **kwargs):
        super().__init__(_default_values, **kwargs)

        # mock common functions
        self.reply = AsyncMock()
        self.send = AsyncMock()
