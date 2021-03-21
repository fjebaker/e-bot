import asyncio
from abstracts import EGameFactory

import discord
from discord.ext import commands

import itertools
import random
import collections
import os

from utils.lookups import EMOJI_FORWARD

from econfig import PATH_EXTENSION


def randomize_prompts(prompts: list) -> list:
    """Utility method for creating a random list of prompt pairs:
        (round 1, round 2)
    are the items of the list, such that each prompt appears exactly once per round.
    """
    # shuffle a copy
    output = []

    p_cycle = itertools.cycle(prompts)
    next(p_cycle)  # exhaust first element
    for i, j in zip(prompts, p_cycle):
        output.append((i, j))
    random.shuffle(output)

    return output


class ELash(EGameFactory):

    # configuration

    game_name = "E Lash"
    game_description = ""
    wait_duration = 2
    min_players = 1
    cog_help = "TODO"
    has_scrape = True

    file_prompts = "data/elash_prompts_{gid}.txt"
    file_safeties = "data/elash_safeties_{gid}.txt"

    channel_prompts = "elash-prompts"
    channel_safeties = "elash-safeties"

    def __init__(self, context):
        super().__init__(context, __name__)

        self.prompts = None
        self.safeties = None

    async def start(self):
        """Main entry"""

        # check if prompts
        if self.prompts == self.safeties == None:
            # info message
            self.logging.info(f"Reading prompts and safety files for {self.guild.id}.")
            await self.channel.send(
                embed=self.embed(f"Reading prompts and safety files...")
            )

            # read files
            try:
                self.prompts = self._read_file(self.file_prompts)
                self.safeties = self._read_file(self.file_safeties)
            except Exception as e:
                self.logging.error(f"Error reading files {e}")
                # early exit
                return await self.channel.send(
                    embed=self.embed(f"Error reading files\n```\n{e}\n```")
                )

            self.logging.info(
                f"Read in {len(self.prompts)} prompts and {len(self.safeties)} safeties."
            )

        # do a round
        return await self.execute_round()

    def _has_prompts(self):
        if os.path.isfile(FILE):
            with open(FILE, "r") as f:
                self.prompt_list = [i for i in f.read().split("\n") if i != ""]
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
        """Executes exactly one round of the game.

        This involves
        - getting new prompts for the round
        - annoucning the round
        - prompting each player twice for answers
        - presenting each prompt in a vote
        - for each vote tally, presenting the scores
        """
        # get prompts for round
        prompts = {i: random.choice(self.prompts) for i in range(self._num_players)}
        ordering = randomize_prompts(prompts.keys())

        # announce new round
        await self.channel.send(
            embed=self.embed("Starting new round -- check your DMs for your prompts!")
        )

        # need an immutable reference
        pids = self.players.keys()

        # give each player an ordering of prompts
        pidmap = {pid: ordering[i] for i, pid in enumerate(pids)}

        # create a data structure to hold the results
        answers = collections.defaultdict(dict)
        # will map prompt_id -> {pid -> answer}

        # dm prompts to players (requires two rounds so even number of answers)
        for game_round in range(2):
            # generate unique content to send to players
            unique_content = {
                pid: {"embed": self.embed(prompts[order[game_round]])}
                for pid, order in pidmap.items()
            }

            # get replies
            dm_replies = await self.dm_players_unique(
                unique_content, interaction=self.DM_TEXT
            )

            # unpack
            for pid, message in dm_replies.items():
                # determine which prompt was given to the player
                prompt_num = pidmap[pid][game_round]

                # store their answer indexed by the player id
                if message:
                    answers[prompt_num][pid] = message.content
                else:
                    # no message given
                    answers[prompt_num][pid] = "Safety placeholder."

        # continuity check ?? or auto win if missing answer

        self.logging.info(answers)
        # present / vote on answers
        for index, solutions in answers.items():
            result = await self.vote_on(prompts[index], solutions)

            # tally scores
            [self._add_score(*i) for i in result]

            # announce winner
            await self.announce_ranking(result)

            # tally total scores

        # print scoreboard
        await self.scoreboard()

    async def vote_on(self, prompt, solutions: dict):
        sols = [(k, v) for k, v in solutions.items()]
        # + 1 so doesn't index at 0
        choices = {i + 1: s[1] for i, s in enumerate(sols)}

        result = await self.titlemenu(
            f"Vote for your favourite.\n**{prompt}**",
            interaction=self.CHOICE(choices),
        )

        result = sorted(
            # subtract one to undo shift
            [(vote, sols[int(i) - 1][0]) for i, vote in result["response"].items()],
            key=lambda i: i[0],
            reverse=True,
        )
        # return (votes, pid_winner), (votes, pid_loser)
        return result

    async def scrape(self, context) -> str:
        """TODO"""

        num_prompts = await self._scrape_channel(
            context, self.channel_prompts, self.file_prompts
        )
        num_safeties = await self._scrape_channel(
            context, self.channel_safeties, self.file_safeties
        )

        return f"Scraped {num_prompts} prompts, and {num_safeties} safeties."
