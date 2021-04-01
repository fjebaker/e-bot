import logging
import pkgutil

import discord
from discord.ext import commands

import cogs


class EBot(commands.Bot):
    """ TODO """

    def __init__(self):
        super().__init__(command_prefix=".e ", activity=discord.Game(name="Loading..."))
        self.logging = logging.getLogger(__name__)

    def load_all_available_cogs(self):
        """ TODO """
        self.logging.info("Loading cogs...")
        for i in pkgutil.walk_packages(cogs.__path__, cogs.__name__ + "."):
            name = i.name
            try:
                self.load_extension(name)
                self.logging.info(f"{name} loaded as extensions")
            except Exception as e:
                self.logging.error(f"{name} failed to load: raised exception: {e}")

    def log_infos(self):
        """Write information about the bot to logs.

        Currently logs:
            - connected guild name and guild id
        """
        for g in self.guilds:
            self.logging.info(f"Active on guild {g} (id={g.id})")

    async def on_ready(self):
        """ TODO """
        await self.wait_until_ready()
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="you. \U0001F441\U0001F444\U0001F441",
            )
        )

        self.log_infos()

    async def on_command_error(self, context, error):
        """ TODO """
        # pylint: disable=arguments-differ
        if isinstance(error, commands.CommandNotFound):
            self.logging.info(f"Call to unknown command {error}")
            await context.send(error)
        else:
            raise error
