import logging

import discord
from discord.ext import commands

import asyncio
import random
import re

from utils import Clock

CHECKMARK = "\U00002611"


class EGame(commands.Cog):
    """E Game Cog

    To be inherited by subclassing game cogs, providing basic interaction
    such as polling, player and context management, scores, etc..

    Channel messaging:
    Provides a number of prefabricated interaction settings, such as
        POLL    - for vote based interaction
        REPLY   - for text based interaction

    Direct messaging:

    """

    # prefabs
    POLL = {
        "type": "reaction",
        "emojis": [
            "\U00002B06",
            "\U00002B07",
            "\U000021A9",
            "\U00002934",
            "\U0001F504",
        ],
        "usercomplete": True,  # wait until all users have voted
        "timeout": 10,  # timeout,
        "minvotes": 1,  # minimum votes needed before continuing
    }

    REPLY = {"type": "reply", "usercomplete": True, "timeout": 15}

    DM_TEXT = {"type": "dmtext", "timeout": 10}
    DM_IMAGE = {"type": "dmimage", "timeout": 10}

    def __init__(self, bot, logger_name):
        """
        `logger_name` should just be `__name__` of instancing module. Used
        only for logging purposes.
        """
        self.bot = bot
        self.logging = logging.getLogger(logger_name)

        self.channel = None
        self.players = {}  # index by id
        self.state = {}

    async def _add_reaction_interaction(self, message, interaction):
        """Method for adding emoji-reaction to a message."""
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
            # update remaining time counter
            em = i.embeds[0]
            em.set_footer(text=f"\nTime Remaining: {rt}s")
            await i.edit(embed=em)

            count -= len(interaction["emojis"])
            # return count >= interaction["minvotes"]

        timer = Clock(interaction["timeout"], callback)
        await timer.start()

        # final update
        message = await self.channel.fetch_message(message.id)

        # tally result
        reactions = {i.emoji: i.count for i in message.reactions}
        result = {emoji: reactions[emoji] for emoji in interaction["emojis"]}

        # self.logging.info(result)
        await self.channel.send(str(result))
        return result

    async def _add_reply_interaction(self, message, interaction):
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
                    await i.add_reaction(CHECKMARK)

        # do clock
        timer = Clock(interaction["timeout"], callback)
        await timer.start()
        # unpack replies

        result = {i.author.id: i for i in replies}
        self.logging.info(result)
        return result

    async def _add_interaction(self, message, interaction, **kwargs):
        if interaction["type"] == "reaction":
            return await self._add_reaction_interaction(message, interaction)
        elif interaction["type"] == "reply":
            return await self._add_reply_interaction(message, interaction)
        else:
            self.logging.error(f"Unknown interaction type {interaction['type']}")

    async def _get_dm_replies(self, messages, interaction):
        tasks = []

        def factory(message, pid):
            em = message.embeds[0]

            self.logging.info(f" - factory {pid}: {message.id}")

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

                    # do checks on messages here (type enforcement, etc)
                    self.logging.info(f"DM reply: {i.content}")

                    await i.add_reaction(CHECKMARK)

                    # wrap up and return
                    em.set_footer(text=f"Message to this DM with your response.")
                    await message.edit(embed=em)

                    return (pid, i)

            return _read_dm

        for pid, message in messages.items():
            self.logging.info(f"Creating DM hook for {self.players[pid]}")

            # abuse closure again
            _read_dm = factory(message, pid)

            timer = Clock(interaction["timeout"], _read_dm)
            tasks.append(timer.start())

        replies = await asyncio.gather(*tasks, return_exceptions=True)

        # unpack to dict
        if replies:
            return {i[0]: i[1] for i in replies}
        else:
            return {}

    async def _dm_all_players(self, content: dict, interaction=None):
        messages = {}
        for pid, player in self.players.items():
            i = await player.send(**content)
            messages[pid] = i

        if interaction:
            replies = await self._get_dm_replies(messages, interaction)
            return replies
        else:
            return None

    async def menu(self, content: dict, interaction=None, channel=None):
        """Used to create menus in `self.channel` or `channel` kw if specified.
        Menus are embeds with optional emoji interactions.
        """

        menu = discord.Embed(**content)

        if channel:
            message = await channel.send(embed=menu)
        else:
            message = await self.channel.send(embed=menu)

        if interaction is not None:
            return await self._add_interaction(message, interaction)

        else:
            return message

    async def titlemenu(self, title, text, interaction=None):
        """Convenience function for creating a tile menu"""
        return await self.menu(
            {"title": title, "description": text, "colour": discord.Colour.red()},
            interaction=interaction,
        )

    async def newplayers(self, title):
        replies = await self.menu(
            {
                "title": title,
                "description": "Reply to this message to join the game.",
                "colour": discord.Colour.blue(),
            },
            interaction=self.REPLY,
        )

        players = {k: v.author for (k, v) in replies.items()}
        self.players = players
        return players

    async def dm_prompt(self, prompt):
        ...
