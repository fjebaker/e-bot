from abstracts import GuildDispatch
from games.elash import ELash
from games.ecards import ECards

import discord
from discord.ext import commands

COG_HELP = """
    TODO
"""

from interactive import *


class EGameDispatch(GuildDispatch):
    cog_help = COG_HELP
    has_scrape = True

    def __init__(self, bot):
        super().__init__(bot, __name__)

    @commands.command(name="elash")
    async def entry(self, context, cmd: str):
        await self._entry(context, cmd, ELash)

    @commands.command(name="ecards")
    async def cards(self, context, cmd: str):
        await self._entry(context, cmd, ECards)

    @commands.command(name="test")
    async def test(self, context):
        ...


def setup(bot):
    bot.add_cog(EGameDispatch(bot))
