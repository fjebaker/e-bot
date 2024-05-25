import logging

from typing import Dict, Tuple

import discord

from interactive.promptmodal import PromptModal
from interactive.userunique import UserUniqueView
from utils.lookups import EMOJI_FORWARD, random_emoji
from utils import async_context_wrap

logger = logging.getLogger(__name__)


class LashPrompt(discord.ui.View):
    def __init__(self, default_outcome: str, **kwargs):
        super().__init__(**kwargs)
        self.outcome: str = None
        self.default = default_outcome
        self.used_default = False

        enter_text_button = discord.ui.Button(
            label="Enter text", emoji=random_emoji(), style=discord.ButtonStyle.green
        )
        enter_text_button.callback = async_context_wrap(self, self.user_input)

        self.add_item(enter_text_button)

    @discord.ui.button(
        label="Safety",
        emoji=EMOJI_FORWARD["temperature"],
        style=discord.ButtonStyle.blurple,
    )
    async def safety(self, interaction: discord.Interaction, button):
        # pylint: disable=unused-argument
        self.outcome = None
        await self.resolve(interaction.message, interaction)

    async def user_input(self, interaction: discord.Interaction):
        modal = PromptModal()
        await interaction.response.send_modal(modal)
        # wait for response
        await modal.wait()

        self.outcome = modal.answer
        await self.resolve(interaction.message, modal.interaction)

    async def on_timeout(self):
        self.outcome = self.default
        self.used_default = True

    async def resolve(self, message: discord.Message, interaction: discord.Interaction):
        # pylint: disable=fixme,unused-argument
        # TODO: want to be able to delete old messages
        # but this doesn't work :/
        # await message.delete()

        if not self.outcome:
            # use default if no outcome yet given
            self.outcome = self.default
            text = f"Safety used: {self.outcome}"
            self.used_default = True
        else:
            text = f"Response submitted: {self.outcome}"

        await interaction.response.send_message(
            content=text, delete_after=10, ephemeral=True
        )
        self.stop()


class LashGetPromptView(UserUniqueView[Tuple[str, str], Tuple[str, bool]]):
    def __init__(self, embed, content: Dict[int, Tuple[str, str]], **kwargs):
        super().__init__(embed, "Get prompt", content, **kwargs)

    async def get_user_response(self, interaction: discord.Interaction, user_data: Tuple[str, str]):
        # tailor user specific modal with a timeout equal to time remaining
        content, default = user_data
        prompt = LashPrompt(default, timeout=self.time)
        await interaction.response.send_message(
            content=content, view=prompt, ephemeral=True, delete_after=self.time
        )
        await prompt.wait()

        logger.info(
            "User %s response: %d '%s'",
            interaction.user.name,
            prompt.used_default,
            prompt.outcome,
        )
        return (prompt.outcome, prompt.used_default)