import itertools
import random
import collections

from abstracts import EGameFactory

from utils.lookups import EMOJI_FORWARD
from interactive import (
    InteractionPipeline,
    MessageInteraction,
    ButtonInteraction,
    ChoiceInteraction,
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
    min_players = 2
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

        # announce new round
        await self.channel.send(
            embed=self.embed("Starting new round -- check your DMs for your prompts!")
        )

        # need an immutable reference
        pids = self.players.keys()

        # give each player an ordering of prompts
        pidmap = {pid: ordering[i] for i, pid in enumerate(pids)}

        # build interaction pipeline
        ipl = InteractionPipeline(
            MessageInteraction(),
            ButtonInteraction(
                "temperature",
                helpstring=f"Press {EMOJI_FORWARD['temperature']} for a Safety Answer (maximum 1 point).",
            ),
        )

        # dm prompts to players (requires two rounds so even number of answers)
        # create a data structure to hold the results
        answers = collections.defaultdict(dict)
        # will map prompt_id -> {pid -> answer}
        for game_round in range(2):
            # generate unique content to send to players
            unique_content = {
                pid: self.embed(prompts[order[game_round]])
                for pid, order in pidmap.items()
            }

            # get replies
            dm_response = await self.dm_players_unique(unique_content, ipipeline=ipl)
            replies = dm_response.get("message", [])

            # unpack
            used_safety = []
            for pid in pids:

                if pid in replies:
                    message = replies[pid].content
                else:
                    # doesn't matter if people picked safety or timeout
                    message = random.choice(self.safeties)
                    used_safety.append(pid)
                    await self.players[pid].send(
                        embed=self.embed(f"Your safety is:\n**{message}**")
                    )
                    message = f"{message} *(Safety)*"

                p_num = pidmap[pid][game_round]
                answers[p_num][pid] = message

        self.logging.info(answers)

        # present / vote on answers
        for index, solutions in answers.items():
            response = await self.vote_on(prompts[index], solutions)

            # announce ranking
            await self.announce_ranking(response["result"])

            if used_safety:
                # adjust for safeties
                result = self._adjust_safety(response["result"], used_safety)
            else:
                result = response["result"]

            # edit vote board
            await self._modify_vote_board(response["message"], result)

            # tally scores
            _ = [self._add_score(i[1], i[0]) for i in result]

        # print scoreboard
        await self.scoreboard()

    async def _modify_vote_board(self, message, result):
        """TODO"""
        self.logging.info("Modifying score board")
        embed = message.embeds[0]

        for (_, pid, i) in result:
            field = embed.fields[i]
            embed.set_field_at(
                i,
                name=field.name,
                value=f"{field.value} :: *{self.players[pid]}*",
                inline=False,
            )

        await message.edit(embed=embed)

    def _adjust_safety(self, result: list, used_safety: list) -> list:
        """TODO"""
        outgoing = []
        for (v, pid, i) in result:
            if pid in used_safety:
                outgoing.append((1 if v >= 1 else 0, pid, i))
            else:
                outgoing.append((v, pid, i))

        return outgoing

    async def vote_on(self, prompt: str, solutions: dict) -> dict:
        """TODO"""
        # keep immutable copy
        pids = list(solutions.keys())
        answers = [solutions[k] for k in pids]

        ipl = InteractionPipeline(
            ChoiceInteraction(*answers, max_votes=self._num_players)
        )
        response = await ipl.send_and_watch(
            self.channel, self.embed(f"Vote for your favourite:\n**{prompt}**\n")
        )

        response["result"] = sorted(
            # tuple of (votes, pid, index of answer in table)
            (
                (v, pids[int(i) - 1], int(i) - 1)
                for i, v in response["response"]["choice"].items()
            ),
            key=lambda i: i[0],
            reverse=True,
        )

        return response

    async def scrape(self, context) -> str:
        """TODO"""

        num_prompts = await self._scrape_channel(
            context, self.channel_prompts, self.file_prompts
        )
        num_safeties = await self._scrape_channel(
            context, self.channel_safeties, self.file_safeties
        )

        return f"Scraped {num_prompts} prompts, and {num_safeties} safeties."
