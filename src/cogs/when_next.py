import logging
import datetime

import discord
from discord.ext import commands

from interactive import (
    InteractionPipeline,
    ChoiceInteraction,
)

DATE_FORMAT = "%d/%m/%y"

COG_HELP = """
    Starts the process of finding out when people are next available to hang out
    Arguments:
        days: Specifies the number of days from the start date to check availability across.
        weekdays: Filters the included days to only include certain days of the week.
           For example, "135" would only include Mondays, Wednesdays and Fridays.
        start_offset: How many days after the current date the start date should be.
"""


class WhenNext(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    @commands.command(name="whennext")
    async def entry(
        self, context, days: str = "31", weekdays: str = "567", start_offset: str = "0"
    ):
        self.logging.info("whennext called")
        days_int = await self._parse_int(context, "days", days)
        if days_int is False:
            return
        offset_int = await self._parse_int(context, "start_offset", start_offset)
        if offset_int is False:
            return
        from_date = datetime.date.today() + datetime.timedelta(days=offset_int)
        until_date = from_date + datetime.timedelta(days=days_int)
        self.logging.info(
            f"Calculating dates from {from_date} until {until_date}, including weekdays {weekdays}"
        )
        valid_days = []
        while from_date < until_date:
            if str(from_date.weekday()) in weekdays:
                valid_days.append(from_date.strftime(DATE_FORMAT))
            from_date = from_date + datetime.timedelta(days=1)
        if valid_days:
            ipl = InteractionPipeline(ChoiceInteraction(*valid_days))
            await ipl.send_and_watch(
                context.channel,
                discord.Embed(
                    title="Hang-out planning",
                    description="Uhhhhh so when do you wanna hang out?",
                    colour=discord.Colour.blue(),
                ),
                timeout=1,
            )
        else:
            await context.send(
                "Invalid combination of parameters led to no valid days to vote on"
            )

    async def _parse_int(self, context, param_name: str, input_text: str):
        try:
            parsed_int = int(input_text)
            return parsed_int
        except ValueError:
            await context.send(
                f"Invalid input for parameter '{param_name}' - expecting an integer, got '{input_text}'"
            )
            return False


async def setup(bot):
    await bot.add_cog(WhenNext(bot))

    return
