import logging

from utils.lookups import EMOJI_FORWARD, EMOJI_BACKWARD
from interactive.monitor import Monitor


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
