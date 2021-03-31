import logging
import random
import re
import os

from discord.ext import commands

from econfig import PATH_EXTENSION


class PopeImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

        self.pope_uris = []

        with open(os.path.join(PATH_EXTENSION, "data/popelist.txt"), "r") as f:
            self.pope_uris = list(filter(lambda i: i != "", f.read().split("\n")))

    def _has_pope(self, content: str) -> bool:
        return re.search(r"pope", content, re.IGNORECASE) is not None

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            # skip bots
            ...
        else:
            if self._has_pope(message.content):
                i = random.randint(0, len(self.pope_uris) - 1)
                msg = f"#{i}\n{self.pope_uris[i]}"
                await message.reply(msg)


def setup(bot):
    bot.add_cog(PopeImage(bot))

    return
