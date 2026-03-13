import asqlite
from discord.ext import commands
from typing import Optional
# bot files
from data.constants import DefaultEmojis
from tools.log_builder import (
    LogColor,
    BOTLOG,
    log
)

class ModerationStorage():
    def __init__(self, bot: commands.Bot, pool: asqlite.Pool):
        self._bot = bot
        self._pool = pool

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
                await conn.execute("DROP TABLE automod_chat")
                await conn.commit()
            await self.init_tables()
            return True
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.CRITICAL} CRITICAL ERROR - An exception was raised during reset of moderation tables.", msg=f"```\n{e}\n```"
            )
            return False

    # ---------------------------------- prevent abuses of reports
    async def get_reports_number(self, user_id: int) -> Optional[int]:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("DELETE FROM report_cooldown WHERE last_reset < DATE('now')")
                cursor = await conn.execute(
                    "SELECT reports_today FROM report_cooldown WHERE user_id = ? AND last_reset = DATE('now')",
                    (user_id,)
                )
                result = await cursor.fetchone()
                count = result[0] if result else 0
                await conn.commit()
                return count
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Unable to obtain the number of reports for member `{user_id}`", msg=f"```\n{e}\n```"
            )
            return None

    async def add_report_to_user(self, user_id: int) -> None:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO report_cooldown (user_id, reports_today) VALUES (?, 1)
                    ON CONFLICT(user_id) DO UPDATE SET reports_today = reports_today + 1
                    """,
                    (user_id,)
                )
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Unable to add a report to the user `{user_id}`", msg=f"```\n{e}\n```"
            )