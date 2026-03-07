"""
This cog contains all the commands accessible only to server admins

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
# bot files
from data.cogs import CogsNames
from tools.utils import plurial
from data.constants import (
    DefaultEmojis,
    ADMIN_CMD
)

class AddFileToAnnouncement(discord.ui.Modal, title="Add file(s) to the announcement"):
    header = discord.ui.TextDisplay(content=(
        "If you don't want to send any files, simply send the modal without providing anything. **All fields below are optional!**"
    ))
    files = discord.ui.Label(
        text="Send files from your computer",
        component=discord.ui.FileUpload(
            max_values=10,
            required=False
        )
    )
    links = discord.ui.Label(
        text="Or links to discord/web image(s)",
        component=discord.ui.TextInput(
            style=discord.TextStyle.long,
            placeholder="Copy the links to your images here (separated by commas)",
            required=False,
            max_length=500
        )
    )

    def __init__(self, parent: MakeAnnouncementModal):
        super().__init__()
        self.parent = parent

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(self.files.component, discord.ui.FileUpload)
        assert isinstance(self.links.component, discord.ui.TextInput)
        assert isinstance(self.parent.channels.component, discord.ui.ChannelSelect)

        links_str = self.links.component.value if self.links.component.value else ""
        links = [link.strip() for link in links_str.split(',') if link.strip()]
        if links:
            self.parent.content += "\n" + "\n".join(links)

        await self.parent.parent._send_and_confirm(
            interaction,
            message=self.parent.content,
            channels=self.parent.channels.component.values,
            attachments=self.files.component.values
        )

class AddAttachmentsInterface(discord.ui.LayoutView):
    buttons_row = discord.ui.ActionRow()

    def __init__(self, parent: MakeAnnouncementModal):
        super().__init__()
        self.parent = parent
        self.container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        self.add_item(self.container)
        self.remove_item(self.buttons_row)
        self.container.clear_items()
        self.container.add_item(discord.ui.TextDisplay(content=(
            "### ⚙️ Click here to add files or send now\n"
        )))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(self.buttons_row)

    @buttons_row.button(label="Send as is now", emoji='📤', style=discord.ButtonStyle.primary)
    async def send_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert isinstance(self.parent.channels.component, discord.ui.ChannelSelect)
        await self.parent.parent._send_and_confirm(interaction, self.parent.content, self.parent.channels.component.values, [])
        await interaction.delete_original_response()

    @buttons_row.button(label="Add attachments", emoji='🔗', style=discord.ButtonStyle.secondary)
    async def add_attachments(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddFileToAnnouncement(parent=self.parent))
        await interaction.delete_original_response()

class MakeAnnouncementModal(discord.ui.Modal, title="Send an announcement message"):
    header = discord.ui.TextDisplay(content=(
        "Once your announcement is sent, **you will no longer be able to edit it**. You can still delete messages and resend them. "
        "See [the Markdown available on Discord](https://support.discord.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline)."
    ))
    message = discord.ui.Label(
        text="The announcement message you wish to send",
        component=discord.ui.TextInput(
            style=discord.TextStyle.long,
            placeholder="Here you can use Markdown tags, links, headings, etc...",
            required=True,
            max_length=1700
        )
    )
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

    def __init__(self, parent: AdminCog, initial_message: str, initial_channel: discord.TextChannel):
        super().__init__()
        self.parent = parent
        self.content: str = None
        if initial_message:
            assert isinstance(self.message.component, discord.ui.TextInput)
            self.message.component.default = initial_message
        assert isinstance(self.channels.component, discord.ui.ChannelSelect)
        self.channels.component.default_values = [initial_channel]

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        assert isinstance(self.message.component, discord.ui.TextInput)
        assert isinstance(self.channels.component, discord.ui.ChannelSelect)
        assert isinstance(self.roles.component, discord.ui.RoleSelect)

        self.content = self.message.component.value
        roles_mentions = [role.mention for role in self.roles.component.values]
        if roles_mentions:
            self.content = ", ".join(roles_mentions) + f"\n{self.content}"

        await interaction.followup.send(view=AddAttachmentsInterface(parent=self), ephemeral=True)

class AdminCog(commands.Cog, name=CogsNames.ADMIN):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_and_confirm(self, interaction: discord.Interaction, message: str, channels: list[app_commands.AppCommandChannel], attachments: list[discord.Attachment]) -> None:
        await interaction.response.defer()
        failed_sends: list[app_commands.AppCommandChannel] = []
        success_sent: list[discord.Message] = []

        _channels = [interaction.client.get_partial_messageable(channel.id) for channel in channels]
        for channel in _channels:
            try:
                files = [await a.to_file() for a in attachments]
                msg = await channel.send(message, files=(files if files else None))
                success_sent.append(msg)
            except Exception:
                failed_sends.append(channel)

        success_list = ", ".join(f"{msg.jump_url}" for msg in success_sent)
        failed_list = '\n'.join(f"- {ch.mention}" for ch in failed_sends)

        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.brand_green())
        view.add_item(container)

        container.add_item(discord.ui.TextDisplay(content="## Result of the talk command"))
        if len(failed_sends) == len(channels):
            container.accent_color = discord.Color.brand_red()
            container.add_item(discord.ui.TextDisplay(content=(
                f"> {DefaultEmojis.ERROR} The message could not be sent in any of the specified channels. **Contact the developer for assistance**."
            )))
        else:
            if len(success_sent) == len(channels):
                container.add_item(discord.ui.TextDisplay(content=f"> {DefaultEmojis.CHECK} Message sent in {len(channels)} channel(s)!\n({success_list})"))
            else:
                container.add_item(discord.ui.TextDisplay(content=(
                    f"> {DefaultEmojis.WARN} **The message was sent in {len(success_sent)} of the {len(channels)} {plurial("channel", len(channels))} requested**\n"
                    f"### {DefaultEmojis.ONLINE} Message(s) sent successfully\n{success_list}\n### {DefaultEmojis.OFFLINE} Channel(s) with failure\n{failed_list}"
                )))
            container.add_item(discord.ui.TextDisplay(content=(
                "### Message preview\n"
                f">>> {(message if len(message) <= 800 else message[:797] + "...")}"
            )))
            if attachments:
                container.add_item(discord.ui.Separator())
                container.add_item(discord.ui.TextDisplay(content="### The command was used with attachments"))
                gallery = discord.ui.MediaGallery()
                gallery.items = [discord.MediaGalleryItem(media=attachment.url) for attachment in attachments]
                container.add_item(gallery)

        container.add_item(discord.ui.TextDisplay(f"-# Used by {interaction.user.mention} ・ {discord.utils.format_dt(interaction.created_at, 'F')}"))
        await interaction.followup.send(view=view, ephemeral=True)

    @app_commands.command(description="[ADMIN] Send a message under RepulsBot's name in the chosen channels")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    @app_commands.describe(
        message="The message you wish to send (useful for inserting emojis without copy-pasting)",
        is_announcement="Switch to True to ping roles, send images, or send to multiple channels"
    )
    async def talk(self, interaction: discord.Interaction, message: str | None, is_announcement: bool = False):
        if not message or is_announcement is True:
            await interaction.response.send_modal(MakeAnnouncementModal(self, message, interaction.channel))
        else:
            await interaction.response.defer(ephemeral=True)
            await interaction.channel.send(message)
            await interaction.delete_original_response()

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))