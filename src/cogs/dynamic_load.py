import logging

from discord.ext import commands

COG_HELP = """TODO: help"""


class DynamicLoad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging = logging.getLogger(__name__)

    async def _reload_all_cogs(self) -> list:
        self.logging.info("Reloading cogs...")

        _reloaded = []
        # local copy
        cogs = list(self.bot.extensions.keys())
        for cog in cogs:
            if cog == __name__:
                # skip
                continue
            try:
                await self.bot.reload_extension(cog)
            except Exception as e:
                self.logging.error(f"{cog} failed to reload: raised exception: {e}")
            else:
                _reloaded.append(cog)
        return _reloaded

    async def _reload_cog(self, cog_name) -> bool:
        self.logging.info(f"Attempting reload on {cog_name}...")

        if cog_name in self.bot.extensions.keys():
            try:
                await self.bot.reload_extension(cog_name)
            except Exception as e:
                self.logging.error(
                    f"{cog_name} failed to reload: raised exception: {e}"
                )
                return f"`{cog_name}` raised exception: ```\n{e}\n```"
            else:
                self.logging.info(f"Reloaded {cog_name}")
                return f"Reloaded `{cog_name}`"

        else:
            try:
                await self.bot.load_extension(cog_name)
            except Exception as e:
                self.logging.error(f"{cog_name} failed to load: raised exception: {e}")
                return f"No such cog: `{cog_name}`"
            else:
                self.logging.info(f"Loaded {cog_name}")
                return f"Loaded new cog `{cog_name}`"

    def _fmt_cog_list(self, input_list: list) -> str:
        ret = "\n".join(f"- {i}" for i in input_list)
        return f"```\n{ret}\n```"

    @commands.command(name="dloader")
    async def entry(self, context, cog_name: str):
        self.logging.info(f"entry called with {cog_name}")

        if cog_name == "all":
            reloaded = self._fmt_cog_list(await self._reload_all_cogs())
            await context.send(f"Reloaded\n{reloaded}")

        elif cog_name == "list":
            resp = self._fmt_cog_list(self.bot.extensions.keys())
            await context.send(f"Cogs currently loaded:\n{resp}")

        elif cog_name == __name__:
            await context.send("Cannot act on self-cog.")

        else:
            resp = await self._reload_cog(cog_name)
            await context.send(resp)

    async def cog_command_error(self, context, error):
        # pylint: disable=arguments-renamed
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await context.send(f"Missing Argument!\n{COG_HELP}")
        else:
            raise error


async def setup(bot):
    await bot.add_cog(DynamicLoad(bot))
    return
