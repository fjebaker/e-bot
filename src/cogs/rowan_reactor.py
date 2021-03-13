import logging

import discord
from discord.ext import commands

_ID = 691729794462908487
EMOJI = "<:thee:817130256808673283>"

class RowanReactor(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.id == _ID:
            await message.add_reaction(EMOJI)
        
def setup(bot):
    bot.add_cog(
        RowanReactor(bot)
    )

    return
