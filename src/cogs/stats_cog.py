"""
This cog contain statistical commands

:copyright: (c) 2026-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
import datetime
# bot files
from data.cogs import CogsNames
from tools.utils import GamePlaylist
from tools.stats_parser import (
    fetch_server_stats,
    fetch_game_version,
    fetch_player,
    PlayerProfile
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

class PlayerInfoView(discord.ui.LayoutView):
    menu_row = discord.ui.ActionRow()

    def __init__(self, requested_name: str, player: PlayerProfile | None):
        super().__init__()
        self.container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        self.add_item(self.container)

        self.requested_name: str = requested_name
        self.player: PlayerProfile | None = player
        self.player_stats_mode: bool = True
        self.attachment = discord.File(self.player.color_theme[0], self.player.color_theme[1]) if self.player and self.player.color_theme else None

    async def generate_interface(self):
        self.remove_item(self.menu_row)
        self.container.clear_items()
        if not self.player:
            self.container.add_item(discord.ui.TextDisplay(content=(
                f"## 🛸 Oh! Unable to retrieve `{self.requested_name}` stats\n"
                "➜ *Verify that this account exists and that the name is correct.*"
            )))
            return self

        stats = discord.ui.TextDisplay(content=(
            f"## `{f"[{self.player.clan}] " if self.player.clan else ''}{self.player.name}` (level {self.player.level})\n"
            f"🏅 {self.player.xp_progress()}\n"
            f"💀 **{self.player.kills}** kills | **{self.player.deaths}** deaths | **{self.player.kd_ratio or '-'} K/D**\n"
            f"⚔️ In **{self.player.matches}** matches, **{self.player.wins}** wins (*{self.player.win_ratio} win rate*)\n" +
            (f"> 🛡️ **`{self.player.name}` is an in-game administrator!**\n" if self.player.is_admin else '') +
            f"-# Account created on {discord.utils.format_dt(self.player.created)}"
        ))
        if self.player.color_theme:
            self.container.add_item(discord.ui.Section(stats, accessory=discord.ui.Thumbnail(
                    media=f"attachment://{self.player.color_theme[1]}",
                    description=f"Primary: {self.player.primary_color} | Secondary: {self.player.secondary_color}"
                )
            ))
        else:
            self.container.add_item(stats)

        advanced_stats = (
            (f"{self.player.vehicle_kills} Vehicle Kills\n" if self.player.vehicle_kills else '') +
            (f"{self.player.headshot} Headshots\n" if self.player.headshot else '') +
            (f"{self.player.flags} Flags\n" if self.player.flags else '') +
            (f"{self.player.assist} Assists\n" if self.player.assist else '') +
            (f"{self.player.skulls} Skulls (halloween event)\n" if self.player.skulls else '')
        )
        achievements = (
            (f"{self.player.winstreak} Winstreak\n" if self.player.winstreak else '') +
            (f"{self.player.double_kill} Double Kill\n" if self.player.double_kill else '') +
            (f"{self.player.triple_kill} Triple Kill\n" if self.player.triple_kill else '') +
            (f"{self.player.quad_kill} Quad Kill\n" if self.player.quad_kill else '') +
            (f"{self.player.mega_kill} Mega Kill\n" if self.player.mega_kill else '') +
            (f"{self.player.ultra_kill} Ultra Kill\n" if self.player.ultra_kill else '') +
            (f"{self.player.monster_kill} Monster Kill" if self.player.monster_kill else '') +
            (f"{self.player.killing_spree} Killing Spree\n" if self.player.killing_spree else '') +
            (f"{self.player.dominating} Dominating\n" if self.player.dominating else '') +
            (f"{self.player.unstoppable} Unstoppable\n" if self.player.unstoppable else '') +
            (f"{self.player.godlike} Godlike\n" if self.player.godlike else '')
        )
        if self.player_stats_mode is True:
            if advanced_stats or achievements:
                self.container.add_item(discord.ui.TextDisplay(content=(
                    (f"## Advanced stats\n{advanced_stats}" if advanced_stats else '') +
                    (f"## Achievements\n{achievements}" if achievements else '')
                )))
        else:
            if self.player.best_weapons or self.player.avatar_mods:
                self.container.add_item(discord.ui.TextDisplay(content=(
                    (f"## Top 5 weapons\n{self.player.best_weapons}\n" if self.player.best_weapons else '') +
                    (f"## Current avatar mods\n{self.player.avatar_mods}" if self.player.avatar_mods else '')
                )))
        if self.player.best_weapons or self.player.avatar_mods:
            self.container.add_item(discord.ui.Separator())
            self.container.add_item(self.menu_row)

        return self

    @menu_row.button(emoji='⚔️', label="View specific statistics", style=discord.ButtonStyle.secondary)
    async def toggle_view_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_stats_mode = not self.player_stats_mode
        if self.player_stats_mode is True:
            self.toggle_view_button.label = "View specific statistics"
            self.toggle_view_button.emoji = '⚔️'
        else:
            self.toggle_view_button.label = "View player statistics"
            self.toggle_view_button.emoji = '👤'
        await self.generate_interface()
        await interaction.response.edit_message(view=self)

class StatsCog(commands.Cog, name=CogsNames.STATS):
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot

    @app_commands.command(description="Displays the current CCU of repuls (global and by region)")
    async def game_ccu(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        game_version = await fetch_game_version(self.bot.playfab_manager)

        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        view = discord.ui.LayoutView()
        view.add_item(container)
        container.add_item(discord.ui.TextDisplay(content="### 📊 Current CCU of repuls.io"))
        if game_version:
            container.add_item(discord.ui.TextDisplay(content=f"*Current game version: **`{game_version}`***"))

        result = await fetch_server_stats()
        if not result:
            container.add_item(discord.ui.TextDisplay(content="*Oh! We're sorry, but something went wrong... Unable to retrieve CCU.*"))
            await interaction.followup.send(view=view, ephemeral=True)
            return

        updated_at, regions, global_stats = result

        lines: list[str] = []
        for region in regions:
            lines.append(f"(*{region.status}*) **`{region.name}`** - {region.total} players")
            for pl in GamePlaylist:
                count = region.get(pl)
                if pl is GamePlaylist.CUSTOMS and count == 0:
                    continue
                lines.append(f"- {pl.label}: {count}")
            lines.append('')

        stats_text = '\n'.join(lines).strip()

        container.add_item(
            discord.ui.TextDisplay(
                content=f"Total knights around the world: **{global_stats.total}**"
            )
        )
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(content=stats_text))
        if updated_at:
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(content=f"-# Data updated on {discord.utils.format_dt(datetime.datetime.fromisoformat(updated_at))}"))

        await interaction.followup.send(view=view, ephemeral=True)

    @app_commands.command(description="Retrieves the precise in-game statistics of a given player")
    @app_commands.describe(name="The display name or username of the player to search for")
    async def player_info(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)

        player = await fetch_player(self.bot.playfab_manager, name)
        view = PlayerInfoView(name, player)
        await view.generate_interface()
        if view.attachment:
            await interaction.followup.send(view=view, file=view.attachment, ephemeral=True)
        else:
            await interaction.followup.send(view=view, ephemeral=True)

async def setup(bot: "RepulsBot"):
    await bot.add_cog(StatsCog(bot))