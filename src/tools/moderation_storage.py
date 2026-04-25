from __future__ import annotations
import asqlite
import discord
from discord.ext import commands
from enum import Enum
from typing import (
    Any,
    Optional
)

from datetime import (
    datetime,
    timedelta
)

# bot files
from data.constants import DefaultEmojis
from tools.log_builder import (
    LogColor,
    BOTLOG,
    log
)

# memory cache lifetime (in minutes)
LIFETIME_SETTINGS_CACHE = 60
LIFETIME_CHANNEL_LOCK_CACHE = 30

class Settings(Enum):
    # NOTE: This class can accommodate settings other than those of the antiraid if needed.

    @property
    def default_value(self) -> Any:
        """ Default value of this setting (e.g., if it is not found during a `get`) """
        return self._value_[0]

    @property
    def typing(self) -> type:
        """ Everything in the db is text; this is the type in which the value should be once extracted """
        return self._value_[1]

    def get(self, settings: Optional[dict]) -> Any:
        """
        Must be called on a constant of the enum

        Parameters
        -----------
        settings: `Optional[dict]`
            Dictionary representation of the contents of the settings table, in which to search.

        Returns
        --------
        The (typed) value of this setting (and its default value if it does not exist)
        """
        if settings is None:
            return self.default_value
        return self._cast_value(settings.get(self.name, self.default_value), self.typing)

    @staticmethod
    def _cast_value(value: str, target_type: type = None) -> Any:
        """ Internal method for converting a database value into a typed python value """
        if isinstance(value, str):
            if target_type is bool:
                return value == '1' # 0/1 = SQL boolean
            if target_type is int:
                return int(value)
            if target_type is float:
                return float(value)
        return value # No value, value already in string format, etc.

    @classmethod
    def _from_key(cls, key: str) -> Settings | None:
        """ Internal method for finding a setting by its name (returns None otherwise) """
        try:
            return cls[key.strip().upper()]
        except KeyError:
            return None

    def _serialize(self, value: Any) -> str:
        """
        Must be called on a constant of the enum.
        This function is solely for converting Python booleans to SQL booleans (0/1).
        Any non-boolean value will simply be converted to a string.
        """
        value = self._cast_value(value, self.typing)
        if self.typing is bool:
            return '1' if value else '0'
        return str(value)

    # ---------------------------------- antiraid
    ANTIRAID_STATE = (1, bool) # antiraid enabled by default

    ANTIRAID_USER_MAX_TRIGGERS_BEFORE_MOD = (3, int) # max. number of triggers before auto-moderator action
    ANTIRAID_USER_MSG_SPAM_THRESHOLD = (4, int) # max. number of messages allowed within the given time
    ANTIRAID_USER_MSG_SPAM_INTERVAL_S = (2, int) # min. interval in which this quantity of message is allowed

    ANTIRAID_USER_CHANNEL_SPAM_THRESHOLD = (3, int) # number of messages from a user across multiple channels on which to perform sampling
    ANTIRAID_USER_CHANNEL_SPAM_INTERVAL_S = (ANTIRAID_USER_CHANNEL_SPAM_THRESHOLD[0] * 4, int) # 3s (margin of 1s) for 1 message per channel on average * number of messages

    ANTIRAID_CHANNEL_MAX_TRIGGERS_BEFORE_LOCK = (5, int)
    ANTIRAID_CHANNEL_LOCK_DURATION_MN = (30, int)
    ANTIRAID_CHANNEL_SPAM_INTERVAL_S = (5, int) # analysis interval (all users combined) for a channel
    ANTIRAID_CHANNEL_SPAM_THRESHOLD = (12, int) # max. number of messages allowed within the given interval

