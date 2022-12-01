import discord


class Monitor:
    name = ""
    is_stream = False

    def get_footer_text(self, embed):
        if embed.footer:
            return embed.footer.text
        else:
            return ""

    def reset(self):
        ...

    def format(self, embed: discord.Embed) -> discord.Embed:
        return embed

    async def post_format(self, message):
        # pylint: disable=unused-argument
        ...

    async def monitor(self, message) -> dict:
        # pylint: disable=unused-argument
        return {}

    async def finalize(self, message) -> dict:
        # pylint: disable=unused-argument
        ...
