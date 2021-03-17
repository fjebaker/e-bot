import asyncio
from abstracts import EGame

import discord
from discord.ext import commands

from utils.lookups import EMOJI_NUM

import itertools
import random
import collections

COG_HELP = """
    TODO
"""

PROMPTS_PER_ROUND = 2
WAIT_DURATION = 5  # time to show info in seconds


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

    async def execute_round(self):
        # get prompts for round
        prompts = {i: f"test {i}" for i in range(len(self.players))}
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
            "Vote for your favourite.\n**{prompt}**:",
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
            if len(players) < 2:
                await context.send(
                    "Too few players to start game. Requires at least 3."
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

    async def cog_command_error(self, context, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await context.send(f"Missing Argument!\n{COG_HELP}")
        else:
            raise error


def setup(bot):
    bot.add_cog(EepLash(bot))
