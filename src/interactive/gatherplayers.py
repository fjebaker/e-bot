import discord

from interactive.timedview import TimedView

from econfig import PLAYER_GATHER_TIMEOUT
from utils import random_emoji, async_context_wrap


class GatherPlayersView(TimedView):
    def __init__(self, embed):
        super().__init__(embed, timeout=PLAYER_GATHER_TIMEOUT)
        self.players = []
        self.text: str = embed.description

        btn = discord.ui.Button(
            label="Join", style=discord.ButtonStyle.green, emoji=random_emoji()
        )
        btn.callback = async_context_wrap(self, self.button_callback)
        self.add_item(btn)

    async def _update_player_list(self):
        text = (
            self.text
            + "\n\nPlayers:\n- "
            + "\n- ".join((f"{i.name} {symbol}" for (i, symbol) in self.players))
        )
        await self.update_text(text)

    async def interaction_check(self, interaction: discord.Interaction):  # pylint: disable=arguments-differ
        # don't let users with the same id interact twice
        is_playing = any((i.id == interaction.user.id for (i, _) in self.players))

        if is_playing:
            # let the player know they have already joined
            await interaction.response.send_message(
                "You have already joined.",
                ephemeral=True,
                delete_after=self.time,
            )
            return False

        return True

    async def button_callback(self, interaction: discord.Interaction):
        # append user
        self.players.append((interaction.user, random_emoji()))
        await self._update_player_list()
        # keep listening for more events
        await interaction.response.defer()
