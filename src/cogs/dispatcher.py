from discord.ext import commands

from games.elash import ELash
from games.ecards import ECards
from games.ridethebus import RideTheBus

from abstracts import GuildDispatch

COG_HELP = """
    TODO
"""


class EGameDispatch(GuildDispatch):
    cog_help = COG_HELP
    has_scrape = True

    def __init__(self, bot):
        super().__init__(bot, __name__)

    @commands.command(name="elash")
    async def elash(self, context, cmd: str):
        await self._entry(context, cmd, ELash)

    @commands.command(name="ecards")
    async def ecards(self, context, cmd: str):
        await self._entry(context, cmd, ECards)

    @commands.command(name="ridethebus")
    async def ridethebus(self, context, cmd: str):
        await self._entry(context, cmd, RideTheBus)

    # @commands.command(name="test")
    # async def test(self, context):
    #     ...


async def setup(bot):
    await bot.add_cog(EGameDispatch(bot))
    return
