import logging
import random

from typing import Dict, List, Tuple

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
                style=discord.ButtonStyle.gray,
            )
            button.callback = self.generate_callback(index, card)
            self.add_item(button)

    def generate_callback(self, index: int, card: str):
        async def _callback(interaction: discord.Interaction):
            return await self.on_button_press(interaction, index, card)

        return _callback

    async def on_button_press(
        self, interaction: discord.Interaction, index: int, card: str
    ):
        self.display_response = card
        self.result = index
        await self.resolve(interaction)

    async def resolve(self, interaction: discord.Interaction):
        text = f"{self.resolve_text}: {self.display_response}"

        await interaction.response.send_message(
            content=text, delete_after=10, ephemeral=True
        )
        self.stop()


class SafetyCardsPrompt(CardsPrompt):
    def __init__(self, resolve_text: str, hand: List[str], safety: str, **kwargs):
        super().__init__(resolve_text, hand, **kwargs)
        self.hand = hand
        self.redraw = False

        safety_button = discord.ui.Button(
            label="Play safety",
            emoji=EMOJI_FORWARD["temperature"],
            style=discord.ButtonStyle.blurple
        )
        safety_button.callback = self.generate_callback(len(hand), safety)
        self.add_item(safety_button)

        redraw_button = discord.ui.Button(
            label="Re-draw hand",
            emoji=EMOJI_FORWARD["reverse"],
            style=discord.ButtonStyle.danger
        )
        redraw_button.callback = self.on_redraw_press
        self.add_item(redraw_button)

    async def on_redraw_press(self, interaction: discord.Interaction):
        index = random.choice(range(len(self.hand)))
        self.display_response = self.hand[index]
        self.result = index
        self.redraw = True
        self.resolve_text = "Redrawing hand.\nSelected random response"
        await self.resolve(interaction)


class CardsGetPromptView(UserUniqueView[List[str], Tuple[int,bool]]):
    def __init__(
        self, embed, title: str, prompt: str, leader: int, content: Dict[int, List[str]], **kwargs
    ):
        # pylint: disable=too-many-arguments
        super().__init__(embed, "Select card", content, **kwargs)
        self.title = title
        self.leader = leader
        self.prompt = prompt

    async def get_user_response(
        self, interaction: discord.Interaction, user_data: List[str]
    ) -> Tuple[int,bool]:
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
        visible_hand = hand[:-1]
        safety = hand[-1]
        prompt = SafetyCardsPrompt("Result selected", visible_hand, safety, timeout=self.time)
        message_content = f"**{self.prompt}**\nSelect a card!\n" + "\n".join(
            f"{EMOJI_FORWARD[index + 1]}: {card}" for index, card in enumerate(visible_hand)
        )
        await interaction.response.send_message(
            content=message_content, view=prompt, ephemeral=True, delete_after=self.time
        )
        await prompt.wait()

        logger.info(
            "User %s response: '%s'",
            interaction.user.name,
            prompt.result,
        )
        return (prompt.result, prompt.redraw)

    def required_responses(self) -> int:
        return len(self.content) - 1  # Exclude leader


class CardsSelectWinningPromptView(
    UserUniqueView[List[Tuple[str, int]], Tuple[str, int]]
):
    def __init__(
        self, embed, leader: int, content: Dict[int, List[Tuple[str, int]]], **kwargs
    ):
        super().__init__(embed, "Select winner", content, **kwargs)
        self.leader = leader

    def get_repeat_interaction_message(self, uid) -> str:
        if (uid != self.leader):
            return "Only the leader can vote for the winning answer"
        else:
            return super().get_repeat_interaction_message(uid)

    async def get_user_response(
        self, interaction: discord.Interaction, user_data: List[Tuple[str, int]]
    ) -> Tuple[str, int]:
        uid = interaction.user.id
        if uid != self.leader:
            await interaction.response.send_message(
                "Only the leader can vote for the winning answer",
                ephemeral=True,
                delete_after=self.time,
            )
            return None

        # tailor user specific modal with a timeout equal to time remaining
        prompt = CardsPrompt(
            "Winner selected", [k for (k, _) in user_data], timeout=self.time
        )
        await interaction.response.send_message(
            content="Select a winner",
            view=prompt,
            ephemeral=True,
            delete_after=self.time,
        )
        await prompt.wait()

        logger.info(
            "Leader %s selected winner: '%s'",
            interaction.user.name,
            prompt.result,
        )
        return user_data[prompt.result]

    def required_responses(self) -> int:
        return 1
