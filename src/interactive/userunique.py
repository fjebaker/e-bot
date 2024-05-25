import logging

from typing import Dict, Tuple, TypeVar, Generic

import discord

from interactive.timedview import TimedView
from utils.lookups import random_emoji
from utils import async_context_wrap

logger = logging.getLogger(__name__)

UserData = TypeVar("UserData")

class UserUniqueView(TimedView, Generic[UserData]):
    def __init__(self, embed, title: str, content: Dict[int, UserData], **kwargs):
        super().__init__(embed, **kwargs)
        self.content = content
        self.responses = {}
        self.interacted = []

        btn = discord.ui.Button(
            label="Get prompt", style=discord.ButtonStyle.green, emoji=random_emoji()
        )
        btn.callback = async_context_wrap(self, self.user_input)
        self.add_item(btn)

    async def interaction_check(
        self, interaction: discord.Interaction
    ):  # pylint: disable=arguments-differ
        uid = interaction.user.id
        if uid in self.responses or uid in self.interacted:
            logger.info("User %s has already respondend", interaction.user.name)
            await interaction.response.send_message(
                "You've already responded", ephemeral=True, delete_after=self.time + 1
            )
            return False
        elif uid in self.content:
            logger.info("User %s asked for prompt", interaction.user.name)
            self.interacted.append(uid)
            return True
        else:
            logger.info("User %s is not playing", interaction.user.name)
            await interaction.response.send_message(
                "Sorry, you're not registered as a player right now.",
                ephemeral=True,
                delete_after=self.time + 1,
            )
            return False

    # override
    async def user_input(self, interaction: discord.Interaction):
        """Callback for when a user interacts with the button"""
        # pylint: disable=unnecessary-ellipsis
        ...

    def check_continue(self):
        if len(self.responses) == len(self.content):
            logger.info("All users responded to prompt")
            # stop the timer
            self.time = 1