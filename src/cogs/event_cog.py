"""
Below is the command error handling, bot startup and other discord events

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
# bot files
from cogs_list import CogsNames
from utils import gettimestamp
from log_system import (
    LogBuilder,
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

    async def get_removed_attachments(self, before: discord.Message, after: discord.Message = None) -> list[discord.File] | None:
        """ returns the list of files deleted between before and after (or all if after is None) """
        if after is not None:
            after_urls = {a.url for a in after.attachments}
            removed = [a for a in before.attachments if a.url not in after_urls]
        else:
            removed = before.attachments
        files = []
        for attachment in removed:
            try:
                files.append(await attachment.to_file())
            except Exception:
                print("DEBUG > File recovery failed")
                pass
        return files or None

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
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        text_changed = before.content != after.content
        attachments_changed = await self.get_removed_attachments(before, after)
        if not text_changed and not attachments_changed:
            return
        
        builder = (
            LogBuilder(self.bot, color=LogColor.ORANGE)
            .m_title(f"✏️ Message from {after.author.mention} edited in {after.channel.mention} ")
            .description(f"[Jump to message]({after.jump_url})")
            .footer(f"User ID: {after.author.id}")
        )
        if text_changed:
            builder.add_field(name="Before", value=before.content or "*Empty*")
            builder.add_field(name="After", value=after.content or "*Empty*")
        if attachments_changed:
            builder.add_files(attachments_changed)
            builder.add_field(name="Attachments removed", value="\n".join(f.filename for f in attachments_changed))
        await builder.send()

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        files = await self.get_removed_attachments(message)
        builder = (
            LogBuilder(self.bot, color=LogColor.RED)
            .m_title(f"🗑️ Message sent by {message.author.mention} deleted in {message.channel.mention}")
            .description(f"**Content**: {message.content or "This message was empty"}")
            .footer(f"Author: {message.author.id} | Message ID: {message.id}")
        )
        if files:
            builder.add_files(files)
            builder.add_field(name="Attachments removed", value="\n".join(f.filename for f in files))
        await builder.send()

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                await (
                    LogBuilder(self.bot, color=LogColor.RED)
                    .m_title(f"🔨 {user.mention} has been banned by {entry.user.mention}")
                    .description(f"**On date** {gettimestamp(entry.created_at)}")
                    .add_field(name="Reason", value=entry.reason if entry.reason else "*no reason specified*")
                    .footer(f"User ID: {user.id}")
                    .send()
                )
                return

        await log(self.bot, color=LogColor.RED, title=f"🔨 {user.mention} has been banned", msg=f"User ID: {user.id}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.unban):
            if entry.target.id == user.id:
                await (
                    LogBuilder(self.bot, color=LogColor.GREEN)
                    .m_title(f"🔓 {user.mention} has been unbanned by {entry.user.mention}")
                    .description(f"**On date** {gettimestamp(entry.created_at)}")
                    .add_field(name="Reason", value=entry.reason if entry.reason else "*no reason specified*")
                    .footer(f"User ID: {user.id}")
                    .send()
                )
                return

        await log(self.bot, color=LogColor.GREEN, title=f"🔓 {user.mention} has been unbanned", msg=f"User ID: {user.id}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                await log(
                    self.bot, color=LogColor.RED,
                    title=f"⛔️ {member.mention} has been kicked by {entry.user.mention}.",
                    msg=f"{f"Reason: *{entry.reason}*\n" if entry.reason else ""}On date: {gettimestamp(entry.created_at)}\nUser ID: {member.id}"
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
                bot=self.bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} User {ctx.author.mention} tried to use the {ctx.command} command",
                msg=f"It failed with the error:\n`{error}`"
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