import logging
from typing import List

import discord
from interactive.timedview import TimedView

from utils.lookups import EMOJI_FORWARD, EMOJI_BACKWARD, random_emoji
from utils import async_context_wrap
from interactive.monitor import Monitor

logger = logging.getLogger(__name__)


class UserPollView(discord.ui.View):
    def __init__(self, labels: List[str], **kwargs):
        super().__init__(**kwargs)

        # where we store the results of the poll
        self.vote = -1

        for i, label in enumerate(labels):
            btn = discord.ui.Button(label=label)
            btn.callback = self._button_callback(i)
            self.add_item(btn)

    def _button_callback(self, i: int):
        async def _callback(interaction: discord.Interaction):
            self.vote = i
            await interaction.response.send_message(
                content="Vote submitted.", delete_after=5, ephemeral=True
            )
            self.stop()

        return _callback


class PollView(TimedView):
    def __init__(
        self, whitelist: List[int], embed: discord.Embed, labels: List[str], **kwargs
    ):
        super().__init__(embed, **kwargs)
        self.labels = labels
        self.whitelist = whitelist
        self.votes = [0 for _ in labels]
        self.voted = []

        btn = discord.ui.Button(
            label="Vote", emoji=random_emoji(), style=discord.ButtonStyle.green
        )
        btn.callback = async_context_wrap(self, self.vote_callback)
        self.add_item(btn)

    async def vote_callback(self, interaction: discord.Interaction):
        poll = UserPollView(self.labels, timeout=self.time)
        await interaction.response.send_message(
            view=poll, ephemeral=True, delete_after=self.time
        )
        # wait until result
        await poll.wait()

        if poll.vote < 0:
            logger.info("User %s did not vote.", interaction.user.name)
        else:
            logger.info("User %s voted for %d", interaction.user.name, poll.vote)
            self.votes[poll.vote] += 1

        self.check_continue()

    async def interaction_check(self, interaction: discord.Interaction):
        uid = interaction.user.id
        if uid in self.whitelist and uid not in self.voted:
            self.voted.append(uid)
            return True

        elif uid in self.voted:
            logger.info("User %s has already voted on this poll", interaction.user.name)
            await interaction.response.send_message(
                content="You have already voted", ephemeral=True, delete_after=5
            )
            return False

        else:
            logger.info("User %s is not playing this round", interaction.user.name)
            await interaction.response.send_message(
                content="You are not playing in this round.",
                ephemeral=True,
                delete_after=5,
            )
            return False

    def check_continue(self):
        if sum(self.votes) == len(self.whitelist):
            self.time = 1


class PollInteraction(Monitor):
    name = "poll"

    def __init__(self, *emoji_indexes):
        self.logging = logging.getLogger(__name__ + ":" + self.__class__.__name__)
        self.emojis = [EMOJI_FORWARD[i] for i in emoji_indexes]

    def format(self, embed):
        footer_text = self.get_footer_text(embed)
        embed.set_footer(text=f"Click a reaction to make a choice.\n{footer_text}")
        return embed

    async def post_format(self, message):
        for emoji in self.emojis:
            await message.add_reaction(emoji)

    async def finalize(self, message):
        # subtract 1 for bot
        return {
            EMOJI_BACKWARD[i.emoji]: i.count - 1
            for i in message.reactions
            if i.emoji in self.emojis
        }
