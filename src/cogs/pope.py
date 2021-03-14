import logging

import discord
from discord.ext import commands

import re

POPE_URI = "https://cdn.cnn.com/cnnnext/dam/assets/180118223304-papa-francisco-chile-peru-choque-caballo-mujer-flores-amazonia-minutofrancisco-18-enero-18-pm-00000230-large-169.jpg"

class RowanReactor(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    def _has_pope(self, content):
        return re.search(r"pope", content, re.IGNORECASE) is not None

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            # skip bots
            ...
        else:
            if self._has_pope(message.content):
                await message.reply(
                    POPE_URI
                )
        
def setup(bot):
    bot.add_cog(
        RowanReactor(bot)
    )

    return
