import logging

from typing import Dict, Tuple

import discord

from interactive.selection import TimedView

logger = logging.getLogger(__name__)


class PromptModal(discord.ui.Modal, title="e-bot"):
    def __init__(self, content):
        super().__init__()
        self.response = discord.ui.TextInput(label=content)
        self.add_item(self.response)

    async def on_submit(self, interaction: discord.Interaction):
        self.stop()
        self.interaction = interaction


class UserPrompt(discord.ui.View):
    def __init__(self, content, default_outcome: str, **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.outcome: str | None = None
        self.default = default_outcome
        self.used_default = False

    @discord.ui.button(label="Safety")
    async def safety(self, interaction: discord.Interaction, button):
        self.outcome = None
        await self.resolve(interaction.message, interaction)

    @discord.ui.button(label="Enter text")
    async def user_input(self, interaction: discord.Interaction, button):
        modal = PromptModal(self.content)
        await interaction.response.send_modal(modal)
        # wait for response
        await modal.wait()

        self.outcome = modal.response.value
        await self.resolve(interaction.message, modal.interaction)

    async def on_timeout(self):
        self.outcome = self.default
        self.used_default = True

    async def resolve(
        self, message: discord.Message | None, interaction: discord.Interaction
    ):
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

        await interaction.response.send_message(content=text, delete_after=10)
        self.stop()


class UserUniqueView(TimedView):
    def __init__(self, embed, content: Dict[int, Tuple[str, str]], **kwargs):
        super().__init__(embed, **kwargs)
        self.content = content
        self.responses = {}

    @discord.ui.button(label="Get prompt")
    async def user_input(self, interaction: discord.Interaction, button):
        uid = interaction.user.id

        if uid in self.responses:
            logger.info("User %s has already respondend", interaction.user.name)
            await interaction.response.send_message(
                "You've already responded", ephemeral=True, delete_after=self.time + 1
            )

        elif uid in self.content:
            logger.info("User %s asked for prompt", interaction.user.name)
            # tailor user specific modal with a timeout equal to time remaining
            content, default = self.content[uid]
            prompt = UserPrompt(content, default, timeout=self.time)
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
            self.responses[uid] = (prompt.outcome, prompt.used_default)
        else:
            logger.info("User %s is not playing", interaction.user.name)
            await interaction.response.send_message(
                "Sorry, you're not registered as a player right now.",
                ephemeral=True,
                delete_after=self.time + 1,
            )
