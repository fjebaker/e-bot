import logging

from utils.lookups import EMOJI_FORWARD
from interactive.monitor import Monitor


class ReplyInteraction(Monitor):
    name = "reply"
    is_stream = True

    def __init__(self):
        self.logging = logging.getLogger(__name__ + ":" + self.__class__.__name__)

    def reset(self):
        self.replies = []

    def format(self, embed):
        footer_text = self.get_footer_text(embed)
        embed.set_footer(text=f"Reply to this message.\n{footer_text}")
        return embed

    async def monitor(self, original, message) -> dict:
        if (
            message.reference
            and message.reference.resolved.id == original.id
            and message not in self.replies
        ):
            self.logging.info(
                f"Reply to {original.id}: {message.author}: {message.content}"
            )

            self.replies.append(message)

            await message.add_reaction(EMOJI_FORWARD["checkmark"])

        return {}

    async def finalize(self, message):
        return {i.author.id: i for i in self.replies}
