import logging

import discord
from discord.ext import commands

import re

EMOJIS = [
    "\U0001F621",
    "\U0001F92C",
    "\U0001F624",
    "\U0001F47F",
    "\U0001F329"
]

class Angery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    def _is_angery(self, content):
        return re.search(r"^angery$", content, re.IGNORECASE) is not None

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            # skip bots
            ...
        else:
            if self._is_angery(message.content):
                for emoji in EMOJIS:
                    await message.add_reaction(emoji)


def setup(bot):
    bot.add_cog(
        Angery(bot)
    )

    return
