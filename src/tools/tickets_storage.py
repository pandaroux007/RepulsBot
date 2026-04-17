import asqlite
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional
# bot files
from data.constants import DefaultEmojis
from tools.log_builder import (
    LogColor,
    BOTLOG,
    log
)

class TicketInfo():
    def __init__(self, name: str, title: str = None, created_at: datetime = None, author_id: int = None, open_log: str = None):
        self.name: str = name
        self.title: str = title or "*Unknown*"
        self.created_at: datetime | None = created_at
        self.author_id: int | None = author_id
        self.open_log_url: str | None = open_log

    @property
    def author(self) -> str:
        return f"<@{self.author_id}>" if self.author_id else "*Unknown*"
    
    @property
    def mention(self) -> str:
        return f"[`{self.name}`]({self.open_log_url})" if self.open_log_url else f"`{self.name}`"

class TicketsStorage():
    def __init__(self, bot: commands.Bot, pool: asqlite.Pool):
        self._bot = bot
        self._pool = pool

    async def init_tables(self) -> None:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tickets (
                        name TEXT PRIMARY KEY NOT NULL,
                        created_at TEXT NOT NULL,
                        title TEXT NOT NULL,
                        author_id INTEGER NOT NULL,
                        open_log_url TEXT NOT NULL
                    )
                    """
                )
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ticket_cooldown (
                        member_id INTEGER PRIMARY KEY NOT NULL,
                        cooldown_until TEXT NOT NULL
                    )
                    """
                )
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.CRITICAL} CRITICAL ERROR - An exception was raised during init of the ticketing system tables.", msg=f"```\n{e}\n```"
            )

    # ---------------------------------- manage tickets
    async def add_ticket(self, name: str, title: str, author: discord.Member, open_log_url: str, cooldown_hours: int) -> None:
        try:
            async with self._pool.acquire() as conn:
                now = discord.utils.utcnow()
                await conn.execute(
                    "INSERT OR REPLACE INTO tickets(name, created_at, title, author_id, open_log_url) VALUES(?, ?, ?, ?, ?)",
                    (name, now.isoformat(), title, author.id, open_log_url)
                )
                await conn.execute(
                    "INSERT OR REPLACE INTO ticket_cooldown(member_id, cooldown_until) VALUES(?, ?)",
                    (author.id, (now + timedelta(hours=cooldown_hours)).isoformat())
                )
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error during ticket registration `{name}`", msg=f"```\n{e}\n```"
            )

    async def get_ticket(self, name: str) -> TicketInfo:
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchone(
                    "SELECT name, created_at, title, author_id, open_log_url FROM tickets WHERE name = ?", (name,)
                )
                if not row:
                    return TicketInfo(name=name)

                name, created_at, title, author_id, open_log_url = row
                return TicketInfo(name, title, datetime.fromisoformat(created_at), author_id, open_log_url)
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Unable to retrieve ticket information `{name}`", msg=f"```\n{e}\n```"
            )
            return TicketInfo(name=name)

    async def remove_ticket(self, name: str) -> None:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("DELETE FROM tickets WHERE name = ?", (name,))
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Unable to delete ticket `{name}`", msg=f"```\n{e}\n```"
            )

    async def purge_cooldown_users(self) -> None:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("DELETE FROM ticket_cooldown WHERE cooldown_until < ?", (discord.utils.utcnow().isoformat(),))
                await conn.commit()
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} Error during the cleanup of users whose cooldown has expired", msg=(f"```\n{e}\n```")
            )

    # ---------------------------------- prevent ticket abuse
    async def is_ticket_allowed(self, member: discord.Member) -> tuple[bool, Optional[datetime]]:
        """
        Returns
        --------
        tuple[`bool`, `Optional[datetime]`]:
            - `False` if the member is not authorized, `True` if they are, or if an error occurs
            - If the member is not currently authorized, and if available, the date on which the cooldown ends
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchone(
                    "SELECT cooldown_until FROM ticket_cooldown WHERE member_id = ?", (member.id,)
                )
                if not row:
                    return (True, None)

                (cooldown_until_str,) = row
                cooldown_until_dt = datetime.fromisoformat(cooldown_until_str)
                if cooldown_until_dt < discord.utils.utcnow():
                    return (True, None)
                return (False, cooldown_until_dt)
        except Exception as e:
            await log(
                bot=self._bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} An error occurred during a cooldown test",
                msg=f"Tested member: {member.mention}\n```\n{e}\n```\n**He/she is enabled by default**"
            )
            return (True, None) # A bit risky in case of a database crash lol, but members are allowed by default