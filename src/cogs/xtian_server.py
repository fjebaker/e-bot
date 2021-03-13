import logging

import discord
from discord.ext import commands

import random
import re

COG_HELP = """ No help available for this cog. """

EMOJIS = ["\U0001F47F", "\U0001F6D1", "\U000026EA", "\U00002626"]

CENSORED_WELL = [
    "heck",
    "darn",
    "drat",
    "devil",
    "lewd",
    "wtf",
    "frick",
    "ffs",
    "shizzle",
    "bum",
    "butt",
    "pee",
    "poo",
    "ankle",
]

RUDE_MESSAGE = "Please do not swear; this is a wholesome, family-friendly christian server thank you very much."


class XtianServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    def _contains_cuss(self, content):
        """
        checks a string for censored words.

        :param content: string, the content string to check for censored words
        :return: true if any words in CENSORED_WORDS are in the content string, false otherwise.
        """
        for word in CENSORED_WELL:
            if content.find(word) != -1:
                return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            # skip bot messages
            ...
        else:
            if self._contains_cuss(message.content):
                # add emoji reaction
                for emoji in EMOJIS:
                    await message.add_reaction(emoji)
                await message.reply(RUDE_MESSAGE, tts=True)


def setup(bot):
    bot.add_cog(XtianServer(bot))

    return
