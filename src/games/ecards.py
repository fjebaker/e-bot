import asyncio
from abstracts import EGameFactory

import random

from interactive import *

from utils import dmerge


class ECards(EGameFactory):
    """
    EGameFactory for a game where one player is given a prompt,
    the other players select an answer from a set of safety answers,
    and the head player selects their favourite answer.
    """

    # Configuration for the game
    game_name = "E Cards"
    game_description = "Prompt cards with your friends!"
    wait_duration = 5
    min_players = 3
    cog_help = """
    EGameFactory for a game where one player is given a prompt,
    the other players select an answer from a set of safety answers,
    and the head player selects their favourite answer.
    """
    has_scrape = True

    file_prompts = "data/elash_prompts_{gid}.txt"
    file_safeties = "data/elash_safeties_{gid}.txt"

    def __init__(self, context):
        super().__init__(context, __name__)

        # instance property of all prompts
        self.prompts = None
        # instance property of all safety "cards"
        self.safeties = None

    async def start(self):
        """
        Method for starting the E Card game.
        Reads in prompts, puts the deck in a particular state, and runs the game.
        """

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

        # create deck orders
        prompt_deck = random.sample(self.prompts, len(self.prompts))
        answer_deck = random.sample(self.safeties, len(self.safeties))

        # create starting hands
        hands = {pid: [answer_deck.pop() for _ in range(9)] for pid in self.players}

        # run a round for each player
        for pid in self.players:
            self.logging.info(
                f"new ecards round with leader player {self.players[pid]}"
            )
            await self.execute_round(pid, prompt_deck.pop(), hands)
            ECards.refill_hands(hands, answer_deck)
        return await self.scoreboard()

    @staticmethod
    def refill_hands(hands: dict, answer_deck: list):
        """
        Refills the players' hands from a deck of answers after a round.
        Objects are passed by reference and modifications made in place, hence no need to return.

        :param hands: a dictionary mapping player index to player hand
        :param answer_deck: a deck of answer cards to fill hands with
        """
        for key in hands:
            while len(hands[key]) < 9:
                hands[key].append(answer_deck.pop())

    @staticmethod
    def construct_message(prompt: str, cards: list) -> str:
        """
        Convenience method to construct the message to send to a non-leader player.
        Tells them the current prompt and their hand.
        """
        end = "\n".join([f"{index+1}: {value}" for index, value in enumerate(list)])
        return "This round's prompt: {prompt}\n{end}"

    async def execute_round(self, leader: str, prompt: str, hands: dict):
        """Executes exactly one round of the game.

        This involves
        - sending the prompt to all players
        - allowing non-leader players to select a card
        - presenting all answers to the leader - allowing them to vote
        - displaying round results to channel

        :param leader: the index of the leader player
        :param prompt: the prompt for the round
        :param hands: the players' hands
        """
        # announce new round
        await self.channel.send(
            embed=self.embed(
                f"Starting new round -- {self.players[leader]} is leader.\nThis round's prompt: {prompt}"
            )
        )

        # construct content
        content_dict = {
            pid: self.embed(
                f"This round's prompt: {prompt}\nYou're the leader for this round - sit back and relax!"
            )
            if pid == leader
            else self.embed(ECards.construct_message(prompt, hands[pid]))
            for pid in hands
        }

        # construct pipelines
        pipeline_dict = {
            pid: False
            if pid == leader
            else InteractionPipeline(ChoiceInteraction(*hands[pid], max_votes=1))
            for pid in hands
        }

        # get all message responses
        dm_response = await self._dm_players_unique_pipelines(
            content_dict, pipeline_dict
        )
        replies = dm_response.get("message", [])

        # card played for each pid
        cards_played = {}
        for pid in hands:
            if pid != leader and pid in replies:
                choices = [
                    index
                    for index, item in enumerate(replies[pid]["choice"])
                    if item == 1
                ]
                if len(choices) > 0:
                    cards_played[pid] = hands[pid].pop(choices[0])

        # TODO: Default logic for if 0 or 1 cards played

        # shuffle responses to list
        shuffled_responses = list(cards_played.values())
        random.shuffle(shuffled_responses)

        # construct message for channel
        end_str = "\n".join(shuffled_responses)
        await self.channel.send(
            embed=self.embed(
                f"This round's answers:\n{end_str}\nAwaiting choice of a winner from {self.players[leader]}"
            )
        )

        # dm the leader to choose
        leader_pipeline = InteractionPipeline(
            ChoiceInteraction(shuffled_responses, max_votes=1)
        )
        choice_response = await self.dm_players(
            "Please vote for the winning prompt.", [leader], leader_pipeline
        )
        choice_replies = choice_response.get("message", [])

        # find winning card
        winning_card = ""
        if leader in choice_replies:
            choices = [
                index
                for index, item in enumerate(choice_replies[leader]["choice"])
                if item == 1
            ]
            if len(choices) > 0:
                winning_card = shuffled_responses[choices[0]]

        # find winning user from card
        winning_pid = ""
        winning_pid_list = [item for item in cards_played if item[1] == winning_card]
        if len(winning_pid_list) > 0:
            winning_pid = winning_pid_list[0]

        # TODO: Logic for if no card is chosen

        # message channel with round result
        await self.channel.send(
            embed=self.embed(
                f"The winning answer:\n{winning_card} (answer from {self.players[winning_pid]})"
            )
        )

        # update scoreboard
        self._add_score(winning_pid, 1)

    async def scrape(self, context) -> str:
        """TODO"""

        num_prompts = await self._scrape_channel(
            context, self.channel_prompts, self.file_prompts
        )
        num_safeties = await self._scrape_channel(
            context, self.channel_safeties, self.file_safeties
        )

        return f"Scraped {num_prompts} prompts, and {num_safeties} safeties."

    async def _dm_players_unique_pipelines(
        self, unique_content: dict, ipipelines: dict
    ) -> dict:
        """DM unique content to each player, indexed by player id.

        :param unique_content: Embed content to send to player, indexed by the
        player id.
        :param ipipelines: Interaction pipeline to send to player, indexed by the
        player id.

        :return: Reply dictionary if interaction present, else `None`.
        """

        tasks = []
        for pid, embed in unique_content.items():

            # get dm channel
            dm_channel = self.players[pid].dm_channel
            if not dm_channel:
                # else create
                dm_channel = await self.players[pid].create_dm()

            if ipipelines[pid]:
                self.logging.info(f"send_and_watch {dm_channel}")
                t = ipipelines[pid].send_and_watch(dm_channel, embed, timeout=31)

            else:
                self.logging.info(f"send {dm_channel}")
                t = dm_channel.send(embed=embed)

            tasks.append(t)

        response_list = await asyncio.gather(*tasks)
        response_list = [item if item else {} for item in response_list]

        responses = dmerge(*response_list)
        self.logging.info(responses)

        return responses["response"]
