from abstracts import GuildDispatch
from games.elash import ELash

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

    @commands.command(name="test")
    async def test(self, context):
        ip = InteractionPipeline(MessageInteraction())

        e = discord.Embed(title="Test")
        result = await ip.send_and_watch(context.channel, e)

        self.logging.info(result["result"])


def setup(bot):
    bot.add_cog(EGameDispatch(bot))
