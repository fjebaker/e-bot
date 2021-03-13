import logging

import discord
from discord.ext import commands

import random
import re

COG_HELP = """ No help available for this cog. """

class XtianServer(commands.Cog):

    emojis = [
        "\U0001F47F",
        "\U0001F6D1",
        "\U000026EA",
        "\U00002626"
    ]

    censored_words = [
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
        "ankle"
    ]

    rude_message = "Please do not swear; this is a wholesome, family-friendly christian server thank you very much."

    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    def _contains_cuss(self, content):
        """
        checks a string for censored words.

        :param content: string, the content string to check for censored words
        :return: true if any words in CENSORED_WORDS are in the content string, false otherwise.
        """
        for word in self.censored_words:
            if content.find(word) != -1:
                return true
        return false

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            # skip bot messages
            ...
        else:
            if self._contains_cuss(message.content):
                # add emoji reaction
                for emoji in self.emojis:
                    await message.add_reaction(emoji)
                await message.reply(
                    self.rude_message
                )


def setup(bot):
    bot.add_cog(
        XtianServer(bot)
    )

    return
