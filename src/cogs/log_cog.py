"""
This cog contains events dedicated only to logs

### moderation logs
Moderation logs are dedicated to events that may be useful to admins, such as:
- message deletions and modifications,
- automod actions (logged by discord, not the bot), purges,
- kicked or banned users, or when a timeout is applied,
- changes to roles are also logged.

Since the bot is not an admin, it will only log events from channels to which it has access;
staff-only channels are not logged unless the bot is explicitly added.

### bot logs
This channel is less critical than the moderation logs; it contains messages from the bot:
- when it goes live,
- when an error occurs on an order,
- when a ticket is opened or closed.

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
# bot files
from cogs_list import CogsNames
from utils import (
    plurial,
    possessive
)

from log_system import (
    LogBuilder,
    LogColor,
    log
)

# ---------------------------------- event cog (see README.md)
class LogCog(commands.Cog, name=CogsNames.LOG):
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
                pass
        return files or None

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await (
            LogBuilder(self.bot, color=LogColor.RED)
            .title(f"🗑️ Role deleted: `{role.name}`")
            .footer(f"Role ID: {role.id}")
            .send()
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        changes = []
        if before.name != after.name:
            changes.append(f"Name: `{before.name}` changed to `{after.name}`")
        if before.color != after.color:
            changes.append(f"Color: `{before.color}` changed to `{after.color}`")
        
        if changes:
            await (
                LogBuilder(self.bot, color=LogColor.ORANGE)
                .title(f"🎭️ The role {after.mention} has been changed on the server")
                .description("\n".join(changes))
                .footer(f"Role ID: {after.id}")
                .send()
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        text_changed = before.content != after.content
        attach_removed = await self.get_removed_attachments(before, after)
        if not text_changed and not attach_removed:
            return
        
        builder = (
            LogBuilder(self.bot, color=LogColor.ORANGE)
            .title(f"✏️ Message from {after.author.mention} edited in {after.channel.mention} ")
            .description(f"[Jump to message]({after.jump_url})")
            .footer(f"Message ID: {after.id}")
        )
        if text_changed:
            builder.add_field(name="Before", value=before.content or "*Empty*")
            builder.add_field(name="After", value=after.content or "*Empty*")
        if attach_removed:
            builder.add_media(title="Attachments removed", files=attach_removed)
        await builder.send()

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        attachments = await self.get_removed_attachments(message)
        builder = (
            LogBuilder(self.bot, color=LogColor.RED)
            .title(f"🗑️ Message sent by {message.author.mention} deleted in {message.channel.mention}")
            .add_field(name="Content:", value=(message.content or "*This message was empty*"))
            .footer(f"Message ID: {message.id}")
        )
        if attachments:
            builder.add_media(title="Attachments of the deleted message", files=attachments)
        await builder.send()

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # ---------------------------------- roles log
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        added_roles = after_roles - before_roles
        removed_roles = before_roles - after_roles
        
        if added_roles or removed_roles or before.display_name != after.display_name:
            builder = (
                LogBuilder(self.bot, color=LogColor.ORANGE)
                # mention being a string "<@id>", the function returns 's by default
                .title(f"🎭️ {possessive(after.mention)} profile has been updated")
                .footer(f"User ID: {after.id}")
            )
            if before.display_name != after.display_name:
                builder.add_field(name="Nickname changed", value=f"**Before: **{before.display_name}\n**After: **{after.display_name}")
            if added_roles:
                builder.add_field(name=f"Added role{plurial(added_roles)}", value=", ".join(role.mention for role in added_roles))
            if removed_roles:
                builder.add_field(name=f"Lost role{plurial(removed_roles)}", value=", ".join(role.mention for role in removed_roles))
            
            await builder.send()
        # ---------------------------------- mute and unmute (discord timeout) system
        if before.timed_out_until != after.timed_out_until:
            entry = None
            async for e in after.guild.audit_logs(limit=10, action=discord.AuditLogAction.member_update):
                if e.target.id == after.id:
                    before_val = getattr(e.changes.before, "timed_out_until", None)
                    after_val = getattr(e.changes.after, "timed_out_until", None)
                    if before_val != after_val:
                        entry = e
                        break

            admin = entry.user if entry else None
            reason = entry.reason if entry else None
            is_muted = after.timed_out_until and (before.timed_out_until is None or before.timed_out_until < discord.utils.utcnow())
            
            mute_log = (
                LogBuilder(self.bot, color=LogColor.RED if is_muted else LogColor.GREEN)
                .title((f"🔇 {after.mention} was muted" if is_muted else f"🔊 {after.mention} was unmuted") + " (*discord timeout*)")
                .description(f"**Duration:** until {discord.utils.format_dt(after.timed_out_until, "F")}" if is_muted else None)
                .footer(f"ID: {after.id}")
            )
            if admin:
                mute_log.add_field(name="Admin", value=admin.mention)
            if reason:
                mute_log.add_field(name="Reason", value=reason)
            await mute_log.send()
    
    # ---------------------------------- members
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                await (
                    LogBuilder(self.bot, color=LogColor.RED)
                    .title(f"🔨 {user.mention} has been banned by {entry.user.mention}")
                    .description(f"**On date** {discord.utils.format_dt(entry.created_at, "F")}")
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
                    .title(f"🔓 {user.mention} has been unbanned by {entry.user.mention}")
                    .description(f"**On date** {discord.utils.format_dt(entry.created_at, "F")}")
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
                await (
                    LogBuilder(self.bot, color=LogColor.RED)
                    .title(f"⛔️ {member.mention} has been kicked by {entry.user.mention}")
                    .description(f"**On date** {discord.utils.format_dt(entry.created_at, "F")}")
                    .add_field(name="Reason", value=entry.reason if entry.reason else "*no reason specified*")
                    .footer(f"User ID: {member.id}")
                    .send()
                )
                return

async def setup(bot: commands.Bot):
    await bot.add_cog(LogCog(bot))