import logging
import asyncio
from collections import namedtuple
from typing import Callable

import discord
from discord.ext import commands

# data type for storing factories
FactoryTask = namedtuple("FactoryTask", ("instance", "future"))


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
        self.cog_help: str

        # class internals
        self.lookup = {}  # lookup game states by guild id

    def embed(self, text: str) -> discord.Embed:
        """TODO"""
        return discord.Embed(
            title="Dispatch Cog", description=text, colour=discord.Colour.red()
        )

    def _stop(self, gid: int) -> str:
        """Stops the game instance running on the guild with id `gid`, and removes
        the instance in the lookup dictionary (so that it is GC'd).

        :param gid: Guild ID

        :return: Info string
        """
        self.logging.info(f"Stopping {self.lookup[gid]} for {gid}.")

        ft = self.lookup[gid]

        if ft.future.cancel():
            # successfully cancelled; game removes itseld
            ...
        else:
            self.logging.warning(f"Failed to stop {ft}")
            return "Error stopping game."

        assert gid not in self.lookup  # sanity check

        return "Game succesfully stopped"

    def _make_instance(self, context, factory):
        """Start a new game instance for the current context. That is to say, will
        create a `factory` instance and store it in `self.lookup[gid]`, where `gid`
        is the guild id of `context`.

        :param context: Discord context.
        :type context: `discord.ext.commands.Context`

        :return: Instance of the factory
        """
        gid = context.guild.id

        self.logging.info(f"Starting {factory} instance for {gid}.")

        # create and return instance
        return factory(context)

    def _launch_threadsafe(self, instance) -> FactoryTask:
        """Run the `start` method of `instance` in a thread using `asyncio.run_coroutine_threadsafe`.

        :return: `FactoryTask` of `instance` and `future`, where the future contains the running threadsafe
            event loop.
        """
        loop = asyncio.get_event_loop()
        future = asyncio.run_coroutine_threadsafe(instance.start(), loop)

        return FactoryTask(instance, future)

    async def _start(self, context, factory):
        """Obtains the factory instance from `self.lookup` of Guild ID `gid`, and calls
        :func:`abstracts.egamefactory.EGameFactory.gather_players`.
        If `factory.min_players` is met, calls :func:`abstracts.egame.EGame.start`.
        """
        gid = context.guild.id

        # gather players
        instance = factory(context)
        player_count = await instance.gather_players()

        if player_count < instance.min_players:
            await context.channel.send(
                embed=self.embed(
                    f"Too few players to start game. Requires at least {factory.min_players}."
                )
            )
            return
        else:
            ft = self._launch_threadsafe(instance)
            ft.future.add_done_callback(
                self._remove_on_done(gid)
            )  # set to auto remove from `self.lookup` on completion

            # store in lookup
            self.lookup[gid] = ft

            self.logging.info(f"Started {factory} on {gid}")
            return

    def _remove_on_done(self, gid: int) -> Callable:
        """ Remove object associated with `gid` from `self.lookup` if associated future is done. """

        def _callback(future):
            # check for exceptions
            e = future.exception()
            if e:
                self.logging.exception("Exception in Game", exc_info=e)

            # remove self from lookup
            _ = self.lookup.pop(gid) if gid in self.lookup else None

        return _callback

    async def _entry(self, context, cmd: str, factory):
        """Cog command entry function, to be called from the derived class. Handles command
        and contexts.
        """
        self.logging.info(
            f"entry called for {factory} with {cmd} from guild {context.guild.name}"
        )

        gid = context.guild.id

        if cmd == "stop":
            if gid in self.lookup:
                # stop game
                self._stop(gid)
                return await context.send(embed=self.embed("Stopped running game."))
            else:
                return await context.send(embed=self.embed("No game running."))

        elif cmd == "start":
            if gid in self.lookup:
                return await context.send(
                    embed=self.embed("A game is already running on this server.")
                )

            else:
                # start game
                return await self._start(context, factory)

        elif cmd == "scrape":
            if factory.has_scrape:
                # good to scrape
                if gid in self.lookup:
                    instance = self.lookup[gid].instance
                else:
                    instance = factory(context)

                status = await instance.scrape(context)
                return await context.send(embed=self.embed(status))

            else:
                return await context.send(
                    embed=self.embed("Does not require scraping.")
                )

        else:
            # catch all
            await context.send(embed=self.embed("Unknown command."))

    async def cog_command_error(self, context, error):
        # pylint: disable=arguments-differ
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
