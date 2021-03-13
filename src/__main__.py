import os
import logging

from ebot import EBot

if __name__ == "__main__":
    logging.basicConfig(level=20)
    logging.info("Starting ebot...")

    bot = EBot()
    bot.load_all_available_cogs()

    bot.run(os.environ["DISCORD_TOKEN"])
