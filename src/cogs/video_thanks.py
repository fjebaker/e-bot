import logging

import discord
from discord.ext import commands

import random
import re

COG_HELP = """ No help available for this cog. """

MESSAGES = [
    "Wow! Thank you for that great video.",
    "Ohoho! I wasn't expecting that kind of enjoyment haha!",
    "Oh my god! This made me literally LoL (Laugh out Loud)!",
    "Hahahaha! I especially liked the bit just before the middle.",
    "This is great! Where do you find all these things?",
    "Good golly, this was another fantastic video! Thanks!"
]

EMOJI = "\U0001F913"

class VideoThanks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    def _has_video(embeds):
        """ returns True if any of the embeds has a YouTube url """
        for em in embeds:
            if re.search(r"www\.youtube.", em.url) is not None:
                return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            # skip bot messages
            ...
        else:
            if self._has_video(message.embeds):
                # add emoji reaction and reply
                message.add_reaction(EMOJI)
                message.reply(
                    random.choice(MESSAGES)
                )
    

def setup(bot):
    bot.add_cog(
        VideoThanks(bot)
    )

    return