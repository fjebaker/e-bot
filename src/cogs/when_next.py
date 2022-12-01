import logging

from discord.ext import commands

COG_HELP = """ 
    Starts the process of finding out when people are next available to hang out
    TODO: arguments
"""

class WhenNext(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    @commands.command(name="whennext")
    async def entry(self, context):
        self.logging.info("whennext called")
        await context.send(f"So uhhhh when you next wanna hang out?")


def setup(bot):
    bot.add_cog(WhenNext(bot))

    return
