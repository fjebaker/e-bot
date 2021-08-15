import logging
import re
from typing import List

from utils.lookups import EMOJI_FORWARD
from interactive.monitor import Monitor


class MessageChoiceInteraction(Monitor):
    name = "messagechoice"
    is_stream = True

    def __init__(self, target_pid: int, choices: List[str]):
        self.logging = logging.getLogger(__name__ + ":" + self.__class__.__name__)

        self.re_choices = re.compile(f"({'|'.join(choices)})", re.IGNORECASE)
        self.target_pid = target_pid

    def format(self, embed):
        footer_text = self.get_footer_text(embed)
        embed.set_footer(
            text=f"Message this channel to submit an answer.\n{footer_text}"
        )
        return embed

    async def monitor(self, original, message) -> dict:
        # pylint: disable=arguments-differ,unused-argument

        if message.author.id == self.target_pid:
            # self.logging.info(
            #    f"Message to {original.id}: {message.author}: {message.content}"
            # )

            # ensure content is one of the available choices
            matches = re.findall(self.re_choices, message.content)
            if matches:
                # emoji react
                await message.add_reaction(EMOJI_FORWARD["checkmark"])

                return {
                    message.author.id: matches[0].lower()
                }  # always return first match

        return {}
