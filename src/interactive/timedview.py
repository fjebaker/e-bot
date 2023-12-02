import asyncio
import logging

import discord

logger = logging.Logger(__name__)


class TimedView(discord.ui.View):
    TIME_FMT = "Time remaining: {}s"

    def __init__(self, embed: discord.Embed, timeout=15, delete_after=False, **kwargs):
        # don't pass the timeout up to superclass
        # since we want to monitor this ourselves
        super().__init__(**kwargs)

        self.embed: discord.Embed = embed
        self.time = timeout
        self._is_complete = False
        self.delete_after = delete_after

        self.message: discord.Message = None

    async def send_and_wait(self, channel: discord.TextChannel):
        self.embed.set_footer(text=self.TIME_FMT.format(self.time))
        self.message = await channel.send(embed=self.embed, view=self)

        while self.time > 0:
            await asyncio.sleep(1.0)
            # update timer
            self.time -= 1
            await self._update_embed()

        self.stop()
        # remove the UI
        await self.message.edit(view=None)
        await self.on_timeout()

        if self.delete_after == True:
            await self.message.delete()

    async def update_text(self, s: str):
        self.embed.description = s
        await self._update_embed()

    async def _update_embed(self):
        self.embed.set_footer(text=self.TIME_FMT.format(self.time))
        await self.message.edit(embed=self.embed)
