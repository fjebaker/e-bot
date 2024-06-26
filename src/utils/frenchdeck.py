"""
Helper class for standard 52 french deck playing cards.
"""

import itertools
import functools
import random
from dataclasses import dataclass
from typing import Generator, List, Union

CARD_VALUES = range(0, 14)
CARD_SUITS = ["D", "H", "C", "S"]

BLANK_CARD = "+---+\n" + "|{} |\n" + "|{}|\n" + "+---+\n"

CARD_VALUE_STRING = {i: f"{i:2d}" for i in CARD_VALUES}
CARD_VALUE_STRING[0] = " A"  # needs space so that everything aligns in pprint
CARD_VALUE_STRING[11] = " J"
CARD_VALUE_STRING[12] = " Q"
CARD_VALUE_STRING[13] = " K"
CARD_SUIT_EMOJIS = {
    "D": "[♦]",
    "H": "[♥]",
    "C": " ♣ ",
    "S": " ♠ ",
}


# typedef
@dataclass
class Card:
    suit: str
    value: int
    is_black: bool

    def __str__(self) -> str:
        return BLANK_CARD.format(
            CARD_VALUE_STRING[self.value], CARD_SUIT_EMOJIS[self.suit]
        )

    def __lt__(self, other: "Card") -> bool:
        return self.value < other.value

    def __le__(self, other: "Card") -> bool:
        return self < other or self == other

    def __gt__(self, other: "Card") -> bool:
        return self.value > other.value

    def __ge__(self, other: "Card") -> bool:
        return self > other or self == other

    def __eq__(self, other: "Card") -> bool:
        return self.value == other.value

    def is_inbetween(self, others: List["Card"]) -> bool:
        s = sorted([self, *others])
        return self < s[-1] and s[1] == self


def _new_deck() -> Generator[Card, None, None]:
    """todo"""
    # pylint: disable=simplifiable-if-expression
    cards = [
        Card(s, v, True if s in "CS" else False)
        for (s, v) in itertools.product(CARD_SUITS, CARD_VALUES)
    ]
    random.shuffle(cards)
    return (i for i in cards)


class FrenchDeck:
    def __init__(self):
        self._deck = _new_deck()

    def deal(self) -> Card:
        """Deal the next card"""
        card = next(self._deck, None)
        if card:
            return card
        else:
            self._deck = _new_deck()
            return self.deal()

    @staticmethod
    def to_string(*cards: Union[Card, str]) -> str:
        lines = [str(i).split("\n") for i in cards]
        if lines:
            return "\n".join(
                functools.reduce(
                    lambda acc, c: [f"{acc[i]} {c[i]}" for i in range(len(c))], lines
                )
            ).strip()
        else:
            return ""

    @staticmethod
    def face_down() -> str:
        return BLANK_CARD.format("  ", "   ")
