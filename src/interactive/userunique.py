import logging

from typing import Dict, TypeVar, Generic

import discord

from interactive.timedview import TimedView
from utils.lookups import random_emoji
from utils import async_context_wrap

logger = logging.getLogger(__name__)

UserData = TypeVar("UserData")
ResponseData = TypeVar("ResponseData")


class UserUniqueView(TimedView, Generic[UserData, ResponseData]):
    def __init__(self, embed, title: str, content: Dict[int, UserData], **kwargs):
        super().__init__(embed, **kwargs)
        self.content = content
        self.responses: Dict[int, ResponseData] = {}
        self.interacted = []

        btn = discord.ui.Button(
            label=title, style=discord.ButtonStyle.green, emoji=random_emoji()
        )
        btn.callback = async_context_wrap(self, self.user_input)
        self.add_item(btn)

    def get_repeat_interaction_message(self, uid) -> str:
        # pylint: disable=unused-argument
        return "You've already responded"

    async def interaction_check(
        self, interaction: discord.Interaction
    ):  # pylint: disable=arguments-differ
        uid = interaction.user.id
        if uid in self.responses or uid in self.interacted:
            logger.info("User %s has already responded", interaction.user.name)
            await interaction.response.send_message(
                self.get_repeat_interaction_message(uid), ephemeral=True, delete_after=self.time + 1
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

    async def user_input(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user_data = self.content[uid]
        # Concrete implementation gets the response
        response = await self.get_user_response(interaction, user_data)
        if response is not None:
            self.responses[uid] = response
        self.check_continue()

    # override
    async def get_user_response(
        self, interaction: discord.Interaction, user_data: UserData
    ) -> ResponseData:
        """Callback for when a user interacts with the button"""
        # pylint: disable=unused-argument,unnecessary-ellipsis
        ...

    def required_responses(self) -> int:
        return len(self.content)

    def check_continue(self):
        if len(self.responses) == self.required_responses():
            logger.info("All users responded to prompt")
            # stop the timer
            self.time = 1
