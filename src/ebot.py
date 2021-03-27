import logging
import pkgutil

import discord
from discord.ext import commands

import cogs


class EBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=".e ", activity=discord.Game(name="Loading..."))
        self.logging = logging.getLogger(__name__)

    def load_all_available_cogs(self):
        self.logging.info("Loading cogs...")
        for i in pkgutil.walk_packages(cogs.__path__, cogs.__name__ + "."):
            name = i.name
            try:
                self.load_extension(name)
                self.logging.info(f"{name} loaded as extensions")
            except Exception as e:
                self.logging.error(f"{name} failed to load: raised exception: {e}")

    async def on_ready(self):
        await self.wait_until_ready()
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="you. \U0001F441\U0001F444\U0001F441",
            )
        )

    async def on_command_error(self, context, error):
        # pylint: disable=arguments-differ
        if isinstance(error, commands.CommandNotFound):
            self.logging.info(f"Call to unknown command {error}")
            await context.send(error)
        else:
            raise error
