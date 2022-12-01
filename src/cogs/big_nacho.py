import logging
import re

from discord.ext import commands


URI = "http://e-doritos.com/img/dorito.png"


class BigNacho(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    def _has_pope(self, content):
        return re.search(r"the big nacho", content, re.IGNORECASE) is not None

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            # skip bots
            ...
        else:
            if self._has_pope(message.content):
                await message.reply(URI)


async def setup(bot):
    await bot.add_cog(BigNacho(bot))

    return
