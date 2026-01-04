# https://github.com/Rapptz/discord.py/blob/master/examples/advanced_startup.py
import discord
from discord.ext import commands
import asyncio
# bot files
from data.cogs import COGS_LIST
from data.constants import (
    PrivateData,
    IDs,
    CMD_PREFIX
)
from tools.youtube_storage import YouTubeStorage

# ---------------------------------- bot creation
class RepulsBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.youtube_storage: YouTubeStorage | None = None

    async def setup_hook(self) -> None:
        self.youtube_storage = YouTubeStorage()
        await self.youtube_storage.init()

        for cog_name in COGS_LIST:
            await self.load_extension(f"cogs.{cog_name}")

        # sync of slash and hybrid commands
        synced = await self.tree.sync()
        print(f"{len(synced)} command(s) have been synchronized")

    async def close(self) -> None:
        if self.youtube_storage:
            await self.youtube_storage.close()

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