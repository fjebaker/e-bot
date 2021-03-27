import logging

from discord.ext import commands

COG_HELP = """ No help available for this cog. """

EMOJIS = ["\U0001F47F", "\U0001F6D1", "\U000026EA", "\U00002626"]

CENSORED_WORDS = [
    "heck",
    "darn",
    "drat",
    "devil",
    "lewd",
    "wtf",
    "frick",
    "ffs",
    "shizzle",
    "bum",
    "butt",
    "pee",
    "poo",
    "ankle",
]

RUDE_MESSAGE = "Please do not swear; this is a wholesome, family-friendly christian server thank you very much."


class XtianServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    def _contains_cuss(self, content):
        """
        checks a string for censored words.

        :param content: string, the content string to check for censored words
        :return: true if any words in CENSORED_WORDS are in the content string, false otherwise.
        """
        for word in CENSORED_WORDS:
            if content.find(word) != -1:
                return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            # skip bot messages
            ...
        else:
            if self._contains_cuss(message.content.lower()):
                # add emoji reaction
                for emoji in EMOJIS:
                    await message.add_reaction(emoji)
                await message.reply(RUDE_MESSAGE, tts=True)

    @commands.command(name="cusslist")
    async def entry(self, context):
        self.logging.info("cusslist called")
        listString = "\n".join(CENSORED_WORDS)
        await context.send(f"Current cuss list:\n{listString}")


def setup(bot):
    bot.add_cog(XtianServer(bot))

    return
