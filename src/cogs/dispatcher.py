import discord
from discord import app_commands

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

    @app_commands.command(name="elash")
    @app_commands.choices(cmd=ELash.choices())
    async def elash(self, interaction: discord.Interaction, cmd: str):
        await self._entry(interaction, cmd, ELash)

    @app_commands.command(name="ecards")
    @app_commands.choices(cmd=ECards.choices())
    async def ecards(self, interaction: discord.Interaction, cmd: str):
        await self._entry(interaction, cmd, ECards)

    @app_commands.command(name="ridethebus")
    @app_commands.choices(cmd=RideTheBus.choices())
    async def ridethebus(self, interaction: discord.Interaction, cmd: str):
        await self._entry(interaction, cmd, RideTheBus)

    # @app_commands.command(name="test")
    # async def test(self, interaction: discord.Interaction):
    #     ...


async def setup(bot):
    await bot.add_cog(EGameDispatch(bot))
    return
