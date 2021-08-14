import logging
import asyncio
import os

from functools import wraps
from itertools import count
from collections import defaultdict

import discord

from utils import dmerge
from utils.lookups import EMOJI_FORWARD

from interactive import InteractionPipeline, ChoiceInteraction, ReplyInteraction

from econfig import PATH_EXTENSION, PLAYER_GATHER_TIMEOUT


def replace_rules(content: str) -> str:
    """TODO"""
    return content.replace("{blank}", "_" * 5).replace(
        "{the current year}", "the current year"
    )


class EGameFactory:
    """E Game Factory Superclass

    To be inherited by subclassing game cogs, providing basic interaction
    such as polling, player and context management, scores, etc.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, context, logger_name: str):
        """
        `logger_name` should just be `__name__` of instancing module. Used
        only for logging purposes.
        """
        self.logging = logging.getLogger(logger_name)

        self.guild = context.guild
        self.channel = context.channel

        # players property
        self._players = {}  # index by id
        self._num_players = 0

        # set in derived
        self.game_name: str
        self.game_description: str
        self.wait_duration: int

        # state
        self.state = {
            "running": False,
            "scores": defaultdict(int),
        }  # scores index pid -> score

        # adjust file locations
        for file_path in [attr for attr in dir(self) if attr.startswith("file_")]:
            self.__setattr__(
                file_path,
                os.path.join(
                    PATH_EXTENSION,
                    self.__getattribute__(file_path).format(gid=self.guild.id),
                ),
            )

    def embed(self, text: str, **kwargs):
        """Convenience method for creating `discord.Embed` instances.

        :param text: Text to insert in the `description` of the embed object.

        :return: The embed instance
        :rtype: discord.Embed
        """
        return discord.Embed(
            title=self.game_name,
            description=text,
            colour=discord.Colour.blue(),
            **kwargs,
        )

    def _add_score(self, pid: int, value: int):
        """TODO"""
        self.logging.info(f"Adding score {value} for player {pid}")
        self.state["scores"][pid] += value

    @staticmethod
    def _read_file(path: str) -> str:
        """Utility method for reading in scraped files. Scraped files
        are always assumed to be new-line seperated.

        :param path: Path to the file

        :return: Content of the file
        """
        data = None
        with open(path, "r") as f:
            data = f.read().split("\n")
        return data

    @property
    def players(self) -> dict:
        """Players property getter"""
        return self._players

    @players.setter
    def players(self, players: dict):
        """Players property setter"""
        self._players = players
        self._num_players = len(players.keys())

    async def dm_players(self, content: dict, player_ids: list, ipipeline=None) -> dict:
        """Convenience method to send a message to a list of players.

        :param content: Embed content to send.
        :param player_ids: List of player ids to send message to.
        :param interaction: Interaction specification
        :param ipipeline: Interaction pipeline
        :type ipipeline: :class:`interactive.InteractionPipeline`, Optional

        :return: Reply dictionary if interaction present, else `None`."""
        unique_content = {pid: content for pid in player_ids}
        return await self.dm_players_unique(unique_content, ipipeline=ipipeline)

    async def dm_players_unique(self, unique_content: dict, ipipeline=None) -> dict:
        """DM unique content to each player, indexed by player id.

        :param unique_content: Embed content to send to player, indexed by the
            player id.
        :param ipipeline: Interaction pipeline
        :type ipipeline: :class:`interactive.InteractionPipeline`, Optional

        :return: Reply dictionary if interaction present, else `None`.
        """

        tasks = []
        for pid, embed in unique_content.items():

            # get dm channel
            dm_channel = self.players[pid].dm_channel
            if not dm_channel:
                # else create
                dm_channel = await self.players[pid].create_dm()

            if ipipeline:
                self.logging.info(f"send_and_watch {dm_channel}")
                t = ipipeline.send_and_watch(dm_channel, embed, timeout=31)

            else:
                self.logging.info(f"send {dm_channel}")
                t = dm_channel.send(embed=embed)

            tasks.append(t)

        response_list = await asyncio.gather(*tasks)

        responses = dmerge(*response_list)
        self.logging.info(responses)

        # unpack
        if ipipeline:
            return responses["response"]
        else:
            return {}

    async def dm_all_players(self, content: dict, ipipeline=None) -> dict:
        """Convenience method to send a message to all players in the game.

        :param content: Embed content to send.
        :param ipipeline: Interaction pipeline
        :type ipipeline: :class:`interactive.InteractionPipeline`, Optional

        :return: Reply dictionary if interaction present, else `None`.
        """
        self.logging.info(f"DMing all players in {self.guild}")
        return await self.dm_players(content, self.players.keys(), ipipeline=ipipeline)

    async def _players_prompt(self) -> dict:
        """Creates a discord embed menu, which players are told to reply to if they
        want to join the game. Extracts the discord author instance, and returns a
        dictionary mapping:

            id -> author

        :return: Authors indexed by id.
        """
        embed = self.embed(
            f"{self.game_description}\n\nReply to this message to join the game."
        )

        # create reply reaction pipeline
        ipl = InteractionPipeline(ReplyInteraction())

        response = await ipl.send_and_watch(
            self.channel, embed, timeout=PLAYER_GATHER_TIMEOUT
        )
        return {k: v.author for (k, v) in response["response"]["reply"].items()}

    async def announce_ranking(self, result: list):
        """Presents the ranking of scores in `results` in a discord embed in the
        public channel of the guild.

        :param result: List of `vote` - `pid` pairs.
        """
        scoreboard = "Scores for this round:\n" + "\n".join(
            [f"{i[0]} votes for {self.players[i[1]]}" for i in result]
        )

        await self.channel.send(embed=self.embed(scoreboard))
        await asyncio.sleep(self.wait_duration)

    async def scoreboard(self):
        """TODO"""
        self.logging.info(self.state)
        tallied_scores = self.state["scores"]

        scores = sorted(
            [(pid, tallied_scores[pid]) for pid in self.players.keys()],
            key=lambda i: i[1],
            reverse=True,
        )
        scoreboard = [
            f"{i+1}. {self.players[t[0]]}: {t[1]}" for i, t in enumerate(scores)
        ]

        em = self.embed("**Global Scores:**\n" + "\n".join(scoreboard))
        em.set_thumbnail(
            url="http://www.bbc.co.uk/gloucestershire/content/images/2005/10/14/louis_theroux_150x180.jpg"
        )

        await self.channel.send(embed=em)

    # override
    async def stop(self):
        """Stop game"""
        ...

    # override
    async def start(self):
        """Main entry"""
        ...

    # override
    async def scrape(self, context) -> str:
        # pylint: disable=unused-argument
        ...

    async def _scrape_channel(self, context, channel_name: str, file_name: str) -> int:
        """TODO"""
        channel = next(filter(lambda c: c.name == channel_name, context.guild.channels))

        message_contents = []

        async for message in channel.history(limit=1000):
            try:
                message_contents.append(replace_rules(message.content))
            except Exception as e:
                self.logging.error(
                    f"Scraping error on {channel_name} in {context.guild.id}: {e}"
                )
                return f"Scraping error {e}."

        with open(file_name, "w") as f:
            f.write("\n".join(message_contents))
        return len(message_contents)

    async def gather_players(self) -> int:
        """Creates a player registration prompt, and returns the number of players
        that replied

        :return: Number of players registered.
        """
        self.logging.info("Calling gather players.")

        self.players = await self._players_prompt()

        self.logging.info(f"number of players {self._num_players}")

        return self._num_players

    async def check_continue(self, min_players: int = 1) -> bool:
        """
        Brings up a dialogue on the main channel to ask players whether they want to continue with
        same players, poll for new players or stop playing completely.

        :param min_players: the minimum number of players who need to join in order to continue.
            optional, defaults to 1
        """
        ipl = InteractionPipeline(
            ChoiceInteraction(
                f"Press {EMOJI_FORWARD['checkmark']} to vote to continue with the same players.",
                f"Press {EMOJI_FORWARD['busts-in-silhouette']} to vote to continue with new players.",
                f"Press {EMOJI_FORWARD['stop-sign']} to vote to stop the game.",
                max_votes=self._num_players,
            ).set_emojis(
                # custom emojis
                [
                    EMOJI_FORWARD["checkmark"],
                    EMOJI_FORWARD["busts-in-silhouette"],
                    EMOJI_FORWARD["stop-sign"],
                ]
            )
        )
        result = await ipl.send_and_watch(
            self.channel,
            self.embed(
                "Finished a round! Vote below to continue the game, change players, or stop the game."
            ),
            timeout=31,
        )
        response = result.get("response", {})
        buttons = response.get("choice", {})
        votes_to_continue = buttons.get("checkmark", 0)
        votes_to_change_players = buttons.get("busts-in-silhouette", 0)
        votes_to_stop = buttons.get("stop-sign", 0)
        # prioritise stop, change players and then continue
        if (
            votes_to_stop >= votes_to_change_players
            and votes_to_stop >= votes_to_continue
        ):
            return False
        elif votes_to_change_players >= votes_to_continue:
            # gather new players
            num_players = await self.gather_players()
            return num_players >= min_players
        else:
            return True

    def execute_rounds(max_rounds: int = 0, prompt_continue: bool = True):
        """
        Decorator method for games with multiple rounds, implementing optional checks at the end
        of each round as to whether player want to continue with same players, poll for new players
        or stop playing completely.
        Note that this will throw an error if max_rounds is set to 0 and prompt_continue is set to False,
        as this would represent infinite rounds with no way to stop.

        :param max_rounds: the maximum number of rounds to play. If set to 0, will have no maximum.
            optional, defaults to 0
        :param prompt_continue: whether to prompt users to continue. optional, defaults to True
        """
        # pylint: disable=no-self-argument

        def decorator(func):
            if max_rounds == 0 and not prompt_continue:
                raise Exception(
                    "Cannot call execute_rounds with max_rounds=-1 and prompt_continue=False - doing so would lead to infinite loop."
                )

            @wraps(func)
            async def wrapped_function(_self, *args, **kwargs):
                for round_number in count(1):
                    await func(_self, *args, **kwargs)
                    # check if max rounds exceeded
                    if max_rounds and round_number >= max_rounds:
                        break
                    # check if users wish to stop
                    if prompt_continue and not await _self.check_continue():
                        break

            return wrapped_function

        return decorator
