# https://github.com/Rapptz/discord.py/blob/master/examples/advanced_startup.py
import discord
from discord.ext import commands
import asyncio
import asqlite
# bot files
from data.cogs import COGS_LIST
from data.constants import (
    PrivateData,
    IDs,
    CMD_PREFIX
)
from data.constants import DB_PATH
from tools.youtube_storage import YouTubeStorage
from tools.tickets_storage import TicketsStorage

# ---------------------------------- bot creation
class RepulsBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_pool: asqlite.Pool | None = None
        self.youtube_storage: YouTubeStorage | None = None
        self.tickets_storage: TicketsStorage | None = None

    async def setup_database(self) -> None:
        self.db_pool = await asqlite.create_pool(DB_PATH)
        async with self.db_pool.acquire() as conn:
            # WAL by default : https://github.com/Rapptz/asqlite/blob/master/asqlite/__init__.py#L499
            await conn.execute("PRAGMA busy_timeout = 5000;")

        self.youtube_storage = YouTubeStorage(self.db_pool)
        await self.youtube_storage.init_tables()
        self.tickets_storage = TicketsStorage(self.db_pool)
        await self.tickets_storage.init_tables()

    async def setup_hook(self) -> None:
        await self.setup_database()

        for cog_name in COGS_LIST:
            await self.load_extension(f"cogs.{cog_name}")

        # sync of slash and hybrid commands
        synced = await self.tree.sync()
        print(f"{len(synced)} command(s) have been synchronized")

    async def close(self) -> None:
        await self.db_pool.close()
        await super().close()

async def main():
    INTENTS = discord.Intents.all()

    async with RepulsBot(
        command_prefix=CMD_PREFIX,
        intents=INTENTS,
        help_command=None,
        owner_id=IDs.repulsTeam.BOT_DEVELOPER
    ) as bot:
        await bot.start(PrivateData.DISCORD_TOKEN)

# ---------------------------------- bot run
if __name__ == "__main__":
    asyncio.run(main())