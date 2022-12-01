import os
import logging
import discord

from ebot import EBot

if __name__ == "__main__":
    discord.utils.setup_logging()
    logging.info("Starting ebot...")

    bot = EBot()
    bot.run(os.environ["DISCORD_TOKEN"])
