"""
This cog contains events dedicated only to logs

Moderation logs are dedicated to events that may be useful to admins, such as
message deletion/editing. Since the bot is not an admin, it will only
log events from channels to which it has access; staff-only channels are not
logged unless the bot is explicitly added.

Bot logs are less critical than the moderation logs, it contains messages from the bot;
when it goes live, when an error occurs, ticket opening/closing, etc.

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
# bot files
from data.cogs import CogsNames
from tools.utils import number
from data.constants import (
    DefaultEmojis,
    IDs,
    ASK_HELP,
    AUTHORISED_SERVERS
)

from tools.log_builder import (
    LogBuilder,
    LogColor,
    log,
    BOTLOG
)

async def get_removed_attachments(before: discord.Message, after: discord.Message = None) -> list[discord.File] | None:
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

class LogCog(commands.Cog, name=CogsNames.LOG):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------------------------- bot operation
    @commands.Cog.listener()
    async def on_ready(self):
        await log(bot=self.bot, type=BOTLOG, title=f"{self.bot.user.mention} is now online! {DefaultEmojis.ONLINE}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if guild.id not in AUTHORISED_SERVERS:
            await guild.leave()

    # ---------------------------------- error handling
    def cog_load(self):
        tree = self.bot.tree
        self._old_tree_error = tree.on_error # optional
        tree.on_error = self.on_app_command_error

    def cog_unload(self):
        tree = self.bot.tree
        tree.on_error = self._old_tree_error

    async def handle_command_error(self, source: commands.Context | discord.Interaction, error: discord.DiscordException):
        message = f"*Unknown error:* {error}" # default

        if isinstance(error, commands.CommandNotFound):
            return # do nothing
        elif isinstance(error, (commands.CheckFailure, app_commands.errors.CheckFailure)):
            message = "You do not have permission to use this command!"
        elif isinstance(error, commands.NotOwner):
            message = "Only the bot maintainer can use this command!"
        elif isinstance(error, commands.MissingRequiredArgument):
            message = "Missing argument!"
        else:
            author = source.author.mention if isinstance(source, commands.Context) else source.user.mention
            await log(
                bot=self.bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} User {author} tried to use the `{source.command.name}` command",
                msg=f"It failed with the error:\n```\n{error}\n```"
            )

        embed = discord.Embed(
            title=f"{DefaultEmojis.ERROR} Oh! We're sorry, but something went wrong...",
            description=f"> {message}{ASK_HELP}",
            color=discord.Color.brand_red()
        )
        if isinstance(source, commands.Context):
            embed.set_footer(text="This message will disappear in 20 seconds")
            await source.send(embed=embed, delete_after=20)
        elif isinstance(source, discord.Interaction):
            if source.response.is_done():
                await source.followup.send(embed=embed, ephemeral=True)
            else:
                await source.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await self.handle_command_error(ctx, error)

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await self.handle_command_error(interaction, error)

    # ---------------------------------- administration
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        text_changed = before.content != after.content
        attach_removed = await get_removed_attachments(before, after)
        if not text_changed and not attach_removed:
            return

        builder = (
            LogBuilder(self.bot, color=LogColor.ORANGE)
            .title(f"✏️ Message from {after.author.mention} edited in {after.channel.mention} ")
            .description(f"[Jump to message]({after.jump_url})")
            .footer(f"Message ID: {after.id}")
        )
        before_text = before.content if before.content else "*Contained only media*" if before.attachments else "*Empty*"
        if text_changed:
            builder.add_field(name="Before", value=before_text)
            builder.add_field(name="After", value=after.content or "*Empty*")
        if attach_removed:
            builder.add_media(title="Attachments removed", files=attach_removed)
        await builder.send()

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        attachments = await get_removed_attachments(message)
        responded_to = message.reference if message.type == discord.MessageType.reply else None
        builder = (
            LogBuilder(self.bot, color=LogColor.RED)
            .title(f"🗑️ Message sent by {message.author.mention} deleted in {message.channel.mention}")
            .add_field(name="Content:", value=(message.content or "*This message was empty*"))
            .footer(f"Message ID: {message.id}")
        )
        if responded_to:
            builder.description(f"This message was a reply to {responded_to.jump_url}")
        if attachments:
            builder.add_media(title="Attachments of the deleted message", files=attachments)
        await builder.send()

    # ---------------------------------- welcome message
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        welcome_channel: discord.PartialMessageable = self.bot.get_partial_messageable(IDs.serverChannel.WELCOME)
        rules_channel: discord.PartialMessageable = self.bot.get_partial_messageable(IDs.serverChannel.RULES)
        verification_channel: discord.PartialMessageable = self.bot.get_partial_messageable(IDs.serverChannel.VERIFICATION)
        await welcome_channel.send(content=(
            f"Welcome {member.mention} ({number(member.guild.member_count)} member)! "
            f"Please complete the captcha at {verification_channel.jump_url} and read {rules_channel.jump_url}, then have fun!"
        ))

async def setup(bot: commands.Bot):
    await bot.add_cog(LogCog(bot))