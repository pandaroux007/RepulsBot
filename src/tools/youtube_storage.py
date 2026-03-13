from discord.ext import commands
import datetime
import asqlite
from typing import Optional
# bot files
from data.constants import DefaultEmojis
from tools.utils import plurial
from tools.log_builder import (
    LogColor,
    BOTLOG,
    log
)

class YouTubeStorage():
    def __init__(self, bot: commands.Bot, pool: asqlite.Pool):
        self._bot = bot
        self._pool = pool

    async def init_tables(self) -> None:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS posted_videos (
                        video_id TEXT PRIMARY KEY NOT NULL,
                        posted_at TEXT NOT NULL DEFAULT (DATETIME(CURRENT_TIMESTAMP))
                    )
                    """
                )
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS forced_video (
                        id INTEGER PRIMARY KEY NOT NULL CHECK (id = 1),
                        message_id INTEGER,
                        days_forced INTEGER,
                        forced_until TEXT
                    )
                    """
                )
                await conn.execute(
                    "INSERT OR IGNORE INTO forced_video(id, message_id, days_forced, forced_until) VALUES(1, NULL, NULL, NULL)"
                )
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.CRITICAL} CRITICAL ERROR - An exception was raised during init of the video system tables", msg=f"```\n{e}\n```"
            )

    async def reset_table(self) -> bool:
        """
        Returns
        --------
        `bool`: True if successful, False otherwise
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("DROP TABLE posted_videos")
                await conn.execute("DROP TABLE forced_video")
                await conn.commit()
            await self.init_tables()
            return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.CRITICAL} CRITICAL ERROR - An exception was raised during reset of the video system tables", msg=f"```\n{e}\n```"
            )
            return False

    # ---------------------------------- posted videos
    # https://stackoverflow.com/questions/12876177/how-to-create-a-singleton-tuple-with-only-one-element
    async def add_posted_video(self, video_id: str) -> bool:
        """
        Parameters
        -----------
        video_id: `str`
            the YouTube ID of the video

        Returns
        --------
        `bool`
            True if inserted (was new), False if it already existed or error
        """
        try:
            async with self._pool.acquire() as conn:
                exists_cur = await conn.execute("SELECT 1 FROM posted_videos WHERE video_id = ?", (video_id,))
                if await exists_cur.fetchone():
                    return False
                await conn.execute("INSERT INTO posted_videos(video_id) VALUES(?)", (video_id,))
                await conn.commit()
                return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error during the addition of an automatically posted video",
                msg=(f"*YouTube video ID: {video_id}*\n```\n{e}\n```")
            )
            return False

    async def purge_old_posted_videos(self, days: int) -> None:
        try:
            async with self._pool.acquire() as conn:
                # https://sqlite.org/lang_datefunc.html
                # https://sqlite.fr/fonctions-date/#manipuler-les-dates-avec-des-modificateurs
                # https://stackoverflow.com/questions/23372550/what-does-sql-select-symbol-mean
                await conn.execute("DELETE FROM posted_videos WHERE DATETIME(posted_at) < DATETIME('now', '-' || ? || ' days')", (days,))
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error during the purging of posted videos", msg=(f"```\n{e}\n```")
            )

    # ---------------------------------- featured forced video
    async def set_forced_video(self, message_id: int, days: int) -> bool:
        """
        Parameters
        -----------
        message_id: `int`
            the Discord ID of the message containing the link to the video to force
        days: `int`
            the number of days the video must be forced

        Returns
        --------
        `bool`: True if successful, False otherwise
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "UPDATE forced_video SET message_id = ?, days_forced = ?, forced_until = NULL WHERE id = 1",
                    (message_id, days)
                )
                await conn.commit()
                return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error during forced video saving",
                msg=(f"Video message ID: {message_id} ({days} {plurial("day", days)})\n```\n{e}\n```")
            )
            return False

    async def activate_forced_video(self) -> Optional[datetime.datetime]:
        """
        Returns
        --------
        Optional[`datetime.datetime`]
            forced_until based on days_forced when the video is actually activated, `None` otherwise
        """
        try:
            async with self._pool.acquire() as conn:
                cur = await conn.execute(
                    "SELECT days_forced FROM forced_video WHERE id = 1 AND message_id IS NOT NULL AND forced_until IS NULL"
                )
                row = await cur.fetchone()
                if not row or not row[0]:
                    return None # No video is currently being forced or it is already activated

                days = row[0]
                forced_until_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)

                await conn.execute(
                    "UPDATE forced_video SET forced_until = ? WHERE id = 1",
                    (forced_until_dt.isoformat(),)
                )
                await conn.commit()
                return forced_until_dt
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error during forced video activation", msg=(f"```\n{e}\n```")
            )
            return None

    async def get_forced_video(self) -> tuple[Optional[int], Optional[int], Optional[datetime.datetime]]:
        """
        Returns
        --------
        tuple[`Optional[int]`, `Optional[int]`, `Optional[datetime]`]
            - Tuple with three `None` if no video is currently being forced
            - Otherwise, it returns the discord ID of the message containing the forced video, the number
            of days the force was in effect, and the expiration date of the force if the video was activated (otherwise `None`)
        """
        try:
            async with self._pool.acquire() as conn:
                cur = await conn.execute("SELECT message_id, days_forced, forced_until FROM forced_video WHERE id = 1")
                row = await cur.fetchone()
                if not row:
                    return (None, None, None) # No forced videos currently

                message_id, days_forced, forced_until_str = row
                forced_until_dt = datetime.datetime.fromisoformat(forced_until_str) if forced_until_str else None
                return (message_id, days_forced, forced_until_dt)
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Unable to get the currently forced video from db", msg=(f"```\n{e}\n```")
            )
            return (None, None, None)

    async def clear_forced_video(self) -> bool:
        """
        Returns
        --------
        `bool`: True if successful, False otherwise
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("UPDATE forced_video SET message_id = NULL, days_forced = NULL, forced_until = NULL WHERE id = 1")
                await conn.commit()
                return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error during forced video deletion from db", msg=(f"```\n{e}\n```")
            )
            return False