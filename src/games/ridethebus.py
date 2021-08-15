import asyncio

from collections import defaultdict, namedtuple
import itertools
from typing import Callable, List, Union, Tuple

import discord

from abstracts import EGameFactory

from utils.frenchdeck import FrenchDeck, Card
from interactive import InteractionPipeline, MessageChoiceInteraction

RideTheBusQuestion = namedtuple("RideTheBusQuestion", ["choices", "prompt", "handle"])


class CardPyramid:
    def __init__(self, deck: FrenchDeck, base=4):
        self.base = base
        # index 0 is bottom row
        self._cards = [
            [deck.deal() for _ in range(i + 1)] for i in reversed(range(base))
        ]
        self.current_row = 1  # start indexing at 1
        self._current_pos = 0

    def __contains__(self, card: Card) -> bool:
        """Returns true is `card` in the currently active row of the pyramid."""
        return card in self._cards[self.current_row - 1]

    def __str__(self) -> str:
        """Pretty prints the pyramid"""
        # rows above current line
        lines = [
            [FrenchDeck.face_down() for _ in range(self.base - i)]
            for i in reversed(range(self.current_row, self.base))
        ]
        # current line
        lines.append(
            [
                str(card) if i < self._current_pos else FrenchDeck.face_down()
                for (i, card) in enumerate(self._cards[self.current_row - 1])
            ]
        )

        # rows below
        # pylint: disable=expression-not-assigned
        [lines.append(self._cards[i]) for i in reversed(range(self.current_row - 1))]

        lines = map(lambda i: FrenchDeck.to_string(*i), lines)

        return "\n".join(lines)

    def current(self) -> Union[Card, None]:
        if self._current_pos <= 0:
            return None
        return self._cards[self.current_row - 1][self._current_pos - 1]

    def advance(self) -> bool:
        retval = True
        self._current_pos += 1

        if self._current_pos > self.base - self.current_row:
            # next row
            self._current_pos = 0
            retval = self.advance_row()

        return retval

    def uncover_row(self):
        self._current_pos = self.base - (self.current_row - 1)

    def advance_row(self, uncover=False) -> bool:
        self.current_row += 1
        if self.current_row > self.base:
            # no more cards
            return False

        if uncover:
            self.uncover_row()
        else:
            self._current_pos = 0

        return True

    def sparse(self) -> str:
        """Sparse string of the pyramid"""
        rep = [
            "." * (self.base - i) for i in reversed(range(self.current_row, self.base))
        ]

        num = self._current_pos
        rep.append("#" * num + "." * ((self.base - self.current_row) - num + 1))
        # pylint: disable=expression-not-assigned
        [
            rep.append("#" * (self.base - i))
            for i in reversed(range(self.current_row - 1))
        ]

        return "\n".join(rep)

    def __iter__(self):
        self._current_pos = 0
        self.current_row = 1
        for c in itertools.chain(*self._cards):
            yield c


