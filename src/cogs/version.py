import logging

import discord
from discord.ext import commands

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    @commands.command(name="version")
    async def entry(self, context):
        await context.send("Currently running e-bot version 0.1.0")


async def setup(bot):
    await bot.add_cog(Version(bot))

    return
