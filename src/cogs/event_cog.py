"""
Below is the command error handling, bot startup and other discord events

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
# bot files
from cogs_list import CogsNames
from log_system import (
    LogColor,
    BOTLOG,
    log
)

from constants import (
    IDs,
    DefaultEmojis,
    ASK_HELP,
    AUTHORISED_SERVERS
)

# ---------------------------------- event cog (see README.md)
class EventCog(commands.Cog, name=CogsNames.EVENT):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if guild.id not in AUTHORISED_SERVERS:
            await guild.leave()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        elif message.channel.id == IDs.serverChannel.RULES:
            await message.channel.send(message.content)
            await message.delete()
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        message = f"*Unknown error:* {error}" # default

        if isinstance(error, commands.CheckFailure):
            message = "You do not have permission to use this command!"
        elif isinstance(error, commands.MissingRequiredArgument):
            message = "Missing argument!"
        elif isinstance(error, commands.CommandNotFound):
            return # do nothing
        else:
            await log(
                bot=self.bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} User {ctx.author.mention} tried to use the `{ctx.command}` command",
                msg=f"It failed with the error:\n```\n{error}\n```"
            )

        embed = discord.Embed(
            title=f"{DefaultEmojis.ERROR} Check failure!",
            description=f"> {message}{ASK_HELP}",
            color=discord.Color.brand_red()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        # sync of slash and hybrid commands
        synced = await self.bot.tree.sync()
        print(f"{len(synced)} command(s) have been synchronized")
        
        await log(bot=self.bot, title=f"{self.bot.user.mention} is now online! 🟢", type=BOTLOG)
        
        game = discord.Game("🎮️ repuls.io browser game! 🕹️")
        await self.bot.change_presence(activity=game)

async def setup(bot: commands.Bot):
    await bot.add_cog(EventCog(bot))