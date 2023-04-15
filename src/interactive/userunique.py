import logging

from typing import Dict, Tuple

import discord

from interactive.timedview import TimedView

logger = logging.getLogger(__name__)


class PromptModal(discord.ui.Modal, title="e-bot"):
    response = discord.ui.TextInput(label="Answer")

    async def on_submit(self, interaction: discord.Interaction):
        self.stop()
        self.interaction = interaction
        self.answer = self.response.value


class UserPrompt(discord.ui.View):
    def __init__(self, default_outcome: str, **kwargs):
        super().__init__(**kwargs)
        self.outcome: str = None
        self.default = default_outcome
        self.used_default = False

    @discord.ui.button(label="Safety")
    async def safety(self, interaction: discord.Interaction, button):
        self.outcome = None
        await self.resolve(interaction.message, interaction)

    @discord.ui.button(label="Enter text")
    async def user_input(self, interaction: discord.Interaction, button):
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


class UserUniqueView(TimedView):
    def __init__(self, embed, content: Dict[int, Tuple[str, str]], **kwargs):
        super().__init__(embed, **kwargs)
        self.content = content
        self.responses = {}
        self.interacted = []

    async def interaction_check(self, interaction: discord.Interaction):
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

    @discord.ui.button(label="Get prompt")
    async def user_input(self, interaction: discord.Interaction, button):
        uid = interaction.user.id

        # tailor user specific modal with a timeout equal to time remaining
        content, default = self.content[uid]
        prompt = UserPrompt(default, timeout=self.time)
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
        self.check_continue()

    def check_continue(self):
        if len(self.responses) == len(self.content):
            logger.info("All users responded to prompt")
            # stop the timer
            self.time = 1
