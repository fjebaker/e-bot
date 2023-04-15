from interactive.timedview import TimedView

from econfig import PLAYER_GATHER_TIMEOUT

import discord


class GatherPlayersView(TimedView):
    def __init__(self, embed):
        super().__init__(embed, timeout=PLAYER_GATHER_TIMEOUT)
        self.players = []
        self.text: str = embed.description

    async def _update_player_list(self):
        text = (
            self.text + "\n\nPlayers:\n- " + "\n- ".join((i.name for i in self.players))
        )
        await self.update_text(text)

    async def interaction_check(self, interaction: discord.Interaction):
        # don't let users with the same id interact twice
        is_playing = any((i.id == interaction.user.id for i in self.players))

        if is_playing:
            # let the player know they have already joined
            username = interaction.user.name
            await interaction.response.send_message(
                f"You have already joined.",
                ephemeral=True,
                delete_after=self.time,
            )
            return False

        return True

    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button):
        # append user
        self.players.append(interaction.user)
        await self._update_player_list()
        # keep listening for more events
        await interaction.response.defer()
