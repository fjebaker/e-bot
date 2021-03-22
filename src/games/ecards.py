import asyncio
from abstracts import EGameFactory

import random

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

        #instance property of all prompts
        self.prompts = None
        #instance property of all safety "cards"
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
        prompt_deck = random.sample(self.prompts,len(self.prompts))
        answer_deck = random.sample(self.safeties,len(self.safeties))

        # create starting hands
        hands = {pid: [answer_deck.pop() for _ in range(9)] for pid in self.players}

        # run a round for each player
        for pid in self.players:
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
            embed=self.embed(f"Starting new round -- {self.players[leader]} is leader -- check your DMs for your prompts!")
        )
    
    async def scrape(self, context) -> str:
        """TODO"""

        num_prompts = await self._scrape_channel(
            context, self.channel_prompts, self.file_prompts
        )
        num_safeties = await self._scrape_channel(
            context, self.channel_safeties, self.file_safeties
        )

        return f"Scraped {num_prompts} prompts, and {num_safeties} safeties."