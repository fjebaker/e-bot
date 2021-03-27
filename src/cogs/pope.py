import logging

from discord.ext import commands

import random
import re

import os
from econfig import PATH_EXTENSION

# load uri array
POPE_URIS = []
with open(os.path.join(PATH_EXTENSION, "data/popelist.txt"), "r") as f:
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
                i = random.randint(0, len(POPE_URIS) - 1)
                msg = f"#{i}\n{POPE_URIS[i]}"
                await message.reply(msg)


def setup(bot):
    bot.add_cog(PopeImage(bot))

    return
