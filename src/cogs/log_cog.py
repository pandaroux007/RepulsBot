"""
This cog contains events dedicated only to logs

Moderation logs are dedicated to events that may be useful to admins, such as
message deletions or modifications. Since the bot is not an admin, it will only
log events from channels to which it has access; staff-only channels are not
logged unless the bot is explicitly added.

Bot logs are less critical than the moderation logs; it contains messages from the bot:
- when it goes live,
- when an error occurs on an order,
- when a ticket is opened or closed.

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
# bot files
from data.cogs import CogsNames
from tools.log_builder import (
    LogBuilder,
    LogColor
)

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

async def setup(bot: commands.Bot):
    await bot.add_cog(LogCog(bot))