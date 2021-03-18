import logging

import discord
from discord.ext import commands

import asyncio


class GameCog(commands.Cog):
    """Superclass for creating cogs for game instance management. Creates a lookup
    dictionary, indexed by guild id, to seperate game instances.

    Derived classes should define
    - `self.game_name` (`str`)
    - `self.min_players` (`int`)
    - `self.factory` (`class`), used to generate new game instances
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
        self.game_name = ""
        self.min_players = 0
        self.factory = None  # class which creates instances of EGame
        self.cog_help = ""
        self.has_scrape = False

        # class internals
        self.lookup = {}  # lookup game states by guild id

    def embed(self, text: str):
        """Convenience method for creating `discord.Embed`s.

        :param text: Text to insert in the `description` of the embed object.

        :return: The embed instance
        :rtype: discord.Embed
        """
        return discord.Embed(
            title=self.game_name, description=text, colour=discord.Colour.red()
        )

    async def _stop(self, gid: int):
        """Stops the game instance running on the guild with id `gid`, and removes
        the instance in the lookup dictionary (so that it is GC'd).

        :param gid: Guild ID
        """
        await self.lookup[gid].stop()
        self.lookup.pop(gid)

    async def _start(self, context):
        """Start a new game instance for the current context. That is to say, will
        create a `self.factory` instance and store it in `self.lookup[gid]`, where `gid`
        is the guild id of `context`.

        Calls :func:`.GameCog._restart`.

        :param context: Discord context.
        :type context: `discord.ext.commands.Context`
        """
        gid = self.context.guild.id

        # create and store instance
        self.lookup[gid] = self.factory(context)

        # same interface method
        return await self._restart(gid)

    async def _restart(self, gid: int):
        """Obtains the factory instance from `self.lookup` of Guild ID `gid`, and calls
        :func:`abstracts.egame.EGame.gather_players`.
        If `self.min_players` is met, calls :func:`abstracts.egame.EGame.start`.
        """
        instance = self.lookup[gid]

        # gather players
        player_count = await instance.gather_players()

        if player_count < self.min_players:
            return await context.send(
                embed=self.embed(
                    f"Too few players to start game. Requires at least {self.min_players}."
                )
            )
        else:
            return await instance.start()

    async def _entry(self, context, cmd: str):
        """Cog command entry function, to be called from the derived class. Handles command
        and contexts.
        """
        self.logging.info(f"entry called with {cmd} from guild {context.guild.name}")

        # check if state for guild exists
        if context.guild.id in self.lookup:

            # restarting
            if cmd == "start":
                await self._restart(context.guild.id)

            # stops must be handled externally
            if cmd == "stop":
                await self._stop(context.guild.id)

        # scraping must be a staticmethod
        elif cmd == "scrape":

            if self.has_scrape:
                await self.factory.scrape(context)

            else:
                await context.send(embed=self.embed("Does not require scraping."))

        # new instances
        elif cmd == "start":
            await self._start(context)

        # info catches
        elif cmd == "stop":
            await context.send(embed=self.embed("No game running."))
        else:
            await context.send(embed=self.embed("Unknown command."))

        ## OLD CODE

        if self.state["running"] == False and cmd == "start":
            # start game
            self.channel = context.channel
            players = await self.newplayers(
                self.game_name,
                descr=f"**{context.author.name}** wants to start a new **{self.game_name}** game.\nRequires at least 3 players.",
            )
            if len(players) < self.min_players:
                ...
            elif self._has_prompts() == False:
                await context.send(
                    embed=self.embed("No prompts found. Run the scrape command first.")
                )
            else:
                self.state["running"] = True
                await self.execute_round()

        elif cmd == "stop":
            # stop game
            if self.state["running"]:
                self.state["running"] = False
                await context.send(embed=self.embed("Game stopped."))
            else:
                await context.send(embed=self.embed("No game running."))

        elif self.state["running"] == False and cmd == "scrape":
            number_prompts = await self._scrape_prompts(context)
            await context.send(embed=self.embed(f"Scraped {number_prompts} prompts."))
        else:
            await context.send(embed=self.embed("Unknown command."))

    async def cog_command_error(self, context, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await context.send(f"Missing Argument!\n{self.cog_help}")
        else:
            raise error
