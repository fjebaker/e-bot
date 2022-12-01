import logging
import datetime

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
        arg_dict = self._parse_command(cmd)
        from_date = datetime.date.today()
        if (FROM_KEY in arg_dict):
            from_date = self._parse_date(context, arg_dict[FROM_KEY])
            if (from_date == False):
                return
        until_date = from_date + datetime.timedelta(weeks=2)
        if (UNTIL_KEY in arg_dict):
            until_date = self._parse_date(context, arg_dict[UNTIL_KEY])
            if (until_date == False):
                return
        weekend_days = []
        while(from_date < until_date):
            if(from_date.weekday() > 4):
                weekend_days.append(from_date.strftime(DATE_FORMAT))
            from_date = from_date + datetime.timedelta(days=1)
        ipl = InteractionPipeline(
            ChoiceInteraction(*weekend_days)
        )
        await ipl.send_and_watch(
            context.channel,
            self.embed("Uhhhh so when do you wanna hang out?"),
            timeout=1,
        )

    async def _parse_date(context, date: str):
        try:
            from_date = datetime.datetime.strptime(date, DATE_FORMAT)
            return from_date.date()
        except ValueError:
            await context.send(f"Invalid start date - try the format dd/mm/yy")
            return False

    def _parse_command(cmd: str):
        cmd_parts = cmd.split(" ")
        return zip(cmd_parts[::2], cmd_parts[1::2])

def setup(bot):
    bot.add_cog(WhenNext(bot))

    return
