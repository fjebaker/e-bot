import asyncio
import random
from typing import Dict

import discord

from abstracts import EGameFactory

from interactive import CardsGetPromptView, CardsSelectWinningPromptView, InteractionPipeline, ChoiceInteraction

from utils import TestBotUser
from utils.misc import dict_reverse_lookup


class ECards(EGameFactory):
    """
    EGameFactory for a game where one player is given a prompt,
    the other players select an answer from a set of safety answers,
    and the head player selects their favourite answer.
    """

    # Configuration for the game
    game_name = "E Cards"
    game_description = "Prompt cards with your friends!"
    wait_duration = 6
    min_players = 2
    cog_help = """
    Prompt card game to play with your friends.
    Take it in turns to choose the funniest answer to a prompt that your peers chose from their hand of cards.
    Commands:
        .e ecards scrape - update the game with the latest prompts and cards
        .e ecards start - start playing a game in the current channel
        .e ecards stop - stop playing the active game
    """

    has_scrape = True
    file_prompts = "data/elash_prompts_{gid}.txt"
    file_safeties = "data/elash_safeties_{gid}.txt"

    channel_prompts = "elash-prompts"
    channel_safeties = "elash-safeties"

    def __init__(self, interaction: discord.Interaction):
        super().__init__(interaction, __name__)

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

        # create deck orders
        prompt_deck = random.sample(self.prompts, len(self.prompts))
        answer_deck = random.sample(self.safeties, len(self.safeties))

        # create starting hands
        hands = {
            pid: [answer_deck.pop() for _ in range(5)] for pid in self.players.keys()
        }

        # run a round for each player
        return await self.execute_rotation(prompt_deck, answer_deck, hands)

    @EGameFactory.execute_rounds(max_rounds=0, prompt_continue=True)
    async def execute_rotation(self, prompt_deck: list, answer_deck: list, hands: dict):
        """
        Runs a round for each player
        """
        # ensure every player has a hand
        for pid in self.players:
            if pid not in hands:
                hands[pid] = [answer_deck.pop() for _ in range(5)]
        # round for each player
        for pid in self.players:
            self.logging.info(
                f"new ecards round with leader player {self.players[pid]}"
            )
            await self.execute_round(pid, prompt_deck.pop(), hands)
            ECards.refill_hands(hands, answer_deck)
            await asyncio.sleep(self.wait_duration)
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
            while len(hands[key]) < 5:
                hands[key].append(answer_deck.pop())

    async def execute_round(self, leader: int, prompt: str, hands: dict):
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
        # get all message responses
        root_embed = self.embed(f"Starting new round -- {self.players[leader]} is leader.\nThis round's prompt: \n**{prompt}**")
        view = CardsGetPromptView(
            root_embed,
            self.game_name,
            leader,
            hands,
            delete_after=True,
            timeout=31,
        )
        await view.send_and_wait(self.channel)

        # get replies
        replies: Dict[int, int] = view.responses
        if TestBotUser.test_bot_id in self.players and TestBotUser.test_bot_id != leader:
            replies[TestBotUser.test_bot_id] = random.choice(range(len(hands[TestBotUser.test_bot_id])))

        # unpack which card played
        # pid -> str
        cards_played = {}
        for pid, responseIndex in replies.items():

            if responseIndex is None:
                self.logging.info(
                    f"Player {self.players[pid]} did not play a card."
                )
            else:
                cards_played[pid] = hands[pid].pop(responseIndex)
                self.logging.info(f"player {pid} chose {responseIndex}")

        # shuffle responses to list
        shuffled_responses = list(cards_played.values())
        random.shuffle(shuffled_responses)

        await asyncio.sleep(self.wait_duration)

        if len(shuffled_responses) == 0:
            # No-one played a card - skip the round
            await self.channel.send(
                embed=self.embed(
                    "No-one played a card. Are the players even there? Skipping this round..."
                )
            )
            return

        elif len(shuffled_responses) == 1:
            # Only one person played a card - award them the victory
            winning_card = shuffled_responses[0]
            winning_pid = dict_reverse_lookup(cards_played, winning_card)
            if winning_pid:
                # send round result
                await self.channel.send(
                    embed=self.embed(
                        f"This round's prompt: \n**{prompt}**\nOnly {self.players[winning_pid]} played a card:\n{winning_card}\nThey win the round by default."
                    )
                )

                # update scoreboard
                return self._add_score(winning_pid, 1)
            else:
                self.logging.warning(
                    f"{winning_card} not in {cards_played}:: {shuffled_responses}."
                )
                return
        else:
            # Enough responses for a proper vote
            end_str = "\n".join((f"- {i}" for i in shuffled_responses))

            em_text = f"This round's prompt: \n**{prompt}**\nThis round's answers:\n{end_str}\nAwaiting choice of a winner from **{self.players[leader]}**."
            winner_root_embed = self.embed(em_text)
            winner_view = CardsSelectWinningPromptView(
                em_text,
                leader,
                {leader:shuffled_responses},
                delete_after=True,
                timeout=31,
            )
            await winner_view.send_and_wait(self.channel)

            winner_replies: Dict[int, int] = winner_view.responses
            if TestBotUser.test_bot_id == leader:
                winner_replies[TestBotUser.test_bot_id] = random.choice(range(len(shuffled_responses)))
            
            choice_response = winner_replies[leader]

            # find winning card
            winning_card = ""
            if choice_response:
                # invert
                inverted = {
                    v: k for k, v in choice_response["response"]["choice"].items()
                }
                index = inverted.get(1, 0)
                if index:
                    winning_card = shuffled_responses[index - 1]

            winning_pid = dict_reverse_lookup(cards_played, winning_card)
            if winning_pid:
                # little pause
                await asyncio.sleep(self.wait_duration)

                # message channel with round result
                await self.channel.send(
                    embed=self.embed(
                        f"The winning answer:\n**{winning_card}**\n(answer from {self.players[winning_pid]})"
                    )
                )

                # update scoreboard
                return self._add_score(winning_pid, 1)

            else:
                # update scoreboard
                self._add_score(leader, -1)
                await self.channel.send(
                    embed=self.embed(
                        f"No winner chosen. Punishing {self.players[leader]} with -1 point for their insolence!"
                    )
                )
                return

    async def scrape(self, interaction: discord.Interaction) -> str:
        """TODO"""

        num_prompts = await self._scrape_channel(
            interaction, self.channel_prompts, self.file_prompts
        )
        num_safeties = await self._scrape_channel(
            interaction, self.channel_safeties, self.file_safeties
        )

        return f"Scraped {num_prompts} prompts, and {num_safeties} safeties."
