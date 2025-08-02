"""
Cog containing only the help command and its generation.

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
# bot files
from cogs_list import CogsNames
from constants import (
    IDs,
    CMD_PREFIX
)

AUTHORISED_ROLES = {
    IDs.serverRoles.ADMIN,
    IDs.serverRoles.DEVELOPER,
    IDs.serverRoles.CONTRIBUTOR
}

class HelpToggleView(discord.ui.View):
    def __init__(self, help_cog: commands.Cog, is_admin: bool):
        super().__init__(timeout=None)
        self.help_cog = help_cog
        self.is_showing_admin = False

        if is_admin:
            self.add_item(self.ToggleButton())

    class ToggleButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Admin panel", emoji="🛡️", style=discord.ButtonStyle.danger)

        async def callback(self, interaction: discord.Interaction):
            view: HelpToggleView = self.view
            view.is_showing_admin = not view.is_showing_admin

            if view.is_showing_admin:
                embed = view.help_cog.get_admin_help_embed()
                self.label = "Return to member help"
                self.emoji = "⬅️"
            else:
                embed = await view.help_cog.get_member_help_embed()
                self.label = "Admin panel"
                self.emoji = "🛡️"

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
            embed.add_field(name=command.mention, value=command.description, inline=False)
        return embed

    def get_admin_help_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔒 Admin commands (unreferenced)",
            description="Commands that can only be used with perms or roles",
            color=discord.Color.red()
        )

        for cmd in self.bot.walk_commands():
            if not isinstance(cmd, commands.HybridCommand):
                embed.add_field(
                    name=f"`{CMD_PREFIX}{cmd.name}`",
                    value=cmd.description,
                    inline=False
                )
        return embed

    @app_commands.command(name="help", description="Show what I am capable of")
    async def help(self, interaction: discord.Interaction):
        embed = await self.get_member_help_embed()
        # https://www.w3schools.com/python/ref_set_intersection.asp
        user_role_ids = {role.id for role in interaction.user.roles}
        is_admin = bool(user_role_ids & AUTHORISED_ROLES)
        view = HelpToggleView(self, is_admin)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))