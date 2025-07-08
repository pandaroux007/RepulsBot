import discord
from discord.ext import commands
# bot file
from cogs.cogs_info import COGS_LIST
from constants import (
    PrivateData,
    CMD_PREFIX
)

# ---------------------------------- bot creation
class RepulsBot(commands.Bot):
    async def setup_hook(self):
        for cog_name in COGS_LIST:
            await self.load_extension(f"cogs.{cog_name}")

INTENTS = discord.Intents.all()
bot = RepulsBot(command_prefix=CMD_PREFIX, intents=INTENTS, help_command=None)

# ---------------------------------- bot run
if __name__ == "__main__":
    bot.run(PrivateData.DISCORD_TOKEN)