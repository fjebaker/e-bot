import logging
from types import FunctionType

import discord

import asyncio
import random
import os
from collections import defaultdict

from utils import Clock
from utils.lookups import EMOJI_FORWARD, EMOJI_BACKWARD

from econfig import PATH_EXTENSION


def replace_rules(content: str) -> str:
    """TODO"""
    return content.replace("{blank}", "_" * 5).replace(
        "{the current year}", "the current year"
    )


class EGameFactory:
    """E Game Factory Superclass

    To be inherited by subclassing game cogs, providing basic interaction
    such as polling, player and context management, scores, etc..

    Channel messaging:
    Provides a number of prefabricated interaction settings, such as
        POLL    - for vote based interaction
        REPLY   - for text based interaction
        CHOICE  - for reaction vote on options (default: for up to 5 choices)

    Direct messaging:
        DM_TEXT
        DM_IMAGE
    """

    # prefabs
    POLL = {
        "type": "reaction",
        "emojis": [EMOJI_FORWARD["up-arrow"], EMOJI_FORWARD["down-arrow"]],
        "usercomplete": True,  # wait until all users have voted
        "timeout": 15,  # timeout, seconds
        "minvotes": 1,  # minimum votes needed before continuing
    }

    REPLY = {"type": "reply", "usercomplete": True, "timeout": 5}

    @staticmethod
    def CHOICE(options: dict) -> dict:
        """Method for generating choice interaction dictionaries. Options should be a
        emoji key indexed dictionary mapping to the associated choice value.
        """
        emojis = [EMOJI_FORWARD[k] for k, v in options.items()]
        return {
            "type": "reaction",
            "usercomplete": True,
            "timeout": 15,
            "choices": options,
            "emojis": emojis,
        }

    DM_TEXT = {"type": "dmtext", "timeout": 30}
    DM_IMAGE = {"type": "dmimage", "timeout": 45}

    def __init__(self, context, logger_name: str):
        """
        `logger_name` should just be `__name__` of instancing module. Used
        only for logging purposes.
        """
        self.logging = logging.getLogger(logger_name)

        self.guild = context.guild
        self.channel = context.channel

        # players property
        self._players = {}  # index by id
        self._num_players = 0

        # state
        self.state = {
            "running": False,
            "scores": defaultdict(int),
        }  # scores index pid -> score

        # adjust file locations
        for file_path in [attr for attr in dir(self) if attr.startswith("file_")]:
            self.__setattr__(
                file_path,
                os.path.join(
                    PATH_EXTENSION,
                    self.__getattribute__(file_path).format(gid=self.guild.id),
                ),
            )

    def embed(self, text: str, **kwargs):
        """Convenience method for creating `discord.Embed`s.

        :param text: Text to insert in the `description` of the embed object.

        :return: The embed instance
        :rtype: discord.Embed
        """
        return discord.Embed(
            title=self.game_name,
            description=text,
            colour=discord.Colour.blue(),
            **kwargs,
        )

    def _add_score(self, value: int, pid: int):
        """TODO"""
        self.logging.info(f"Adding score {value} for player {pid}")
        self.state["scores"][pid] += value

    @staticmethod
    def _read_file(path: str) -> str:
        """Utility method for reading in scraped files. Scraped files
        are always assumed to be new-line seperated.

        :param path: Path to the file

        :return: Content of the file
        """
        data = None
        with open(path, "r") as f:
            data = f.read().split("\n")
        return data

    @property
    def players(self) -> dict:
        """Players property getter"""
        return self._players

    @players.setter
    def players(self, players: dict):
        """Players property setter"""
        self._players = players
        self._num_players = len(players.keys())

    async def _add_reaction_interaction(self, message, interaction: dict):
        """Internal method for adding emoji-reaction to a message."""
        for emoji in interaction["emojis"]:
            await message.add_reaction(emoji)

        # exploit closure
        async def callback(rt):
            count = 0

            i = await self.channel.fetch_message(message.id)
            count = sum(
                map(
                    lambda x: x.count if x.emoji in interaction["emojis"] else 0,
                    i.reactions,
                )
            )

            # get embed
            em = i.embeds[0]

            # checks
            count -= len(interaction["emojis"])
            if interaction["usercomplete"] and count >= len(self.players):
                em.set_footer(text="Everyone voted.")
                await i.edit(embed=em)
                return True

            # update remaining time counter
            em.set_footer(text=f"\nTime Remaining: {rt}s")
            await i.edit(embed=em)

            return False

        timer = Clock(interaction["timeout"], callback)
        await timer.start()

        # final update
        message = await self.channel.fetch_message(message.id)

        # tally result
        reactions = {i.emoji: i.count - 1 for i in message.reactions}
        # decode emojis back into internal representation
        result = {
            EMOJI_BACKWARD[emoji]: reactions[emoji] for emoji in interaction["emojis"]
        }

        return result

    async def _add_reply_interaction(self, message, interaction):
        """Internal method"""
        # get embed
        em = message.embeds[0]
        replies = list()

        async def callback(rt):
            em.set_footer(text=f"Reply to this message. \nTime Remaining: {rt}s")
            await message.edit(embed=em)

            # read in replies
            async for i in message.channel.history(limit=100):
                # if reading messages before bot message, break
                if i.id == message.id:
                    break

                if (
                    i.reference
                    and i.reference.resolved.id == message.id
                    and i not in replies
                ):
                    self.logging.info(f"Reply to {message.id}: {i.author}: {i.content}")
                    replies.append(i)
                    await i.add_reaction(EMOJI_FORWARD["checkmark"])

        # do clock
        timer = Clock(interaction["timeout"], callback)
        await timer.start()

        # unpack replies
        result = {i.author.id: i for i in replies}
        self.logging.info(result)
        return result

    async def _add_choices_to_message(self, message, choices):
        """Internal method for adding numerical choices to a message embed."""
        em = message.embeds[0]
        for k, v in choices.items():
            em.add_field(name=str(k), value=v, inline=False)
        await message.edit(embed=em)

    async def _add_interaction(self, message, interaction, **kwargs) -> dict:
        """Internal method for adding interaction to messages."""
        if interaction["type"] == "reaction":
            if interaction.get("choices", False):
                await self._add_choices_to_message(message, interaction["choices"])
            return await self._add_reaction_interaction(message, interaction)
        elif interaction["type"] == "reply":
            return await self._add_reply_interaction(message, interaction)
        else:
            self.logging.error(f"Unknown interaction type {interaction['type']}")

    def _dm_reply_factory(self, message, pid: int) -> FunctionType:
        """Internal factory method for generating proper asynchronous closure capture.

        :return: Direct message reading callback function.
        """

        # get embed
        em = message.embeds[0]

        async def _read_dm(rt):
            # self.logging.info(f" - closure {pid}: {message.id}")
            em.set_footer(
                text=f"Message to this DM with your response. \nTime Remaining: {rt}"
            )
            await message.edit(embed=em)

            async for i in message.channel.history(limit=5):
                # don't read messages before bot message
                if i.id == message.id:
                    break

                # do checks on messages here (type enforcement, length, etc)
                self.logging.info(f"DM reply: {i.content}")

                await i.add_reaction(EMOJI_FORWARD["checkmark"])

                # wrap up and return
                em.set_footer(text=f"Message to this DM with your response.")
                await message.edit(embed=em)

                return (pid, i)

        return _read_dm

    async def _get_dm_replies(self, messages: dict, interaction: dict) -> dict:
        """Internal method

        :return: Reply messages indexed by player id.
        """

        tasks = []
        for pid, message in messages.items():
            self.logging.info(f"Creating DM hook for {self.players[pid]}")

            # abuse closure again
            _read_dm = self._dm_reply_factory(message, pid)

            timer = Clock(interaction["timeout"], _read_dm, default_return=(pid, None))
            tasks.append(timer.start())

        replies = await asyncio.gather(*tasks, return_exceptions=False)

        self.logging.info(replies)

        # unpack to dict
        if replies:
            return {i[0]: i[1] for i in replies}
        else:
            return {}

    async def dm_players(
        self, content: dict, player_ids: list, interaction=None
    ) -> dict:
        """Convenience method to send a message to a list of players.

        :param content: Embed content to send.
        :param player_ids: List of player ids to send message to.
        :param interaction: Interaction specification
        :type interaction: `dict`, or `None`

        :return: Reply dictionary if interaction present, else `None`."""
        unique_content = {pid: content for pid in player_ids}
        return await self.dm_players_unique(unique_content, interaction=interaction)

    async def dm_players_unique(self, unique_content: dict, interaction=None) -> dict:
        """DM unique content to each player, indexed by player id.

        :param unique_content: Embed content to send to player, indexed by the
        player id.
        :param interaction: Interaction specification
        :type interaction: `dict`, or `None`

        :return: Reply dictionary if interaction present, else `None`.
        """
        messages = {}
        for pid, content in unique_content.items():
            i = await self.players[pid].send(**content)
            messages[pid] = i

        if interaction:
            replies = await self._get_dm_replies(messages, interaction)
            return replies
        else:
            return None

    async def dm_all_players(self, content: dict, interaction=None) -> dict:
        """Convenience method to send a message to all players in the game.

        :param content: Embed content to send.
        :param interaction: Interaction specification
        :type interaction: `dict`, or `None`

        :return: Reply dictionary if interaction present, else `None`.
        """
        self.logging.info(f"DMing all players in {self.guild}")
        return await self.dm_players(
            content, self.players.keys(), interaction=interaction
        )

    async def menu(self, content: dict, interaction=None, channel=None) -> dict:
        """Used to create menus in `self.channel` or `channel` kw if specified.
        Menus are embeds with optional emoji interactions.

        :param content: Content to use in the Embed; unpacked as keywords for the
        `discord.Embed` function
        :param interaction: Interaction specification
        :type interaction: `dict`, or `None`
        :param channel: The channel to send the menu to. Defaults to the context channel.
        :type channel: `discord.TextChannel`

        :return: dictionary with the menu message instance, and optionally the interaction
        result.
        """
        menu = discord.Embed(**content)

        if channel:
            message = await channel.send(embed=menu)
        else:
            message = await self.channel.send(embed=menu)

        if interaction is not None:
            respones = await self._add_interaction(message, interaction)
            return dict(response=respones, message=message)

        return dict(message=message)

    async def titlemenu(self, text: str, interaction=None) -> dict:
        """Convenience function for creating a title menu"""
        return await self.menu(
            {
                "title": self.game_name,
                "description": text,
                "colour": discord.Colour.blue(),
            },
            interaction=interaction,
        )

    async def _players_prompt(self) -> dict:
        """Creates a discord embed menu, which players are told to reply to if they
        want to join the game. Extracts the discord author instance, and returns a
        dictionary mapping:

            id -> author

        :return: Authors indexed by id.
        """
        replies = await self.menu(
            {
                "title": self.game_name,
                "description": f"{self.game_description}\n\nReply to this message to join the game.",
                "colour": discord.Colour.blue(),
            },
            interaction=self.REPLY,
        )

        return {k: v.author for (k, v) in replies["response"].items()}

    async def announce_ranking(self, result: list):
        """Presents the ranking of scores in `results` in a discord embed in the
        public channel of the guild.

        :param result: List of  `(num votes: int, pid: int)` tuples.
        """
        scoreboard = "Scores for this round:\n" + "\n".join(
            [f"{votes} votes for {self.players[pid]}" for votes, pid in result]
        )

        await self.channel.send(embed=self.embed(scoreboard))
        await asyncio.sleep(self.wait_duration)

    async def scoreboard(self):
        """TODO"""
        self.logging.info(self.state)
        tallied_scores = self.state["scores"]

        scores = sorted(
            [(pid, tallied_scores[pid]) for pid in self.players.keys()],
            key=lambda i: i[1],
        )
        scoreboard = [
            f"{i+1}. {self.players[t[0]]}: {t[1]}" for i, t in enumerate(scores)
        ]
        await self.channel.send(
            embed=self.embed("**Global Scores:**\n" + "\n".join(scoreboard))
        )

    # override
    async def stop(self):
        """Stop game"""
        ...

    # override
    async def start(self):
        """Main entry"""
        ...

    # override
    async def scrape(self, context) -> str:
        ...

    async def _scrape_channel(self, context, channel_name: str, file_name: str) -> int:
        """TODO"""
        channel = next(filter(lambda c: c.name == channel_name, context.guild.channels))

        message_contents = []

        async for message in channel.history(limit=1000):
            try:
                message_contents.append(replace_rules(message.content))
            except Exception as e:
                self.logging.error(
                    f"Scraping error on {channel_name} in {context.guild.id}: {e}"
                )
                return f"Scraping error {e}."

        with open(file_name, "w") as f:
            f.write("\n".join(message_contents))
        return len(message_contents)

    async def gather_players(self) -> int:
        """Creates a player registration prompt, and returns the number of players
        that replied

        :return: Number of players registered.
        """
        self.logging.info("Calling gather players.")
        self.players = await self._players_prompt()

        self.logging.info(f"number of players {self._num_players}")

        return self._num_players