class RideTheBus(EGameFactory):

    # configuration
    game_name = "Ride the Bus"
    game_description = "Drink."
    wait_duration = 7
    min_players = 1
    cog_help = "TODO"

    def __init__(self, context):
        super().__init__(context, __name__)
        self.has_scrape = False

        # map player id to the cards they currently have
        self.hands = defaultdict(list)

        # assemble round questions
        self._questions = [
            self._red_or_black,
            self._higher_or_lower,
            self._inbetween,
            self._guess_suit,
        ]

        self.deck = None

    async def start(self):
        self.deck = FrenchDeck()

        # get immutable ordering
        pids = list(self.players.keys())

        await self.round_one(pids)
        # await asyncio.sleep(self.wait_duration)
        bus_rider_pid = await self.round_two(pids)

        await self.round_three(bus_rider_pid)

        return

    async def round_three(self, br_pid: int):
        self.logging.info(
            "Started round 3: %s is riding the bus", self.players[br_pid].name
        )

        pyramid = CardPyramid(self.deck)

        def get_msg_body():
            return "\n```css\n{}```\n\n".format(pyramid)

        for card in pyramid:
            # clear the players hand
            self.hands[br_pid] = []

            # want to edit the same message for the array of questions
            message = await self.channel.send(embed=self.embed(get_msg_body()))

            for i, question in enumerate(self._questions):
                await self._handle_question(
                    br_pid,
                    question,
                    card,
                    modifier=pyramid.current_row,
                    prompt_prefix=get_msg_body(),
                    edit_message=message,
                )
                # update card for next question
                card = self.deck.deal()
                # sleep
                await asyncio.sleep(self.wait_duration)

                # only advance on first question
                if i == 0:
                    self.logging.info("Advancing pyramid...")
                    pyramid.advance()

        await self.channel.send(
            embed=self.embed(
                "Congratulations **{}**: you have successfully ridden the bus.".format(
                    self.players[br_pid].name
                )
            )
        )

    async def round_two(self, pids) -> int:
        self.logging.info("Starting phase 2")

        pyramid = CardPyramid(self.deck)

        def get_msg_body():
            return "\n```css\n{}```\n\n".format(pyramid) + "\n".join(
                self._hand_to_string(pid, f"{self.players[pid].name}:\n")
                for pid in pids
            )

        message = await self.channel.send(
            embed=self.embed("Phase 2:\n" + get_msg_body())
        )

        await asyncio.sleep(self.wait_duration)

        # as many rounds as base of pyramid
        for round_num in range(pyramid.base):

            self.logging.info("Round two: row %d of %d", round_num + 1, pyramid.base)

            # reveal
            pyramid.uncover_row()

            msg = "Phase 2:\n" + get_msg_body()
            # update message
            await message.edit(embed=self.embed(msg))

            # check who scored this round
            scores = defaultdict(int)

            for pid in pids:
                # create copy of hand
                hand = self.hands[pid][:]

                # pylint: disable=expression-not-assigned
                [self.hands[pid].remove(c) for c in hand if c in pyramid]
                # count removed
                scores[pid] = len(hand) - len(self.hands[pid])

            await asyncio.sleep(self.wait_duration)

            score_text = "\n".join(
                f"{self.players[pid].name} hand out **{score * (round_num + 1)} drinks**!"
                for pid, score in scores.items()
                if score
            )

            # info catch
            score_text = score_text if score_text else "Nobody scored!"

            msg = "Phase 2:\n" + get_msg_body() + "\n" + score_text
            # update message
            await message.edit(embed=self.embed(msg))

            # advance to next row
            pyramid.advance_row()

            # scale wait time for number of players
            await asyncio.sleep(len(self.players) * self.wait_duration)

        # announce who is riding the bus: sorry first person in list ://
        br_pid = min(self.hands.items(), key=lambda i: i[1])[0]

        await self.channel.send(
            embed=self.embed(
                "{} is **riding the bus**!".format(self.players[br_pid].name)
            )
        )

        return br_pid

    async def round_one(self, pids: List[int]):
        """
        Cycling players:
            - red or black
            - higher or lower
            - in-between or outside
            - guess the suit
        """

        self.logging.info("Started phase one")

        for question in self._questions:
            # prompt each player
            for pid in pids:
                # deal card
                card = self.deck.deal()
                # handle question
                await self._handle_question(pid, question, card)
                # sleep
                await asyncio.sleep(self.wait_duration)

    async def _handle_question(
        self,
        pid: int,
        question: RideTheBusQuestion,
        card: Card,
        modifier: int = 1,
        prompt_prefix: str = "",
        edit_message: Union[None, discord.Message] = None,
    ):
        # pylint: disable=too-many-arguments
        self.logging.info(
            "Posing %s to player %s.", question.choices, self.players[pid]
        )

        ipl = InteractionPipeline(MessageChoiceInteraction(pid, question.choices))

        # get user response to question
        prompt = prompt_prefix + self._make_prompt(pid, question.prompt)
        response = await ipl.send_and_watch(
            self.channel,
            self.embed(prompt + self._hand_to_string(pid, prefix="Your hand:\n")),
            edit_message=edit_message,
        )

        self.logging.info("Response: %s", response)

        if "messagechoice" in response["response"]:
            answer = response["response"]["messagechoice"].get(pid, "")
        else:
            answer = ""

        # get result of question
        colour, outcome = question.handle(pid, answer, card, amount=1 * modifier)

        # assemble modification to prompt
        result = (
            prompt
            + self._hand_to_string(pid, prefix="Current cards:\n")
            + f"\n{outcome}"
        )

        # update message with result
        await response["message"].edit(embed=self.embed(result, colour=colour))

    @property
    def _red_or_black(self) -> RideTheBusQuestion:
        return RideTheBusQuestion(
            choices=["red", "black"],
            prompt="**Red** or **Black**?",
            handle=self._make_handler(
                lambda hand, answer, card: (answer == "black" and card.is_black)
                or (answer == "red" and not card.is_black)
            ),
        )

    @property
    def _higher_or_lower(self) -> RideTheBusQuestion:
        return RideTheBusQuestion(
            choices=["higher", "lower"],
            prompt="**Higher** or **Lower**?",
            handle=self._make_handler(
                lambda hand, answer, card: (answer == "higher" and card >= hand[-1])
                or (answer == "lower" and card < hand[-1])
            ),
        )

    @property
    def _inbetween(self) -> RideTheBusQuestion:
        return RideTheBusQuestion(
            choices=["inbetween", "outside"],
            prompt="**Inbetween** or **Outside**?",
            handle=self._make_handler(
                lambda hand, answer, card: (
                    answer == "inbetween" and card.is_inbetween(hand[-2:-1])
                )
                or (answer == "outside" and not card.is_inbetween(hand[-2:-1]))
            ),
        )

    @property
    def _guess_suit(self) -> RideTheBusQuestion:
        return RideTheBusQuestion(
            choices=["hearts", "spades", "diamonds", "clubs", "broccoli"],
            prompt="Guess the suit: **Hearts**, **Diamonds**, **Clubs**, or **Spades**?",
            handle=self._make_handler(
                lambda hand, answer, card: (answer == "spades" and card.suit == "S")
                or (answer == "hearts" and card.suit == "H")
                or (answer == "diamonds" and card.suit == "D")
                or (answer in ["clubs", "broccoli"] and card.suit == "C")
            ),
        )

    def _make_handler(
        self, func: Callable[[List[Card], str, Card], bool]
    ) -> Callable[[int, str, Card], str]:
        def handler(
            pid: int, answer: str, card: Card, amount=1
        ) -> Tuple[discord.Colour, str]:

            hand = self.hands[pid]
            self.logging.info("pid %d gave answer '%s'", pid, answer)
            if hand:
                self.logging.info("card < hand[-1] %s", card < hand[-1])
                self.logging.info("card > hand[-1] %s", card > hand[-1])

            # check outcome
            if func(hand, answer, card):
                ret = (
                    discord.Colour.green(),
                    f"You are Correct! **Hand out {amount} drink{'s' if amount > 1 else ''}.**",
                )
            elif answer:
                ret = (
                    discord.Colour.red(),
                    f"You are Incorrect! **Drink {amount} sip{'s' if amount > 1 else ''}!**",
                )
            else:
                ret = (
                    discord.Colour.red(),
                    f"You didn't provide a suitable answer. **Drink {amount} sip{'s' if amount > 1 else ''}!**",
                )

            self.logging.info("Returning string '%s'", ret[1])

            # add card to hand
            self.hands[pid].append(card)
            return ret

        return handler

    def _make_prompt(self, pid: int, question: str) -> str:
        return f"@{self.players[pid].name}: {question}\n"

    def _hand_to_string(self, pid: int, prefix="") -> str:
        return (
            "{}```css\n{}```".format(prefix, FrenchDeck.to_string(*self.hands[pid]))
            if self.hands[pid]
            else ""
        )
