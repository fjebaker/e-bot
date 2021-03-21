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
        ...

    async def monitor(self, message) -> dict:
        return {}

    async def finalize(self, message) -> dict:
        ...
