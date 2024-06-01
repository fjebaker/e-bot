import discord


class PromptModal(discord.ui.Modal, title="e-bot"):
    response = discord.ui.TextInput(label="Answer")

    async def on_submit(self, interaction: discord.Interaction):
        # pylint: disable=arguments-differ,attribute-defined-outside-init
        self.stop()
        self.interaction = interaction
        self.answer = self.response.value
