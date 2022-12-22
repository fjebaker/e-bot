import logging
import datetime

import discord
from discord.ext import commands

from interactive import (
    InteractionPipeline,
    ChoiceInteraction,
)

DATE_FORMAT = "%d/%m/%y"
FROM_KEY = "--from"
UNTIL_KEY = "--until"

COG_HELP = f"""
    Starts the process of finding out when people are next available to hang out
    Arguments:
        {FROM_KEY}: Specifies the first day that can be selected to hang out on
        {UNTIL_KEY}: Specifies the last day that can be selected to hang out on
"""


class WhenNext(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    @commands.command(name="whennext")
    async def entry(self, context, cmd: str):
        self.logging.info("whennext called")
        from_date = datetime.date.today()
        until_date = from_date + datetime.timedelta(weeks=2)
        weekend_days = []
        while from_date < until_date:
            if from_date.weekday() > 4:
                weekend_days.append(from_date.strftime(DATE_FORMAT))
            from_date = from_date + datetime.timedelta(days=1)
        ipl = InteractionPipeline(ChoiceInteraction(*weekend_days))
        await ipl.send_and_watch(
            context.channel,
            discord.Embed(
                title="Hang-out planning",
                description="Uhhhh so when do you wanna hang out?",
                colour=discord.Colour.blue(),
            ),
            timeout=1,
        )

async def setup(bot):
    await bot.add_cog(WhenNext(bot))

    return
