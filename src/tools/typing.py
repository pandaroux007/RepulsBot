"""
Abstraction layer for manipulating game data

:copyright: (c) 2026-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

from __future__ import annotations
import aiohttp
from enum import Enum
# bot files
from data.constants import DefaultEmojis
from tools.api_client import PublicAPI

# Chap. 8.13.8: https://docs.python.org/3.5/library/enum.html#allowed-members-and-attributes-of-enumerations
# Example (8.13.13.4): https://docs.python.org/3.5/library/enum.html#planet
class GamePlaylist(Enum):
    """
    Provided the complete list of available "game modes" (playlist) + search functions
    """
    WARFARE = ("wf", "Warfare", "Team play and vehicle based maps")
    HARDCORE = ("hc", "Hardcore", "Arena maps, no vehicles")
    CASUAL = ("ws", "Casual", "Crasy modes focused on fun")
    CUSTOMS = ("cm", "Customs", "User created modes")

    def __init__(self, code: str, label: str, desc: str):
        self.code: str = code
        self.label: str = label
        self.description: str = desc

    def __str__(self):
        return self.label

    @classmethod
    def from_code(cls, code: str) -> GamePlaylist | None:
        code = code.lower()
        for pl in cls:
            if pl.code == code:
                return pl
        return None

class GameRegion:
    """
    Represents one of the game's servers (usually specific to a region of the world)
    """
    def __init__(self, name: str, players: dict[GamePlaylist, int] | None = None):
        self.name: str = name
        self.players: dict[GamePlaylist, int] = players or {}
        self._status: str | None = None
    
    def __eq__(self, value: str):
        return self.name == value

    @property
    def total(self) -> int:
        """
        Returns the total number of players on this server (across all playlists).
        """
        return sum(self.players.values())

    def get(self, playlist: GamePlaylist) -> int:
        """
        Returns the number of players for a playlist (0 if it doesn't exist) on this server
        """
        return self.players.get(playlist, 0)

    @property
    async def status(self) -> str:
        if not self._status:
            try:
                PING_URL = PublicAPI.REGION_PING.format(region=self.name)
                async with aiohttp.ClientSession() as session:
                    async with session.get(PING_URL, timeout=3) as resp_ping:
                        if resp_ping.status == 200:
                            data = await resp_ping.json(content_type=None)
                            if isinstance(data, dict) and data.get("status") == "ok":
                                self._status = f"{DefaultEmojis.ONLINE} Online"
                            else:
                                self._status = "🟡 Down"
                        else:
                            self._status = f"{DefaultEmojis.OFFLINE} Unavailable"
            except Exception:
                self._status = f"{DefaultEmojis.NO_ENTRY} Error"
        return self._status

class GameInProgress:
    """
    Represents an ongoing game session (with its map, mode, players, etc.)
    """
    def __init__(self, name: str, map: str, mode: str, players: int, max_players: int, port: int):
        self.name: str = name
        self.map: str = map
        self.mode: str = mode
        self.web_port: int = port
        self._players: int = players
        self._max_players: int = max_players

    @property
    def players(self) -> str:
        """
        Player representation in the form "current players/max players"
        """
        return f"{self._players}/{self._max_players}"

    @property
    def is_full(self) -> bool:
        return self._players == self._max_players

    @property
    def is_empty(self) -> bool:
        return self._players == 0