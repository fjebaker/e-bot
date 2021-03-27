import logging

from utils.lookups import EMOJI_FORWARD, EMOJI_BACKWARD
from interactive.monitor import Monitor


class ChoiceInteraction(Monitor):
    name = "choice"

    def __init__(self, *choices, max_votes=0):
        self.logging = logging.getLogger(__name__ + ":" + self.__class__.__name__)
        self.emojis = [EMOJI_FORWARD[i] for i in range(1, len(choices) + 1)]
        self.choices = choices
        self.max_votes = max_votes

    def format(self, embed):
        for i, choice in enumerate(self.choices):
            embed.add_field(name=str(i + 1), value=choice, inline=False)

        footer_text = self.get_footer_text(embed)
        embed.set_footer(text=f"Click a reaction to make a choice.\n{footer_text}")

        return embed

    async def monitor(self, message) -> dict:
        if self.max_votes:
            count = sum(
                map(
                    lambda x: x.count - 1 if x.emoji in self.emojis else 0,
                    message.reactions,
                )
            )
            if count >= self.max_votes:
                return {self.name: count}

        return {}

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
