import discord
from datetime import datetime
# bot files
from tools.utils import BaseStorage
from data.constants import DEFAULT_DB_DIR

TICKETS_DB_PATH = DEFAULT_DB_DIR / "tickets.db"

class TicketsStorage(BaseStorage):
    def __init__(self):
        super().__init__()

    async def init(self) -> None:
        await super().init(TICKETS_DB_PATH)
        await self._conn.execute(
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
        await self._conn.commit()

    # ---------------------------------- posted videos
    async def add_ticket(self, name: str, title: str, author: discord.Member, open_log_url: str) -> bool:
        await self._check_init()
        try:
            now = discord.utils.utcnow().isoformat()
            await self._conn.execute(
                "INSERT OR IGNORE INTO tickets(name, created_at, title, author_id, open_log_url) VALUES(?, ?, ?, ?, ?)",
                (name, now, title, author.id, open_log_url)
            )
            await self._conn.commit()
            return True
        except Exception:
            return False
        
    async def get_ticket(self, name: str) -> dict:
        row = await self._conn.fetchone(
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
        await self._check_init()
        try:
            await self._conn.execute("DELETE FROM tickets WHERE name = ?", (name,))
            await self._conn.commit()
            return True
        except Exception:
            return False