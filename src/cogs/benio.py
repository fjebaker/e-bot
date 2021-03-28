import logging
import os

from discord.ext import commands

from econfig import PATH_EXTENSION

_ID = 462721725520543764
FILE = os.path.join(PATH_EXTENSION, "data/benmessages.txt")


class BenIO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    def _append_message(self, content):
        with open(FILE, "a") as f:
            f.write(f"\n\n{content}")

    @commands.Cog.listener()
    async def on_message(self, message):
        self.logging.info(f"{message.author.name}, {message.author.id}")
        if message.author.id == _ID:
            self._append_message(message.content)


def setup(bot):
    bot.add_cog(BenIO(bot))

    return
