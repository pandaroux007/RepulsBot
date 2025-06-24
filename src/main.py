import discord
from discord.ext import commands
# bot file
from constants import *

# https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html
cogs_list = [EVENT_COG, SERVER_COG, ABOUT_COG, VOTE_COG]

# ---------------------------------- bot creation
class RepulsBot(commands.Bot):
    async def setup_hook(self):
        for cog_name in cogs_list:
            await self.load_extension(f"cogs.{cog_name}")

INTENTS = discord.Intents.all()
bot = RepulsBot(command_prefix=BOT_PREFIX, intents=INTENTS, help_command=None)

# ---------------------------------- bot run
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)