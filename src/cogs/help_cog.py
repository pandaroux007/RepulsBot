"""
Cog containing only the help command and its generation.

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
from cmd_list import CmdList, ADMIN_SLASH_COMMANDS, ADMIN_CTX_COMMANDS
from cogs_list import CogsNames
from constants import (
    DefaultEmojis,
    AUTHORISED_ROLES,
    CMD_PREFIX    
)

ADMIN_EMOTE = "🛡️"
ADMIN_LABEL = "Admin panel"

class HelpToggleView(discord.ui.View):
    def __init__(self, help_cog: HelpCog, is_admin: bool = False):
        super().__init__()
        self.help_cog = help_cog
        self.is_showing_admin = False

        if is_admin:
            self.add_item(self.ToggleButton())

    class ToggleButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=ADMIN_LABEL, emoji=ADMIN_EMOTE, style=discord.ButtonStyle.danger)

        async def callback(self, interaction: discord.Interaction):
            view: HelpToggleView = self.view
            view.is_showing_admin = not view.is_showing_admin

            if view.is_showing_admin:
                embed = await view.help_cog.get_admin_help_embed()
                self.label = "Return to member help"
                self.emoji = "⬅️"
            else:
                embed = await view.help_cog.get_member_help_embed()
                self.label = ADMIN_LABEL
                self.emoji = ADMIN_EMOTE

            await interaction.response.edit_message(embed=embed, view=view)

# https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.app_commands.CommandTree.walk_commands
# ---------------------------------- help cog (see README.md)
class HelpCog(commands.Cog, name=CogsNames.HELP):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_member_help_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📌 Member commands (slash)",
            description="All functions you can access through the discord menu",
            color=discord.Color.dark_blue()
        )

        for command in await self.bot.tree.fetch_commands():
            if command.name not in ADMIN_SLASH_COMMANDS:
                embed.add_field(name=command.mention, value=command.description, inline=False)
        return embed

    async def get_admin_help_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔒 Admin commands (unreferenced)",
            description="Commands that can only be used with perms or roles",
            color=discord.Color.red()
        )

        # ctx commands admin
        for cmd in self.bot.walk_commands():
            if cmd.name in ADMIN_CTX_COMMANDS:
                embed.add_field(
                    name=f"`{CMD_PREFIX}{cmd.name}`",
                    value=cmd.description,
                    inline=False
                )
        # slash commands admin
        for command in await self.bot.tree.fetch_commands():
            if command.name in ADMIN_SLASH_COMMANDS:
                embed.add_field(name=command.mention, value=command.description, inline=False)
        return embed
    
    async def get_command_help_embed(self, command_name: str) -> discord.Embed | None:
        for slash_cmd in await self.bot.tree.fetch_commands():
            if slash_cmd.name == command_name:
                embed = discord.Embed(
                    description=f"**📖 Help about the {slash_cmd.mention} command**\n{slash_cmd.description or "This command has no description!"}",
                    color=discord.Color.dark_blue(),
                )

                if slash_cmd.options:
                    opts_str = "\n".join([f"`{opt.name}`: {opt.description}" for opt in slash_cmd.options])
                    embed.add_field(name="Options", value=opts_str, inline=False)
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

    @app_commands.command(name=CmdList.HELP, description="Show what I am capable of")
    @app_commands.describe(command="Name of a specific command to get help for")
    async def help(self, interaction: discord.Interaction, command: str = None):
        # https://www.w3schools.com/python/ref_set_intersection.asp
        user_role_ids = {role.id for role in interaction.user.roles}
        is_admin = bool(user_role_ids & AUTHORISED_ROLES)

        if command:
            embed = await self.get_command_help_embed(command)
            if not embed:
                await interaction.response.send_message(f"{DefaultEmojis.ERROR} No command named `{command}` found.", ephemeral=True)
                return
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        embed = await self.get_member_help_embed()
        view = HelpToggleView(self, is_admin)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))