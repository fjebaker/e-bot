import logging


from utils.lookups import EMOJI_FORWARD
from interactive.monitor import Monitor


class MessageInteraction(Monitor):
    name = "message"
    is_stream = True

    def __init__(self):
        self.logging = logging.getLogger(__name__ + ":" + self.__class__.__name__)

    def format(self, embed):
        footer_text = self.get_footer_text(embed)
        embed.set_footer(text=f"Message this DM to submit an answer.\n{footer_text}")
        return embed

    async def monitor(self, original, message) -> dict:

        self.logging.info(
            f"Reply to {original.id}: {message.author}: {message.content}"
        )

        await message.add_reaction(EMOJI_FORWARD["checkmark"])

        return {message.author.id: message}
