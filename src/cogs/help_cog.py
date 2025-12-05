"""
Cog containing only the help command and its generation.

## Help command details
The help command differentiates between commands that are usable by all members and those that are only usable by admins. It does this by relying on the `extras` parameter of the `discord.py` decorators.
- Contextual commands ([discord.ext.commands.command](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.command))
- Slash commands ([discord.app_commands.command](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.command))

The problem with this method is that it does not allow you to mention slash commands since you do not get their ID.

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

# https://docs.python.org/3/library/__future__.html
# to remplace the "type hint as string"
from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands
import platform
# bot files
from log_system import LogColor
from utils import (
    is_admin,
    nl,
    ADMIN_CMD
)

from cogs_list import CogsNames
from constants import (
    Links,
    BotInfo,
    DefaultEmojis,
    IDs,
    CMD_PREFIX
)

class AdminPanel:
    EMOTE = "🛡️"
    LABEL = "Admin panel"
    DESC = f"""
    Admins are encouraged to use Discord's native features, such as polls or moderation tools from within the interface for bans, kicks, and timeouts.

    For mutes longer than a week, use the <@&{IDs.serverRoles.MUTED}> role).
    *The bot logs all actions taken, and the automod manages content filters and raids.*
    """

class HelpMenuView(discord.ui.View):
    def __init__(self, bot: commands.Bot, help_cog: HelpCog, is_admin: bool = False):
        super().__init__()
        self.help_cog = help_cog
        self.is_showing_admin = False
        self.bot = bot

        self.add_item(self.BotInfoButton(self.bot))
        if is_admin:
            self.add_item(self.ToggleButton())

    class ToggleButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=AdminPanel.LABEL, emoji=AdminPanel.EMOTE, style=discord.ButtonStyle.danger)

        async def callback(self, interaction: discord.Interaction):
            view: HelpMenuView = self.view
            view.is_showing_admin = not view.is_showing_admin

            embed = await view.help_cog.get_help_embed(view.is_showing_admin)
            if view.is_showing_admin:
                self.label = "Return to member help"
                self.emoji = "⬅️"
            else:
                self.label = AdminPanel.LABEL
                self.emoji = AdminPanel.EMOTE

            await interaction.response.edit_message(embed=embed, view=view)

    class BotInfoButton(discord.ui.Button):
        def __init__(self, bot: commands.Bot):
            super().__init__(label="About the bot", emoji='🔧', style=discord.ButtonStyle.secondary)
            self.bot = bot

        async def callback(self, interaction: discord.Interaction):
            self.embed = discord.Embed(color=discord.Color.dark_blue())
            self.embed.description = nl(BotInfo.DESCRIPTION.format(
                name=self.bot.user.mention,
                server=Links.MAIN_SERVER,
                game=Links.GAME
            ))
            self.embed.add_field(name=f"{self.bot.user.display_name}", value=f"v{BotInfo.VERSION}")
            self.embed.add_field(name="discord.py", value=f"v{discord.__version__}")
            self.embed.add_field(name="python", value=f"v{platform.python_version()}")
            self.embed.add_field(name="Source code", value=f"See on [GitHub]({BotInfo.GITHUB})")
            self.embed.add_field(name="Report an issue", value=f"Contact the developer <@{self.bot.owner_id}> or create a [GitHub issue]({BotInfo.GITHUB}/issues)")

            await interaction.response.send_message(embed=self.embed, ephemeral=True)

# https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.app_commands.CommandTree.walk_commands
# ---------------------------------- help cog (see README.md)
class HelpCog(commands.Cog, name=CogsNames.HELP):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def format_command_name(cmd: app_commands.Command | commands.Command) -> str:
        return f"`{"/" if isinstance(cmd, app_commands.Command) else CMD_PREFIX}{cmd.name}`"

    async def get_help_embed(self, admin: bool = False) -> discord.Embed:
        title = "🔒 Admin commands" if admin else "📌 Member commands"
        desc = f"**You can access this because you are an admin.** {nl(AdminPanel.DESC)}" if admin else "Commands you can use"
        color = discord.Color.red() if admin else discord.Color.dark_blue()
        embed = discord.Embed(title=title, description=desc, color=color)
        # ---------------------------------- slash commands
        for command in self.bot.tree.get_commands():
            if command.extras.get(ADMIN_CMD, False) == admin:
                embed.add_field(
                    name=self.format_command_name(command),
                    value=command.description or "No description",
                    inline=False
                )
        # ---------------------------------- ctx commands
        for cmd in self.bot.walk_commands():
            if cmd.extras.get(ADMIN_CMD, False) == admin:
                embed.add_field(
                    name=self.format_command_name(cmd),
                    value=cmd.help or cmd.description or "No description",
                    inline=False
                )
        
        return embed
    
    async def get_command_help_embed(self, command_name: str) -> discord.Embed | None:
        command = self.bot.tree.get_command(command_name) or self.bot.get_command(command_name)
        if command:
            embed = discord.Embed(
                title=f"📖 Help about the {self.format_command_name(command)} command",
                description=f"*{command.description or "This command has no description!"}*",
                color=discord.Color.dark_blue(),
            )
            if command.extras.get(ADMIN_CMD, False):
                embed.color = discord.Color.brand_red()
                embed.add_field(
                    name="🛡️ Please note, this command can only be used by administrators!",
                    inline=False
                )
            return embed
        return None

    @app_commands.command(description="Show what I am capable of")
    @app_commands.describe(command="Name of a specific command to get help for")
    async def help(self, interaction: discord.Interaction, command: str = None):
        if command:
            cmd_embed = await self.get_command_help_embed(command)
            if not cmd_embed:
                error_embed = discord.Embed(
                    title=f"{DefaultEmojis.ERROR} Command not found!",
                    description=f"No command named `{command}` found.",
                    color=LogColor.RED
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return
            
            await interaction.response.send_message(embed=cmd_embed, ephemeral=True)
            return

        help_embed = await self.get_help_embed()
        view = HelpMenuView(self.bot, self, is_admin(interaction.user))
        await interaction.response.send_message(embed=help_embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))