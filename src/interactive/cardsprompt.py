import logging

from typing import Dict, List

import discord

from interactive.userunique import UserUniqueView
from utils.lookups import EMOJI_FORWARD

logger = logging.getLogger(__name__)


class CardsPrompt(discord.ui.View):
    def __init__(self, resolve_text: str, hand: List[str], **kwargs):
        super().__init__(**kwargs)
        self.result: int = None
        self.display_response: str = None
        self.resolve_text = resolve_text

        for index, card in enumerate(hand):
            button = discord.ui.Button(
                label="",
                emoji=EMOJI_FORWARD[index + 1],
                style=discord.ButtonStyle.green
            )
            button.callback = self.generate_callback(index, card)
            self.add_item(button)

    def generate_callback(self, index: int, card: str):
        async def _callback(interaction: discord.Interaction):
            return await self.on_button_press(interaction, index, card)

        return _callback

    async def on_button_press(self, interaction: discord.Interaction, index: int, card: str):
        self.display_response = card
        self.result = index
        await self.resolve(interaction)

    async def resolve(self, interaction: discord.Interaction):
        text = f"{self.resolve_text}: {self.display_response}"

        await interaction.response.send_message(
            content=text, delete_after=10, ephemeral=True
        )
        self.stop()


class CardsGetPromptView(UserUniqueView[List[str], int]):
    def __init__(self, embed, title: str, leader: int, content: Dict[int, List[str]], **kwargs):
        super().__init__(embed, "Select card", content, **kwargs)
        self.title = title
        self.leader = leader

    async def get_user_response(self, interaction: discord.Interaction, user_data: List[str]):
        uid = interaction.user.id
        if uid == self.leader:
            await interaction.response.send_message(
                "You are the leader for this round! Sit back and relax!",
                ephemeral=True,
                delete_after=self.time,
            )
            return None

        # tailor user specific modal with a timeout equal to time remaining
        hand = user_data
        prompt = CardsPrompt("Result selected", hand, timeout=self.time)
        message_content = "Select a card!\n" + '\n'.join(f"{EMOJI_FORWARD[index + 1]}: {card}" for index, card in enumerate(hand))
        await interaction.response.send_message(
            content=message_content, view=prompt, ephemeral=True, delete_after=self.time
        )
        await prompt.wait()

        logger.info(
            "User %s response: '%s'",
            interaction.user.name,
            prompt.result,
        )
        return prompt.result

    def required_responses(self) -> int:
        return len(self.content) - 1  # Exclude leader


class CardsSelectWinningPromptView(UserUniqueView[List[str], int]):
    def __init__(self, embed, leader: int, content: Dict[int, List[str]], **kwargs):
        super().__init__(embed, "Select winner", content, **kwargs)
        self.leader = leader

    async def get_user_response(self, interaction: discord.Interaction, user_data: List[str]):
        uid = interaction.user.id
        if uid != self.leader:
            await interaction.response.send_message(
                "Only the leader can vote for the winning answer",
                ephemeral=True,
                delete_after=self.time,
            )
            return None

        # tailor user specific modal with a timeout equal to time remaining
        prompt = CardsPrompt("Winner selected", user_data, timeout=self.time)
        await interaction.response.send_message(
            content="Select a winner", view=prompt, ephemeral=True, delete_after=self.time
        )
        await prompt.wait()

        logger.info(
            "Leader %s selected winner: '%s'",
            interaction.user.name,
            prompt.result,
        )
        return prompt.result

    def required_responses(self) -> int:
        return 1