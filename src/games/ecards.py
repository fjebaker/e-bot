import asyncio
import random

from abstracts import EGameFactory

from interactive import InteractionPipeline, ChoiceInteraction

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
            asyncio.sleep(self.wait_duration)
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
                f"Starting new round -- {self.players[leader]} is leader.\nThis round's prompt: **{prompt}**"
            )
        )

        # immutable pids
        pids = list(self.players.keys())

        # construct content
        content_dict = {
            pid: self.embed(
                f"This round's prompt: {prompt}\nYou're the leader for this round - sit back and relax!"
            )
            if pid == leader
            else self.embed(f"This round's prompt: {prompt}")
            for pid in pids
        }

        # get all message responses
        tasks = []
        for pid in pids:
            # get channel
            dm_channel = await self.players[pid].create_dm()

            if pid != leader:
                # make pipeline
                ipl = InteractionPipeline(ChoiceInteraction(*hands[pid], max_votes=1))

                # send message by storing coroutine
                tasks.append(
                    ipl.send_and_watch(dm_channel, content_dict[pid], timeout=31)
                )
            else:
                # leader
                tasks.append(dm_channel.send(embed=content_dict[pid]))

        # await routines
        dm_response = {
            # ensure type consistent output
            pid: resp if pid != leader else {}
            for pid, resp in zip(pids, await asyncio.gather(*tasks))
        }

        # unpack which card played
        # pid -> str
        cards_played = {}
        for pid, resp in dm_response.items():

            # make sure result is present
            if "choice" in resp.get("response", {}):
                # invert choices:
                inverted = {v: k for k, v in resp["response"]["choice"].items()}

                # get, or falsey (min enumeration is 1)
                index = inverted.get(1, 0)

                if index:
                    index = inverted[1] - 1
                    cards_played[pid] = hands[pid].pop(index)
                    self.logging.info(f"player {pid} chose {index}")

                else:
                    # no card: log for now
                    self.logging.info(
                        f"Player {self.players[pid]} did not play a card."
                    )

            elif pid != leader:
                # log warning
                self.logging.warning(f"Bad response from {self.players[pid]}: {resp}")

        # shuffle responses to list
        shuffled_responses = list(cards_played.values())
        random.shuffle(shuffled_responses)

        asyncio.sleep(self.wait_duration)

        if len(shuffled_responses) == 0:
            # No-one played a card - skip the round
            return await self.channel.send(
                embed=self.embed(
                    "No-one played a card. Are the players even there? Skipping this round..."
                )
            )
        elif len(shuffled_responses) == 1:
            # Only one person played a card - award them the victory
            winning_card = shuffled_responses[0]
            winning_pid = dict_reverse_lookup(cards_played, winning_card)
            if winning_pid:

                # message channel with round result
                await self.channel.send(
                    embed=self.embed(
                        f"Only {self.players[winning_pid]} played a card:\n{winning_card}\nThey win the round by default. Is everyone else even there?"
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
            end_str = "\n".join(shuffled_responses)
            await self.channel.send(
                embed=self.embed(
                    f"This round's answers:\n{end_str}\nAwaiting choice of a winner from {self.players[leader]}"
                )
            )

            # little pause
            asyncio.sleep(self.wait_duration)

            # dm the leader to choose
            leader_ipl = InteractionPipeline(
                ChoiceInteraction(*shuffled_responses, max_votes=1)
            )
            choice_response = await leader_ipl.send_and_watch(
                await self.players[leader].create_dm(),
                self.embed("Please vote for the winning prompt."),
                timeout=31,
            )

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
                asyncio.sleep(self.wait_duration)

                # message channel with round result
                await self.channel.send(
                    embed=self.embed(
                        f"The winning answer:\n{winning_card} (answer from {self.players[winning_pid]})"
                    )
                )

                # update scoreboard
                return self._add_score(winning_pid, 1)

            else:
                # update scoreboard
                self._add_score(leader, -1)
                return await self.channel.send(
                    embed=self.embed(
                        f"No winner chosen. Punishing {self.players[leader]} with -1 point for their insolence!"
                    )
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
