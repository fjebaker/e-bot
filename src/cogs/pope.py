import logging

import discord
from discord.ext import commands

import random
import re

# load uri array
POPE_URIS = []
with open("./data/popelist.txt", "r") as f:
    POPE_URIS = [i for i in f.read().split("\n") if i != ""]


class PopeImage(commands.Cog):

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
                    random.choice(POPE_URIS)
                )
        
def setup(bot):
    bot.add_cog(
        PopeImage(bot)
    )

    return
