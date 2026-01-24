import asqlite
import discord
from datetime import datetime

class TicketsStorage():
    def __init__(self, pool: asqlite.Pool):
        self._pool = pool

    async def init_tables(self) -> None:
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
            await conn.commit()

    async def reset_table(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DROP TABLE tickets")
            await conn.commit()
        await self.init_tables()

    # ---------------------------------- posted videos
    async def add_ticket(self, name: str, title: str, author: discord.Member, open_log_url: str) -> bool:
        try:
            async with self._pool.acquire() as conn:
                now = discord.utils.utcnow().isoformat()
                await conn.execute(
                    "INSERT OR IGNORE INTO tickets(name, created_at, title, author_id, open_log_url) VALUES(?, ?, ?, ?, ?)",
                    (name, now, title, author, open_log_url)
                )
                await conn.commit()
                return True
        except Exception:
            return False
        
    async def get_ticket(self, name: str) -> dict:
        async with self._pool.acquire() as conn:
            row = await conn.fetchone(
                "SELECT name, created_at, title, author_id, open_log_url FROM tickets WHERE name = ?", (name,)
            )
            if not row:
                return {}
        
            name, created_at, title, author_id, open_log_url = row
            return {
                "name": name,
                "created_at": datetime.fromisoformat(created_at),
                "title": title,
                "author_id": author_id,
                "open_log_url": open_log_url,
            }

    async def remove_ticket(self, name: int) -> bool:
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("DELETE FROM tickets WHERE name = ?", (name,))
                await conn.commit()
                return True
        except Exception:
            return False