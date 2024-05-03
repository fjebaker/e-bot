import itertools
import random
import collections

from typing import Dict, Tuple

import discord

from abstracts import EGameFactory

from interactive import (
    UserUniqueView,
    PollView,
)


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
    wait_duration = 5
    prompt_duration = 60
    min_players = 2
    cog_help = "TODO"

    has_scrape = True
    file_prompts = "data/elash_prompts_{gid}.txt"
    file_safeties = "data/elash_safeties_{gid}.txt"

    channel_prompts = "elash-prompts"
    channel_safeties = "elash-safeties"

    def __init__(self, interaction: discord.Interaction):
        super().__init__(interaction, __name__)

        self.prompts = None
        self.safeties = None

    async def start(self):
        """Main entry"""

        # check if prompts
        if self.prompts is self.safeties is None:
            # info message
            self.logging.info(f"Reading prompts and safety files for {self.guild.id}.")
            await self.channel.send(
                embed=self.embed("Reading prompts and safety files...")
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

    @EGameFactory.execute_rounds(max_rounds=0, prompt_continue=True)
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

        # need an immutable reference
        pids = self.players.keys()

        # give each player an ordering of prompts
        pidmap = {pid: ordering[i] for i, pid in enumerate(pids)}

        # prompts to players (requires two rounds so even number of answers)
        # create a data structure to hold the results
        answers = collections.defaultdict(dict)

        # will map prompt_id -> {pid -> answer}
        for game_round in range(2):
            # generate unique content to send to players
            unique_content = {
                pid: (prompts[order[game_round]], random.choice(self.safeties))
                for pid, order in pidmap.items()
            }

            # get user inputs
            root_embed = self.embed(f"Round: {game_round} -- Click to get your prompts")
            view = UserUniqueView(
                root_embed,
                unique_content,
                delete_after=True,
                timeout=self.prompt_duration,
            )
            await view.send_and_wait(self.channel)

            # get replies
            replies: Dict[int, Tuple[str, bool]] = view.responses

            for pid in pids:
                reply, safety = replies.get(pid, (unique_content[pid][1], True))
                p_num = pidmap[pid][game_round]
                answers[p_num][pid] = (reply, safety)

        self.logging.info(answers)

        # present / vote on answers
        for index, solutions in answers.items():
            message, result = await self.vote_on(prompts[index], solutions)

            # announce ranking
            await self.announce_ranking(result)

            used_safety = [pid for (pid, sol) in solutions.items() if sol[1]]

            if used_safety:
                # adjust for safeties
                result = self._adjust_safety(result, used_safety)

            # edit vote board
            await self._modify_vote_board(message, result, used_safety)

            # tally scores
            _ = [self._add_score(i[1], i[0]) for i in result]

        # print scoreboard
        await self.scoreboard()

    async def _modify_vote_board(self, message, result, used_safety):
        """TODO"""
        self.logging.info("Modifying score board")
        embed = message.embeds[0]

        for votes, pid, i in result:
            field = embed.fields[i]
            safety_string = " (safety)" if pid in used_safety else ""
            embed.set_field_at(
                i,
                name=f"Total votes: {votes}",
                value=f"{field.value} -- *{self.players[pid].name}* {self._player_symbols[pid]}"
                + safety_string,
                inline=False,
            )

        await message.edit(embed=embed)

    def _adjust_safety(self, result: list, used_safety: list) -> list:
        """TODO"""
        outgoing = []
        for v, pid, i in result:
            if pid in used_safety:
                outgoing.append((1 if v >= 1 else 0, pid, i))
            else:
                outgoing.append((v, pid, i))

        return outgoing

    async def vote_on(
        self, prompt: str, solutions: dict
    ) -> Tuple[discord.Message, list]:
        """TODO"""
        # keep immutable copy
        pids = list(solutions.keys())
        answers = [solutions[k][0] for k in pids]

        # assemble vote card and issue the poll
        embed = self.embed(f"Click to vote:\n**{prompt}**\n")
        labels = []
        for i, ans in enumerate(answers):
            label = f"{i+1}"
            embed.add_field(name=label, value=ans, inline=False)
            labels.append(label)

        poll = PollView(
            list(self.players.keys()), embed, labels, timeout=self.prompt_duration
        )
        await poll.send_and_wait(self.channel)

        # get the results
        result = sorted(
            ((v, pids[i], i) for (i, v) in enumerate(poll.votes)),
            key=lambda i: i[0],
            reverse=True,
        )

        return poll.message, result

    async def scrape(self, interaction: discord.Interaction) -> str:
        """TODO"""

        num_prompts = await self._scrape_channel(
            interaction, self.channel_prompts, self.file_prompts
        )
        num_safeties = await self._scrape_channel(
            interaction, self.channel_safeties, self.file_safeties
        )

        return f"Scraped {num_prompts} prompts, and {num_safeties} safeties."
