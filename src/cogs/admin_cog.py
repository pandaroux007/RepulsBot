"""
This cog contains all the commands accessible only to server admins

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
import re
# bot files
from data.cogs import CogsNames
from tools.utils import plurial
from data.constants import (
    DefaultEmojis,
    IDs,
    ADMIN_CMD,
    DISCORD_MSG_ID_REGEX,
    ASK_HELP
)

from tools.log_builder import (
    LogBuilder,
    LogColor,
    BOTLOG
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

REPORT_TYPES = [
    ("Harassment", "The author of the message attacked someone repeatedly and personally"),
    ("Profanities/behavior", "The message is toxic/vulgar/doesn't respect the rules"),
    ("Hacking/Cheating", "The message mentions hackers/banned users/cheating, etc."),
    ("Illegal content", "Shows NSFW/gore/drugs/weapons/crypto content"),
    ("Other report", "It's explicit; the admins will judge for themselves")
]

class ReportModal(discord.ui.Modal, title="Report a message to the staff"):
    header = discord.ui.TextDisplay(content=(
        "🚩 This menu allows you to easily report a community message that you find inappropriate, "
        "**directly to the staff**. You are limited in the number of reports you can make per day, "
        "so choose your messages carefully and only report if you feel it's truly necessary (__any abuse will be punished__)."
    ))
    problem = discord.ui.Label(
        text="Reason",
        description="Please select the option that best describes the problem",
        component=discord.ui.Select(
            options = [
                discord.SelectOption(label=label, description=desc)
                for label, desc in REPORT_TYPES
            ],
            placeholder="Choose a reason for reporting...",
            min_values=1, max_values=1
        )
    )
    additional_message = discord.ui.Label(
        text="Optional message to describe or add something",
        component=discord.ui.TextInput(
            style=discord.TextStyle.paragraph,
            max_length=300,
            required=False,
            placeholder="Add a message (be respectful, remember it will be read by the admins)"
        )
    )

    def __init__(self, bot: "RepulsBot", report_author: discord.User, message: discord.Message):
        super().__init__()
        self.bot = bot
        self.report_author: discord.User = report_author
        self.target_message: discord.Message = message

    def get_selected_reason(self, selected: str) -> tuple[str, str]:
        return next(((label, desc) for label, desc in REPORT_TYPES if label == selected), (REPORT_TYPES[-1][0], REPORT_TYPES[-1][1]))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        assert isinstance(self.problem.component, discord.ui.Select)
        assert isinstance(self.additional_message.component, discord.ui.TextInput)
        report_message: str | None = self.additional_message.component.value
        report_reason = self.get_selected_reason(self.problem.component.values[0])

        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.brand_red())
        view.add_item(container)
        container.add_item(discord.ui.Section(
            discord.ui.TextDisplay(content=f"### {DefaultEmojis.CRITICAL} New message reported by {interaction.user.mention}!"),
            accessory=discord.ui.Button(
                label="Go to message",
                style=discord.ButtonStyle.url,
                url=self.target_message.jump_url
            )
        ))
        container.add_item(discord.ui.TextDisplay(content=(
            f"**Selected reason:**\n➜ __{report_reason[0]}__ (*{report_reason[1]}*)\n" +
            (f"**Additional report message**:\n>>> {report_message}" if report_message else '')
        )))
        container.add_item(discord.ui.Separator())
        content = (self.target_message.content if len(self.target_message.content) <= 500 else f"{self.target_message.content[:497]}...").strip() if self.target_message.content else "*This message is empty*"
        container.add_item(discord.ui.TextDisplay(content=(
            "### Info about the problematic message\n"
            f"**Message author**: {self.target_message.author.mention}\n" + 
            ("**Message content**:\n>>> " + content)
        )))
        if self.target_message.attachments:
            container.add_item(discord.ui.TextDisplay(content="**Attachments of the reported message**"))
            gallery = discord.ui.MediaGallery()
            gallery.items = [discord.MediaGalleryItem(media=attachment.url) for attachment in self.target_message.attachments][:10]
            container.add_item(gallery)

        report_channel = interaction.guild.get_channel(IDs.serverChannel.REPORTS)
        await report_channel.send(view=view)
        await self.bot.moderation_storage.add_report_to_user(interaction.user.id)
        await interaction.followup.send(content=f"> {DefaultEmojis.CHECK} Message reported - thank you for helping to make our community safer!", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error):
        await (
            LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
            .title(f"{DefaultEmojis.ERROR} An error occurred when {interaction.user.mention} tried to report a message")
            .description(f"```\n{error}\n```")
            .send()
        )
        await interaction.followup.send(content=(
            f">>> 🛰️ Hmm... Sorry, the reporting function seems to be **temporarily unavailable**.{ASK_HELP}"
        ))
        return await super().on_error(interaction, error)

class AnnouncementModal(discord.ui.Modal, title="Send announcement message(s)"):
    header = discord.ui.TextDisplay(content=(
        "This command allows you to **select one or more of your messages** (that you sent in a private channel "
        "previously) to send them on my behalf (__RepulsBot__) in **one or more channels** to be defined in this modal "
        "(I will send your messages there identically, **including files**, and I will add the pings you define here to the first message)."
    ))
    info = discord.ui.TextDisplay(content="### Messages provided\n")
    channels = discord.ui.Label(
        text="The channel(s) where to send the announcement",
        component=discord.ui.ChannelSelect(
            channel_types=[discord.ChannelType.news, discord.ChannelType.text],
            max_values=25,
            required=True,
            placeholder="Choose one or more channels..."
        )
    )
    roles = discord.ui.Label(
        text="Role(s) to ping (optional and maximum 10)",
        component=discord.ui.RoleSelect(
            max_values=10,
            placeholder="Choose one or more roles..."
        )
    )

    def __init__(self, messages: list[discord.Message], failed_links: list[str]):
        super().__init__()
        self.base_messages: list[discord.Message] = messages
        assert isinstance(self.info, discord.ui.TextDisplay)
        self.info.content += (
            '\n'.join(f"- {msg.jump_url}" for msg in self.base_messages) +
            ("\n### Some messages could not be found\n>>> " + '\n'.join(f"- [{link[-14:]}...]({link})" for link in failed_links) if failed_links else '')
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        assert isinstance(self.channels.component, discord.ui.ChannelSelect)
        assert isinstance(self.roles.component, discord.ui.RoleSelect)
        channels = [interaction.client.get_partial_messageable(channel.id) for channel in self.channels.component.values]
        roles_mentions = [role.mention for role in self.roles.component.values]

        success_sent: list[discord.PartialMessageable] = []
        failed_sends: dict[discord.PartialMessageable, int] = {}
        for channel in channels:
            for idx, message in enumerate(self.base_messages):
                message_to_send: str = ", ".join(roles_mentions) + f"\n{message.content}" if idx == 0 and roles_mentions else message.content
                try:
                    files = [await a.to_file() for a in message.attachments]
                    await channel.send(content=message_to_send, files=(files if files else None))
                except Exception:
                    failed_sends.setdefault(channel, 0)
                    failed_sends[channel] += 1
            if failed_sends.get(channel) is None:
                success_sent.append(channel)

        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.brand_green())
        view.add_item(container)
        container.add_item(discord.ui.TextDisplay(content="## Result of the `announcement` command"))
        container.add_item(discord.ui.Separator())

        if len(failed_sends) == len(channels):
            container.accent_color = discord.Color.brand_red()
            container.add_item(discord.ui.TextDisplay(content=(
                f"> {DefaultEmojis.ERROR} The message could not be sent in any of the specified channels. **Contact the developer for assistance**."
            )))
        else:
            success_list = ", ".join(f"{ch.mention}" for ch in success_sent)
            failed_list = '\n'.join(f"- {ch.mention} ({errors} failed {plurial("message", errors)})" for ch, errors in failed_sends.items())
            if len(success_sent) == len(channels):
                container.add_item(discord.ui.TextDisplay(content=f"{DefaultEmojis.CHECK} Message sent in {len(channels)} channel(s)!\n> {success_list}"))
            else:
                container.add_item(discord.ui.TextDisplay(content=(
                    f"> {DefaultEmojis.WARN} **The message was sent in {len(success_sent)} of the {len(channels)} {plurial("channel", len(channels))} requested**\n"
                    f"### {DefaultEmojis.ONLINE} Message(s) sent successfully\n{success_list}\n### {DefaultEmojis.OFFLINE} Channel(s) with failure\n{failed_list}"
                )))

        await interaction.followup.send(view=view, ephemeral=True)

class AdminCog(commands.Cog, name=CogsNames.ADMIN):
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot

    async def cog_load(self):
        # https://github.com/Rapptz/discord.py/blob/master/examples/app_commands/basic.py#L109
        report_cmd = app_commands.ContextMenu(name="Report to moderators", callback=self.report_message)
        self.bot.tree.add_command(report_cmd)

    @app_commands.guild_only()
    async def report_message(self, interaction: discord.Interaction, message: discord.Message):
        user_reports_number = await self.bot.moderation_storage.get_reports_number(interaction.user.id)
        if user_reports_number is None or user_reports_number > 3:
            await interaction.response.send_message("> Oh! You've reported too many messages today and you've reached the limit 🙄", ephemeral=True)
        else:
            await interaction.response.send_modal(ReportModal(self.bot, interaction.user, message))

    @app_commands.command(description="[ADMIN] Send a message quickly with RepulsBot in the current channel")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    @app_commands.describe(
        content="The message you wish to send (only emojis are available there, no files)",
        reply_to="Link (optional) to the message you want to reply to"
    )
    async def talk(self, interaction: discord.Interaction, content: str, reply_to: str | None = None):
        await interaction.response.defer(ephemeral=True)
        if not reply_to:
            await interaction.channel.send(content)
        else:
            match = re.search(DISCORD_MSG_ID_REGEX, reply_to)
            if not match:
                await interaction.followup.send(content=f"{DefaultEmojis.WARN} Couldn't parse a message id from `reply_to` link", ephemeral=True)
                return
            message_id = int(match.group(1))
            try:
                message_to_reply = await interaction.channel.fetch_message(message_id)
                await message_to_reply.reply(content=content)
            except discord.NotFound:
                await interaction.followup.send(embed=(
                    f"{DefaultEmojis.WARN} There doesn't seem to be any message at this link\n"
                    "### Message preview\n"
                    f">>> {(content if len(content) <= 1930 else content[:1927] + "...")}"
                ), ephemeral=True)
        await interaction.delete_original_response()

    @app_commands.command(description="[ADMIN] Create an announcement with images, mentions, etc. in one or more channels")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    @app_commands.describe(messages="One (or more, in order and separated by commas) link(s) to the messages to be turned into an announcement")
    async def announcement(self, interaction: discord.Interaction, messages: str):
        links = [link.strip() for link in messages.split(',') if link.strip()]
        messages_found_list: list[discord.Message] = []
        messages_not_found_list: list[str] = []
        for link in links:
            match = re.search(DISCORD_MSG_ID_REGEX, link)
            if not match:
                messages_not_found_list.append(link)
                continue
            message_id = int(match.group(1))
            try:
                message = await interaction.channel.fetch_message(message_id)
                messages_found_list.append(message)
            except discord.NotFound:
                messages_not_found_list.append(link)
        if len(links) > 0 and len(links) > len(messages_not_found_list):
            await interaction.response.send_modal(AnnouncementModal(messages_found_list, messages_not_found_list))
        else:
            await interaction.response.send_message(content=f"{DefaultEmojis.WARN} None of the provided links appear to be valid?\n", ephemeral=True)

async def setup(bot: "RepulsBot"):
    await bot.add_cog(AdminCog(bot))