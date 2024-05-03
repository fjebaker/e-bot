import os
import logging
import discord
import json

from ebot import EBot


if __name__ == "__main__":
    discord.utils.setup_logging()
    logging.info("Starting ebot...")

    admins = json.loads(os.environ["ADMIN_USERS"])
    assert isinstance(admins,list)
    bot = EBot(admins)
    bot.run(os.environ["DISCORD_TOKEN"])
