import logging
import eversion

from discord.ext import commands

class Version(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    @commands.command(name="version")
    async def entry(self, context):
        current_version = self._get_version_string()
        self.logging.info(f"version called - current version is {current_version}")
        await context.send(f"Currently running e-bot version {current_version}")

    def _get_version_string(self):
        release_extension = ""
        if eversion.RELEASE_CANDIDATE:
            release_extension = f"-rc{eversion.RELEASE_CANDIDATE}"
        return f"Currently running e-bot version {eversion.MAJOR_VERSION}.{eversion.MINOR_VERSION}.{eversion.PATCH_VERSION}{release_extension}"


async def setup(bot):
    await bot.add_cog(Version(bot))

    return
