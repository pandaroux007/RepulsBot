"""
Below is the command error handling, bot startup and other discord events

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
# bot file
from cogs_list import CogsNames
from constants import (
    IDs,
    ASK_HELP
)

# ---------------------------------- event cog (see README.md)
class EventCog(commands.Cog, name=CogsNames.EVENT):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
            # log system
            log_channel = self.bot.get_channel(IDs.serverChannel.LOG)
            if log_channel is not None:
                await log_channel.send(f"User {ctx.author.mention} tried to use the {ctx.command} command, but it failed with the error:\n`{error}`", silent=True)

        error_emoji = await self.bot.fetch_application_emoji(IDs.customEmojis.DECONNECTE) or "❌"
        embed = discord.Embed(
            title=f"{error_emoji} Check failure!",
            description=f"{message}{ASK_HELP}",
            color=discord.Color.brand_red()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        # sync of slash and hybrid commands
        synced = await self.bot.tree.sync()
        print(f"{len(synced)} command(s) have been synchronized")
        
        status_channel = self.bot.get_channel(IDs.serverChannel.STATUS)
        if status_channel is not None:
            await status_channel.send(f"{self.bot.user.mention} is now **online**! {await self.bot.fetch_application_emoji(IDs.customEmojis.CONNECTE)}")
        
        game = discord.Game("🎮️ repuls.io browser game! 🕹️")
        await self.bot.change_presence(activity=game)

async def setup(bot: commands.Bot):
    await bot.add_cog(EventCog(bot))