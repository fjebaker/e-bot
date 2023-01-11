import logging

from discord.ext import commands

MAJOR_VERSION = 0
MINOR_VERSION = 1
PATCH_VERSION = 0
RELEASE_CANDIDATE = 1


class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    @commands.command(name="version")
    async def entry(self, context):
        await context.send(self._get_version_string())

    def _get_version_string(self):
        release_extension = ""
        if RELEASE_CANDIDATE:
            release_extension = f"-rc{RELEASE_CANDIDATE}"
        return f"Currently running e-bot version {MAJOR_VERSION}.{MINOR_VERSION}.{PATCH_VERSION}{release_extension}"


async def setup(bot):
    await bot.add_cog(Version(bot))

    return
