import logging
import time
import os
import chatgpt

from discord.ext import commands


class GPTChat(commands.Cog):
    TIMEOUT = 20  # allow no more than 1 request every TIMEOUT seconds
    MIN_PROMPT_LENGTH = 30
    THINKING_EMOJI = "\U0001F914"

    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)
        self.last_time = time.time()
        key = os.environ.get("GPT_ACCESS_KEY", "")
        if key:
            self._gpt = chatgpt.Conversation(access_token=key)
            self._gpt.reset()
            self.enabled = True
        else:
            self.logging.warning(
                "No GPT access token provided. Cog is in disabled state."
            )
            self._gpt = None
            self.enabled = False

    def _message_meets_criteria(self, content: str) -> bool:
        return content.lower().strip().startswith("hey ebot")

    @commands.command(name="gpt_reset")
    async def reset_conversation(self, context: commands.Context, _: str):
        self._gpt.reset()
        return await context.send("Conversation state reset.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            # skip bots
            ...
        elif self._message_meets_criteria(message.content):
            if not self.enabled:
                return await message.reply("Chat is currently disabled.")
            # check timeout
            now = time.time()
            delta = now - self.last_time
            if delta < self.TIMEOUT:
                remaining = self.TIMEOUT - delta
                self.logging.info("GPT timeout remaining: %d", remaining)
                return await message.reply(
                    f"Please wait another {remaining:.1f} second(s)."
                )
            self.last_time = now

            prompt = message.content[8:].strip()
            if len(prompt) > self.MIN_PROMPT_LENGTH:
                await message.add_reaction(self.THINKING_EMOJI)
                self.logging.info("GPT prompt: '%s'", prompt)
                response = self._gpt.chat(prompt)
                return await message.reply(response)
            else:
                return await message.reply(
                    f"Sorry, your prompt is too short ({len(prompt)}/{self.MIN_PROMPT_LENGTH})"
                )


async def setup(bot):
    await bot.add_cog(GPTChat(bot))
    return
