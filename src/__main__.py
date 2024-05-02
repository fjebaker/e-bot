import os
import logging
import discord

from ebot import EBot


if __name__ == "__main__":
    discord.utils.setup_logging()
    logging.info("Starting ebot...")

    bot = EBot(os.environ["ADMIN_USER"])
    bot.run(os.environ["DISCORD_TOKEN"])
