"""
This cog contains all the commands accessible only to server admins

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

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

class AdminTalkModal(discord.ui.Modal, title="Admin talk function"):
    message = discord.ui.Label(
        text="The message you want to send",
        component=discord.ui.TextInput(
            style=discord.TextStyle.long,
            placeholder="Write your message here...",
            required=True,
            max_length=1000
        )
    )
    channels = discord.ui.Label(
        text="The channel(s) where to send the message",
        description="Select one or more channels from the list",
        component=discord.ui.ChannelSelect(
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=25,
            required=True,
            placeholder="Choose one or more channels..."
        )
    )

    def __init__(self, interaction: discord.Interaction, initial_message: str):
        super().__init__()
        self.guild = interaction.guild
        assert isinstance(self.message.component, discord.ui.TextInput)
        self.message.component.default = initial_message
        assert isinstance(self.channels.component, discord.ui.ChannelSelect)
        self.channels.component.default_values = [interaction.channel]

    async def on_submit(self, interaction: discord.Interaction):
        # https://github.com/Rapptz/discord.py/blob/master/examples/modals/label.py#L66
        assert isinstance(self.message.component, discord.ui.TextInput)
        assert isinstance(self.channels.component, discord.ui.ChannelSelect)

        message = self.message.component.value
        channels = [
            interaction.client.get_partial_messageable(channel.id)
            for channel in self.channels.component.values
        ]
        failed_sends: list[discord.TextChannel] = []
        success_sent: list[discord.Message] = []
        for channel in channels:
            try:
                msg = await channel.send(message)
                success_sent.append(msg)
            except Exception:
                failed_sends.append(channel)
        
        embed = discord.Embed(
            title="Result of the talk command"
        )
        embed.add_field(name="Message preview", value=f">>> {(message if len(message) <= 800 else message[:797] + "...")}")
        success_list = ", ".join(f"{msg.jump_url}" for msg in success_sent)
        failed_list = '\n'.join(f"- {ch.mention}" for ch in failed_sends)
        if not failed_sends:
            embed.color = discord.Color.brand_green()
            embed.description = f"{DefaultEmojis.CHECK} Message sent in {len(channels)} channel(s)!\n({success_list})"
        else:
            embed.color = discord.Color.brand_red()
            if not success_sent:
                embed.description = f"{DefaultEmojis.ERROR} The message could not be sent in any of the specified channels. Contact the developer for assistance."
            else:
                embed.description = f"{DefaultEmojis.WARN} **The message was sent in {len(success_sent)} of the {len(channels)} {plurial("channel", len(channels))} requested**\n"
                embed.description += f"### {DefaultEmojis.ONLINE} Message(s) sent successfully\n{success_list}\n### {DefaultEmojis.OFFLINE} Channel(s) with failure\n{failed_list}"

        await interaction.response.send_message(embed=embed, ephemeral=True)

class AdminCog(commands.Cog, name=CogsNames.ADMIN):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="talk", description="[ADMIN] Send a message under RepulsBot's name in the chosen channels")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def talk(self, interaction: discord.Interaction, message: str, multiple_channels: bool = False):
        if multiple_channels is False:
            await interaction.response.defer()
            await interaction.channel.send(message)
            await interaction.delete_original_response()
        else:
            await interaction.response.send_modal(AdminTalkModal(interaction, message))

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
