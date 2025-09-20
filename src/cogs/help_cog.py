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
# bot files
from log_system import LogColor
from utils import (
    IS_ADMIN,
    nl
)

from cogs_list import CogsNames
from constants import (
    DefaultEmojis,
    AUTHORISED_ROLES,
    CMD_PREFIX
)

class AdminPanel:
    EMOTE = "🛡️"
    LABEL = "Admin panel"
    DESC = """
    Admins are encouraged to use Discord's native features, such as polls or moderation tools (via native commands or from the interface)
    for bans, kicks, and timeouts. The bot logs all actions taken, and the automod manages content filters and raids.
    """

class HelpToggleView(discord.ui.View):
    def __init__(self, help_cog: HelpCog, is_admin: bool = False):
        super().__init__()
        self.help_cog = help_cog
        self.is_showing_admin = False

        if is_admin:
            self.add_item(self.ToggleButton())

    class ToggleButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=AdminPanel.LABEL, emoji=AdminPanel.EMOTE, style=discord.ButtonStyle.danger)

        async def callback(self, interaction: discord.Interaction):
            view: HelpToggleView = self.view
            view.is_showing_admin = not view.is_showing_admin

            embed = await view.help_cog.get_help_embed(view.is_showing_admin)
            if view.is_showing_admin:
                self.label = "Return to member help"
                self.emoji = "⬅️"
            else:
                self.label = AdminPanel.LABEL
                self.emoji = AdminPanel.EMOTE

            await interaction.response.edit_message(embed=embed, view=view)

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
            if command.extras.get(IS_ADMIN, False) == admin:
                embed.add_field(
                    name=self.format_command_name(command),
                    value=command.description or "No description",
                    inline=False
                )
        # ---------------------------------- ctx commands
        for cmd in self.bot.walk_commands():
            if cmd.extras.get(IS_ADMIN, False) == admin:
                embed.add_field(
                    name=self.format_command_name(cmd),
                    value=cmd.help or cmd.description or "No description",
                    inline=False
                )
        
        return embed
    
    async def get_command_help_embed(self, command_name: str) -> discord.Embed | None:
        slash_cmd = self.bot.tree.get_command(command_name)
        if slash_cmd:
            embed = discord.Embed(
                title=f"📖 Help about `/{slash_cmd.name}`",
                description=f"*{slash_cmd.description or "This command has no description!"}*",
                color=discord.Color.dark_blue(),
            )
            return embed
        
        ctx_cmd = self.bot.get_command(command_name)
        if ctx_cmd:
            embed = discord.Embed(
                title=f"📖 Help about the `{CMD_PREFIX}{ctx_cmd.qualified_name}` command",
                description=ctx_cmd.description,
                color=discord.Color.dark_blue(),
            )
            return embed
        return None

    @app_commands.command(description="Show what I am capable of")
    @app_commands.describe(command="Name of a specific command to get help for")
    async def help(self, interaction: discord.Interaction, command: str = None):
        user_role_ids = {role.id for role in interaction.user.roles}
        is_admin = bool(user_role_ids & AUTHORISED_ROLES)

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
        view = HelpToggleView(self, is_admin)
        await interaction.response.send_message(embed=help_embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))