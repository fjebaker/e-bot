import logging
import random
import pathlib

import discord
from discord.ext import commands


class Nostalgia(commands.Cog):
    PROMPTS = [
        "Oh that reminds me!",
        "Interesting point but have you ever considered that maybe:",
        "No??? Clearly,",
        "Yes!! And also,",
    ]

    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

        self.wordlist = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            # skip bots
            ...
        else:
            # 1 in 30 chance
            if random.randint(1, 30) == 22:
                self.logging.info("nostalgia invoked!")
                gid = message.guild.id
                if gid in self.wordlist:
                    wordlist = self.wordlist[gid]
                else:
                    file = pathlib.Path("data/elash_safeties_{gid}.txt".format(gid=gid))
                    if not file.exists():
                        self.logging.warning("file %s does not exist.", file.name)
                        return
                    lines = file.read_text("utf-8").split("\n")
                    self.wordlist[gid] = [item for item in lines if item]
                    wordlist = self.wordlist[gid]

                memory = random.choice(wordlist)
                prompt = random.choice(self.PROMPTS)
                msg = f"{prompt} {memory}"
                await message.reply(msg)


async def setup(bot):
    await bot.add_cog(Nostalgia(bot))
    return