class ModerationStorage():
    def __init__(self, bot: commands.Bot, pool: asqlite.Pool):
        self._bot = bot
        self._pool = pool
        self._settings_cache: Optional[dict] = None
        self._last_settings_cache_update: Optional[datetime] = None
        self._channel_lock_cache: Optional[dict] = None
        self._last_channel_lock_cache_update: Optional[datetime] = None

    # ---------------------------------- settings cache
    @property
    def settings_cache(self) -> Optional[dict]:
        return self._settings_cache

    @settings_cache.setter
    def settings_cache(self, value: Optional[dict]) -> None:
        self._last_settings_cache_update = discord.utils.utcnow() if value is not None else None
        self._settings_cache = value

    @property
    def is_settings_cache_outdated(self) -> bool:
        if self._last_settings_cache_update is None or self.settings_cache is None:
            return True
        return self._last_settings_cache_update < (discord.utils.utcnow() - timedelta(minutes=LIFETIME_SETTINGS_CACHE))

    # ---------------------------------- channel lock cache
    @property
    def channel_lock_cache(self) -> Optional[dict]:
        return self._channel_lock_cache

    @channel_lock_cache.setter
    def channel_lock_cache(self, value: Optional[dict]) -> None:
        self._last_channel_lock_cache_update = discord.utils.utcnow() if value is not None else None
        self._channel_lock_cache = value

    @property
    def is_channel_lock_cache_outdated(self) -> bool:
        if self._last_channel_lock_cache_update is None or self._channel_lock_cache is None:
            return True
        return self._last_channel_lock_cache_update < (discord.utils.utcnow() - timedelta(minutes=LIFETIME_CHANNEL_LOCK_CACHE))

    # ---------------------------------- database management
    async def init_tables(self) -> None:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS report_cooldown (
                        user_id INTEGER PRIMARY KEY NOT NULL,
                        reports_today INTEGER NOT NULL DEFAULT 0,
                        last_reset TEXT NOT NULL DEFAULT (DATE('now'))
                    )
                    """
                )
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS channel_locks (
                        channel_id INTEGER PRIMARY KEY NOT NULL,
                        locked_until TEXT NOT NULL
                    )
                    """
                )
                # generate default settings (manage the transition from the old structure)
                existing_info = await conn.fetchall("PRAGMA table_info(settings)")
                old_values = {}
                if existing_info:
                    column_names = [row["name"] for row in existing_info]
                    if column_names != ["key", "value"]:
                        old_row = await conn.fetchone("SELECT * FROM settings WHERE id = 1")
                        if old_row:
                            old_values = dict(old_row)
                        await conn.execute("DROP TABLE IF EXISTS settings")

                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY NOT NULL,
                        value TEXT NOT NULL
                    )
                    """
                )
                await conn.executemany(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    [(setting.name, setting._serialize(setting.default_value)) for setting in Settings]
                )
                if old_values:
                    for setting in Settings:
                        key = setting.name
                        if key in old_values:
                            await conn.execute(
                                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                                (key, str(old_values[key]))
                            )
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.CRITICAL} CRITICAL ERROR - An exception was raised during init of moderation tables.", msg=f"```\n{e}\n```"
            )

    # ---------------------------------- anti-raid settings
    async def get_all_settings(self) -> Optional[dict[str, Any]]:
        """
        Returns
        --------
        Optional[`dict`]:
            A dictionary with the parameters (keys) and their current values
            (updates the cache if needed), otherwise None
        """
        if self.settings_cache is None or self.is_settings_cache_outdated:
            try:
                async with self._pool.acquire() as conn:
                    rows = await conn.fetchall("SELECT key, value FROM settings")
                    self.settings_cache = {}
                    for row in rows:
                        key = row["key"]
                        setting = Settings._from_key(key)
                        self.settings_cache[key] = Settings._cast_value(str(row["value"]), setting.typing if setting else None)
            except Exception as e:
                await log(
                    bot=self._bot, type=BOTLOG, color=LogColor.RED,
                    title=f"{DefaultEmojis.ERROR} Unable to retrieve settings", msg=f"➜ Settings cache set to `None`\n```\n{e}\n```"
                )
                self.settings_cache = None
        return self.settings_cache

    async def set_setting(self, action_author: discord.Member, param: Settings, value: Any) -> bool:
        """
        Allows you to modify the value of a parameter via its name

        Returns
        --------
        `bool`: True if successful, False otherwise
        """
        self.settings_cache = None
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (param.name, param._serialize(value))
                )
                await conn.commit()
                await self.get_all_settings()  # update cache
                return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error during settings update",
                msg=(f"Initiated by {action_author.mention}\n**Request**: `{param.name}` ➜ {value}\n**Error**:\n```\n{e}\n```")
            )
            return False

    async def reset_settings(self, action_author: discord.Member) -> bool:
        """
        Resets all settings to default values

        Returns
        --------
        `bool`: True if successful, False otherwise
        """
        self.settings_cache = None
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("DELETE FROM settings")
                await conn.executemany(
                    "INSERT INTO settings (key, value) VALUES (?, ?)",
                    [(setting.name, setting._serialize(setting.default_value)) for setting in Settings]
                )
                await conn.commit()
                await self.get_all_settings()  # update cache
                return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error resetting settings",
                msg=(f"Initiated by {action_author.mention}\n**Error**:\n```\n{e}\n```")
            )
            return False

    # ---------------------------------- channels lock
    async def load_channel_locks(self) -> Optional[dict]:
        """
        Returns
        --------
        Optional[`dict`]
            A dictionary of the locked channel IDs with the end-of-lock datetime,
            (updates the cache if needed), otherwise None
        """
        if self.channel_lock_cache is None or self.is_channel_lock_cache_outdated:
            try:
                async with self._pool.acquire() as conn:
                    rows = await conn.fetchall("SELECT channel_id, locked_until FROM channel_locks")
                    self.channel_lock_cache = {row[0]: datetime.fromisoformat(row[1]) for row in rows} if rows else None
            except Exception as e:
                await log(
                    bot=self._bot, type=BOTLOG, color=LogColor.RED, msg=(f"```\n{e}\n```"),
                    title=f"{DefaultEmojis.ERROR} Unable to retrieve the list of locked channels",
                )
                self.channel_lock_cache = None
        return self.channel_lock_cache

    async def get_channel_lock(self, channel_id: int) -> Optional[datetime]:
        """
        Parameters
        -----------
        channel_id: `int`
            The Discord ID of the channel to check

        Returns
        --------
        Optional[`datetime`]
            End-of-lock datetime if the channel is locked, otherwise None
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchone("SELECT locked_until FROM channel_locks WHERE channel_id = ?", (channel_id,))
                return datetime.fromisoformat(row[0]) if row else None
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Unable to obtain channel lock status",
                msg=(f"Requested channel: {channel_id}\n```\n{e}\n```")
            )
            return None

    async def set_channel_lock(self, channel_id: int, lock_until: datetime) -> bool:
        """
        Parameters
        -----------
        channel_id: `int`
            The Discord ID of the channel to save as locked
        duration_minutes: `int`
            Number of minutes of lock time (30 by default)

        Returns
        --------
        `bool`: True if successful, False otherwise
        """
        self.channel_lock_cache = None
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "INSERT OR REPLACE INTO channel_locks (channel_id, locked_until) VALUES (?, ?)",
                    (channel_id, lock_until.isoformat())
                )
                await conn.commit()
                await self.load_channel_locks() # update cache
                return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error saving channel lock",
                msg=(f"Requested channel: {channel_id})\n```\n{e}\n```")
            )
            return False

    async def del_channel_lock(self, channel_id: int) -> bool:
        """
        Parameters
        -----------
        channel_id: `int`
            The Discord ID of the channel to be deleted

        Returns
        --------
        `bool`: True if successful, False otherwise
        """
        self.channel_lock_cache = None
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("DELETE FROM channel_locks WHERE channel_id = ?", (channel_id,))
                await conn.commit()
                await self.load_channel_locks() # update cache
                return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Unable to delete a locked channel from the db",
                msg=(f"Requested channel: {channel_id})\n```\n{e}\n```")
            )
            return False

    # ---------------------------------- prevent abuses of reports
    async def get_reports_number(self, user_id: int) -> Optional[int]:
        try:
            async with self._pool.acquire() as conn:
                # automatic deletion of obsolete rows
                await conn.execute("DELETE FROM report_cooldown WHERE last_reset < DATE('now')")
                await conn.commit()
                row = await conn.fetchone(
                    "SELECT reports_today FROM report_cooldown WHERE user_id = ? AND last_reset = DATE('now')",
                    (user_id,)
                )
                return row[0] if row else 0
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED, msg=f"```\n{e}\n```",
                title=f"{DefaultEmojis.ERROR} Unable to obtain the number of reports for member `{user_id}`"
            )
            return None

    async def add_report_to_user(self, user_id: int) -> None:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO report_cooldown (user_id, reports_today) VALUES (?, 1)
                    ON CONFLICT(user_id) DO UPDATE SET
                        reports_today = reports_today + 1,
                        last_reset = DATE('now')
                    """,
                    (user_id,)
                )
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED, msg=f"```\n{e}\n```",
                title=f"{DefaultEmojis.ERROR} Unable to add a report to the user `{user_id}`"
            )