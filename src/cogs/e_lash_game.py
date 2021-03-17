import asyncio
from abstracts import EGame

import discord
from discord.ext import commands

from utils.lookups import EMOJI_NUM

import itertools
import random
import collections
import os

from econfig import PATH_EXTENSION

COG_HELP = """
    TODO
"""

PROMPTS_PER_ROUND = 2
MIN_PLAYERS = 3
WAIT_DURATION = 5  # time to show info in seconds
SCRAPE_CHANNEL = "elash-prompts"
FILE = os.path.join(PATH_EXTENSION, "data/prompts.txt")


def randomize_prompts(prompts: list):
    # shuffle a copy
    output = []

    p_cycle = itertools.cycle(prompts)
    next(p_cycle)  # exhaust first element
    for i, j in zip(prompts, p_cycle):
        output.append((i, j))
    random.shuffle(output)

    return output


class EepLash(EGame):
    def __init__(self, bot):
        super().__init__(bot, __name__)

        self.game_name = "E Lash"

    def embed(self, text):
        return discord.Embed(
            title="E Lash", description=text, colour=discord.Colour.red()
        )

    def _has_prompts(self):
        if os.path.isfile(FILE):
            with open(FILE, "r") as f:
                self.prompt_list = [i for i in f.read().split("\n") if i is not ""]
            return len(self.prompt_list) > 0
        else:
            self.logging.error(f"No prompt file {FILE}.")
            return False

    async def _scrape_prompts(self, context):
        channel = next(
            filter(lambda c: c.name == SCRAPE_CHANNEL, context.guild.channels)
        )

        prompts = []
        async for message in channel.history(limit=1000):
            try:
                prompts.append(
                    message.content.replace("{blank}", "_" * 5).replace(
                        "{the current year}", "the current year"
                    )
                )
            except Exception as e:
                self.logging.error(f"Prompt scrape error: {e}")

        with open(FILE, "w") as f:
            f.write("\n".join(prompts))

        return len(prompts)

    async def execute_round(self):
        # get prompts for round
        prompts = {i: random.choice(self.prompt_list) for i in range(len(self.players))}
        ordering = randomize_prompts(prompts.keys())

        # announce new round
        self.channel.send(
            self.embed("Starting new round -- check your DMs for your prompts!")
        )

        # need an immutable reference
        pids = self.players.keys()
        pidmap = {pid: ordering[i] for i, pid in enumerate(pids)}
        answers = collections.defaultdict(dict)

        # dm prompts to players (requires two rounds so even number of answers)
        for game_round in range(2):
            unique_content = {
                pid: {"embed": self.embed(prompts[order[game_round]])}
                for pid, order in pidmap.items()
            }
            dm_replies = await self.dm_players_unique(
                unique_content, self.players, interaction=self.DM_TEXT
            )

            for pid, message in dm_replies.items():
                prompt_num = pidmap[pid][game_round]
                answers[prompt_num][pid] = message.content

        # continuity check ?? or auto win if missing answer

        self.logging.info(answers)
        # present / vote on answers
        for index, solutions in answers.items():
            result = await self.vote_on(prompts[index], solutions)

            # announce winner
            await self.announce_ranking(result)

            # tally total scores

        await self.channel.send(embed=self.embed("End of round."))

    async def vote_on(self, prompt, solutions: dict):
        sols = [(k, v) for k, v in solutions.items()]
        choices = {i + 1: s[1] for i, s in enumerate(sols)}

        result = await self.titlemenu(
            self.game_name,
            f"Vote for your favourite.\n**{prompt}**",
            interaction=self.CHOICE(choices),
        )
        result = sorted(
            [(vote, sols[EMOJI_NUM[i] - 1][0]) for i, vote in result.items()],
            key=lambda i: i[0],
            reverse=True,
        )
        # return pid winner, pid loser
        return result

    async def announce_ranking(self, result: list):
        scoreboard = "\n".join(
            [f"{votes} votes for {self.players[pid]}" for votes, pid in result]
        )

        await self.channel.send(embed=self.embed(scoreboard))
        await asyncio.sleep(WAIT_DURATION)

    @commands.command(name="elash")
    async def entry(self, context, cmd):
        self.logging.info(f"entry called with {cmd}")

        if self.state["running"] == False and cmd == "start":
            # start game
            self.channel = context.channel
            players = await self.newplayers(
                self.game_name,
                descr=f"**{context.author.name}** wants to start a new **{self.game_name}** game.\nRequires at least 3 players.",
            )
            if len(players) < MIN_PLAYERS:
                await context.send(
                    embed=self.embed(
                        f"Too few players to start game. Requires at least {MIN_PLAYERS}."
                    )
                )
            elif self._has_prompts() == False:
                await context.send(
                    embed=self.embed("No prompts found. Run the scrape command first.")
                )
            else:
                self.state["running"] = True
                await self.execute_round()

        elif cmd == "stop":
            # stop game
            if self.state["running"]:
                self.state["running"] = False
                await context.send(embed=self.embed("Game stopped."))
            else:
                await context.send(embed=self.embed("No game running."))

        elif self.state["running"] == False and cmd == "scrape":
            number_prompts = await self._scrape_prompts(context)
            await context.send(embed=self.embed(f"Scraped {number_prompts} prompts."))
        else:
            await context.send(embed=self.embed("Unknown command."))

    async def cog_command_error(self, context, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await context.send(f"Missing Argument!\n{COG_HELP}")
        else:
            raise error


def setup(bot):
    bot.add_cog(EepLash(bot))
