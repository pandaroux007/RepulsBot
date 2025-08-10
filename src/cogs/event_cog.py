"""
Below is the command error handling, bot startup and other discord events

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
# bot file
from cogs_list import CogsNames
from utils import (
    log, BOTLOG, LogColor
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

    # https://discord.com/developers/docs/reference#message-formatting
    # https://gist.github.com/LeviSnoot/d9147767abeef2f770e9ddcd91eb85aa
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                await log(
                    self.bot, color=LogColor.LEAVE,
                    title=f"🔨 {user.display_name} has been banned by {entry.user.mention}",
                    msg=f"{f"Reason: *{entry.reason}*, " if entry.reason else ""}On date: <t:{int(entry.created_at.timestamp())}:F>\nUser ID: {user.id}"
                )
                return

        await log(self.bot, color=LogColor.LEAVE, title=f"🔨 {user.display_name} has been banned, author undetermined.", msg=f"User ID: {user.id}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                await log(
                    self.bot, color=LogColor.LEAVE,
                    title=f"⛔️ {member.mention} has been kicked by {entry.user.mention}.",
                    msg=f"{f"Reason: *{entry.reason}*, " if entry.reason else ""}User ID: {member.id}"
                )
                return
    
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
                bot=self.bot, type=BOTLOG,
                title=f"{DefaultEmojis.ERROR} User {ctx.author.mention} tried to use the {ctx.command} command",
                msg=f"It failed with the error:\n`{error}`"
            )

        embed = discord.Embed(
            title=f"{DefaultEmojis.ERROR} Check failure!",
            description=f"{message}{ASK_HELP}",
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