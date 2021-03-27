import discord


class Monitor:
    name = ""
    is_stream = False

    def get_footer_text(self, embed):
        #pylint: disable=no-self-use
        if embed.footer:
            return embed.footer.text
        else:
            return ""

    def reset(self):
        #pylint: disable=no-self-use
        ...

    def format(self, embed: discord.Embed) -> discord.Embed:
        #pylint: disable=no-self-use
        return embed

    async def post_format(self, message):
        #pylint: disable=no-self-use,unused-argument
        ...

    async def monitor(self, message) -> dict:
        #pylint: disable=no-self-use,unused-argument
        return {}

    async def finalize(self, message) -> dict:
        #pylint: disable=no-self-use,unused-argument
        ...
