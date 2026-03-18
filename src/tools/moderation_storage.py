import asqlite
import discord
from discord.ext import commands
from typing import Optional
from datetime import (
    datetime,
    timedelta
)

# bot files
from data.constants import (
    DefaultEmojis,
    DefaultAntiraidSettings
)

from tools.log_builder import (
    LogColor,
    BOTLOG,
    log
)

# memory cache lifetime (in minutes)
LIFETIME_SETTINGS_CACHE = 60
LIFETIME_CHANNEL_LOCK_CACHE = 30

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
        self._last_settings_cache_update = discord.utils.utcnow() if value else None
        self._settings_cache = value

    @property
    def is_settings_cache_outdated(self) -> bool:
        if not self._last_settings_cache_update or not self.settings_cache:
            return True
        return self._last_settings_cache_update < (discord.utils.utcnow() - timedelta(minutes=LIFETIME_SETTINGS_CACHE))

    # ---------------------------------- channel lock
    @property
    def channel_lock_cache(self) -> Optional[dict]:
        return self._channel_lock_cache

    @channel_lock_cache.setter
    def channel_lock_cache(self, value: Optional[dict]) -> None:
        self._last_channel_lock_cache_update = discord.utils.utcnow() if value else None
        self._channel_lock_cache = value

    @property
    def is_channel_lock_cache_outdated(self) -> bool:
        if not self._last_channel_lock_cache_update or not self._channel_lock_cache:
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
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY NOT NULL CHECK (id = 1),
                        antiraid_enabled BOOLEAN NOT NULL DEFAULT {DefaultAntiraidSettings.ANTIRAID_STATE},
                        user_max_repeat_before_mod INTEGER DEFAULT {DefaultAntiraidSettings.USER_MAX_TRIGGERS_BEFORE_MOD},
                        user_msg_spam_threshold INTEGER DEFAULT {DefaultAntiraidSettings.USER_MSG_SPAM_THRESHOLD},
                        user_msg_spam_interval_s INTEGER DEFAULT {DefaultAntiraidSettings.USER_MSG_SPAM_INTERVAL_S},
                        channel_lock_duration_mn INTEGER DEFAULT {DefaultAntiraidSettings.CHANNEL_LOCK_DURATION_MN},
                        channel_max_triggers_before_lock INTEGER DEFAULT {DefaultAntiraidSettings.CHANNEL_MAX_TRIGGERS_BEFORE_LOCK},
                        channel_triggers_interval_s INTEGER DEFAULT {DefaultAntiraidSettings.CHANNEL_TRIGGERS_INTERVAL_S}
                    )
                    """
                )
                await conn.execute("INSERT OR IGNORE INTO settings(id) VALUES(1)")
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.CRITICAL} CRITICAL ERROR - An exception was raised during init of moderation tables.", msg=f"```\n{e}\n```"
            )

    async def reset_table(self) -> bool:
        """
        Returns
        --------
        `bool`: True if successful, False otherwise
        """
        try:
            async with self._pool.acquire() as conn:
                self.settings_cache = None
                await conn.execute("DROP TABLE automod_chat")
                await conn.execute("DROP TABLE settings")
                await conn.execute("DROP TABLE channel_locks")
                await conn.commit()
            await self.init_tables()
            return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.CRITICAL} CRITICAL ERROR - An exception was raised during reset of moderation tables.", msg=f"```\n{e}\n```"
            )
            return False

    # ---------------------------------- anti-raid settings
    async def get_antiraid_settings(self) -> Optional[dict]:
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
                    row = await conn.fetchone("SELECT * FROM settings WHERE id = 1")
                    self.settings_cache = dict(row) if row else None
            except Exception as e:
                await log(
                    bot=self._bot, type=BOTLOG, color=LogColor.RED,
                    title=f"{DefaultEmojis.ERROR} Unable to retrieve antiraid settings", msg=f"```\n{e}\n```"
                )
                self.settings_cache = None
        return self.settings_cache

    async def set_antiraid_state(self, action_author: discord.Member, state: bool = True) -> bool:
        """
        Enables or disables antiraid system

        Returns
        --------
        `bool`: True if successful, False otherwise
        """
        self.settings_cache = None
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("UPDATE settings SET antiraid_enabled = ? WHERE id = 1", (1 if state else 0,))
                await conn.commit()
                await self.get_antiraid_settings() # update cache
                return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error during saving the state of the antiraid",
                msg=(f"Initiated by {action_author.mention} (requested state: {"enabled" if state else "disabled"})\n```\n{e}\n```")
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
            end-of-lock datetime if the channel is locked, otherwise None
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchone("SELECT locked_until FROM channel_locks WHERE channel_id = ?", (channel_id,))
                return datetime.fromisoformat(row[0]) if row else None
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Unable to obtain channel lock status",
                msg=(f"Requested channel: {channel_id})\n```\n{e}\n```")
            )
            return None

    async def set_channel_lock(self, channel_id: int, duration_minutes: int = 30) -> bool:
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
                    """INSERT OR REPLACE INTO channel_locks (channel_id, locked_until)
                    VALUES (?, DATETIME('now', '+' || ? || ' minutes'))""",
                    (channel_id, duration_minutes)
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