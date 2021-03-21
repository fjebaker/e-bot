import logging

import discord
from discord.ext import commands

import asyncio


class GuildDispatch(commands.Cog):
    """Superclass for creating cogs for game instance management. Creates a lookup
    dictionary, indexed by guild id, to seperate game instances.

    Derived classes should define
    - `self.game_name` (`str`)
    - `self.min_players` (`int`)
    - `self.cog_help` (`str`)
    - `self.has_scrape` (`bool`), as to whether this game has channel scraping implemented.
    Scraping requires the definition of a function with the fingerprint
    ```py

    @staticmethod
    async def scrape(context: discord.ext.commands.Context):
        ...

    ```

    :param bot: Bot instance
    :type bot: discord.ext.Bot
    :param logger_name: The module `__name__` of the derived class, used to configure the logger.
    :type logger_name: str
    """

    def __init__(self, bot, logger_name):
        self.bot = bot
        self.logging = logging.getLogger(logger_name)

        # set these in derived
        # self.cog_help = ""
        # self.has_scrape = False

        # class internals
        self.lookup = {}  # lookup game states by guild id

    def embed(self, text: str) -> discord.Embed:
        """TODO"""
        return discord.Embed(
            title="Dispatch Cog", description=text, colour=discord.Colour.red()
        )

    async def _stop(self, gid: int):
        """Stops the game instance running on the guild with id `gid`, and removes
        the instance in the lookup dictionary (so that it is GC'd).

        :param gid: Guild ID
        """
        self.logging.info(f"Stopping {self.lookup[gid]} for {gid}.")

        await self.lookup[gid].stop()
        self.lookup.pop(gid)

    async def _make_instance(self, context, factory):
        """Start a new game instance for the current context. That is to say, will
        create a `factory` instance and store it in `self.lookup[gid]`, where `gid`
        is the guild id of `context`.

        :param context: Discord context.
        :type context: `discord.ext.commands.Context`
        """
        gid = context.guild.id

        self.logging.info(f"Starting {factory} instance for {gid}.")

        # create and store instance
        self.lookup[gid] = factory(context)

    async def _start(self, gid: int, ret_channel, factory):
        """Obtains the factory instance from `self.lookup` of Guild ID `gid`, and calls
        :func:`abstracts.egamefactory.EGameFactory.gather_players`.
        If `factory.min_players` is met, calls :func:`abstracts.egame.EGame.start`.
        """
        instance = self.lookup[gid]

        # gather players
        player_count = await instance.gather_players()

        if player_count < factory.min_players:
            return await ret_channel.send(
                embed=self.embed(
                    f"Too few players to start game. Requires at least {factory.min_players}."
                )
            )
        else:
            return await instance.start()

    async def _entry(self, context, cmd: str, factory):
        """Cog command entry function, to be called from the derived class. Handles command
        and contexts.
        """
        self.logging.info(
            f"entry called for {factory} with {cmd} from guild {context.guild.name}"
        )

        # check if state for guild exists
        if context.guild.id not in self.lookup:

            # info catches
            if cmd == "stop":
                return await context.send(embed=self.embed("No game running."))

            else:
                # start an instance
                await self._make_instance(context, factory)

        # restarting
        if cmd == "start":
            return await self._start(context.guild.id, context.channel, factory)

        # stops must be handled externally
        elif cmd == "stop":
            await self._stop(context.guild.id)
            return await context.send(embed=self.embed(f"Stopped {factory.game_name}."))

        elif cmd == "scrape":

            if self.has_scrape:
                status = await self.lookup[context.guild.id].scrape(context)
                return await context.send(embed=self.embed(status))

            else:
                return await context.send(
                    embed=self.embed("Does not require scraping.")
                )

        # catch all
        await context.send(embed=self.embed("Unknown command."))

    async def cog_command_error(self, context, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await context.send(f"Missing Argument!\n{self.cog_help}")
        else:
            raise error

    def _debug_embed(self, text: str) -> str:
        return discord.Embed(
            title="GuildDispatch Debug", description=f"Lookup table:\n```\n{text}\n```"
        )

    @commands.command(name="dispatch")
    async def debug(self, context, cmd):

        if cmd == "debug":
            await context.send(embed=self._debug_embed(str(self.lookup)))
