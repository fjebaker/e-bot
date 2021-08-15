import logging
import random
import re

from discord.ext import commands


COG_HELP = """ No help available for this cog. """

MESSAGES = [
    "Wow! Thank you for that great video.",
    "Ohoho! I wasn't expecting that kind of enjoyment haha!",
    "Oh my god! This made me literally LoL (Laugh out Loud)!",
    "Hahahaha! I especially liked the bit just before the middle.",
    "This is great! Where do you find all these things?",
    "Good golly, this was another fantastic video! Thanks!",
    "This is absolutely blowing my mind! Love it!",
    "Jeepers creepers, another top notch video there old chum!",
    "Holy guacamole! I LOOOOOOOOVE IT!",
    "I am forever indebted to you for this glorious video!",
    "You can't just keep coming at me with these incredible vids. I don't think I can take much more...",
]

EMOJI = "\U0001F913"


class VideoThanks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    def _has_video(self, content):
        """returns True if message has a YouTube url"""
        return re.search(r"www\.youtube\.com", content) is not None

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            # skip bot messages
            ...
        else:
            if self._has_video(message.content):
                # add emoji reaction and reply
                await message.add_reaction(EMOJI)
                await message.reply(random.choice(MESSAGES))


def setup(bot):
    bot.add_cog(VideoThanks(bot))

    return
