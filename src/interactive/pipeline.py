import logging
from typing import Union

import discord

from utils import Clock


class InteractionPipeline:
    """Class for creating and unwinding message interactions.

    :param actions: List of interactions to watchd.
    :param timeout: Timeout in seconds before monitoring stopped.
    """

    def __init__(self, *actions):
        self.logging = logging.getLogger(__name__ + ":" + self.__class__.__name__)
        self.pipeline = actions

        self.logging.info(f"instanced with {str(actions)}")

    async def send_and_watch(
        self,
        channel,
        embed: discord.Embed,
        timeout: int = 16,
        edit_message: Union[None, discord.Message] = None,
    ) -> dict:
        # apply formats to embed and reset pipeline state
        for p in self.pipeline:
            p.reset()
            embed = p.format(embed)

        # send or edit message message
        if edit_message:
            message = edit_message
            await message.edit(embed=embed)
        else:
            message = await channel.send(embed=embed)

        # apply post formatting (emojis, etc)
        for p in self.pipeline:
            await p.post_format(message)

        # watch the message
        message, result = await self._watch(message, timeout)

        return {"message": message, "response": result}

    def _closure_capture(self, message):
        em = message.embeds[-1]

        # extract footer info
        footer_text = em.footer.text if em.footer else ""

        streaming = [i for i in self.pipeline if i.is_stream]
        observing = [i for i in self.pipeline if not i.is_stream]

        async def update_footer(text):
            em.set_footer(text=footer_text + text)
            await message.edit(embed=em)

        async def callback(rt) -> dict:
            # update info
            await update_footer(f"\nTime Remaining: {rt}s")

            if streaming:

                # monitor streams
                async for m in message.channel.history(limit=50):
                    # don't read prior to initial message
                    if m.id == message.id:
                        break

                    for p in streaming:
                        ret = await p.monitor(message, m)

                        if ret:
                            # early exit + reset footer
                            await update_footer("")
                            return {p.name: ret}

            if observing:

                # can't reassign to capture, so temp variable
                current_reference = await message.channel.fetch_message(message.id)

                # monitor own message
                for p in observing:
                    ret = await p.monitor(current_reference)

                    if ret:
                        # early exit + reset footer
                        await update_footer("")
                        return {p.name: ret}

            # return falsey
            return {}

        return callback

    async def _watch(self, message, timeout: int) -> tuple:

        clock = Clock(timeout, self._closure_capture(message))

        self.logging.info(f"Monitoring for {timeout}s")

        result = await clock.start()

        # update message reference
        message = await message.channel.fetch_message(message.id)

        for p in self.pipeline:
            p_result = await p.finalize(message)

            if p_result:

                result[p.name] = p_result

        return message, result
