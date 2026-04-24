"""
This cog contain statistical commands

:copyright: (c) 2026-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from enum import Enum
# bot files
from data.cogs import CogsNames
from data.constants import (
    DefaultEmojis,
    GameUrl,
    IDs,
    FOOTER_EMBED
)

from tools.api_client import PublicAPI
from tools.typing import (
    GamePlaylist,
    GameRegion
)

from tools.stats_parser import (
    fetch_build_date,
    fetch_server_stats,
    fetch_game_version,
    fetch_player,
    PlayerProfile
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

# ---------------------------------- player info
class PlayerInfoState(Enum):
    STATS = 1
    LOADOUT = 2
    MODINFO = 3

class PlayerInfoView(discord.ui.LayoutView):
    menu_row = discord.ui.ActionRow()

    def __init__(self, requested_name: str, player: PlayerProfile | None, author: discord.User | discord.Member):
        super().__init__()
        self.container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        self.add_item(self.container)
        self.current_view: PlayerInfoState = PlayerInfoState.STATS

        self.request_author = author
        self.requested_name = requested_name
        self.player = player
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
        if self.player.is_admin or self.player.mod_history:
            self.container.add_item(discord.ui.Separator())
            self.container.add_item(discord.ui.TextDisplay(content=(
                (f"> 🛡️ **`{self.player.name}` is an in-game administrator!**\n" if self.player.is_admin else '') +
                ("> 🚩 This player has already been flagged by moderation" if self.player.mod_history else '')
            )))

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
        if self.current_view == PlayerInfoState.STATS:
            self.stats_view_button.disabled = True
            if advanced_stats or achievements:
                self.container.add_item(discord.ui.TextDisplay(content=(
                    (f"## Advanced stats\n{advanced_stats}" if advanced_stats else '') +
                    (f"## Achievements\n{achievements}" if achievements else '')
                )))
        elif self.current_view == PlayerInfoState.LOADOUT:
            self.loadout_view_button.disabled = True
            if self.player.best_weapons or self.player.avatar_mods:
                self.container.add_item(discord.ui.TextDisplay(content=(
                    (f"## Top 5 weapons\n{self.player.best_weapons}\n" if self.player.best_weapons else '') +
                    (f"## Current avatar mods\n{self.player.avatar_mods}" if self.player.avatar_mods else '')
                )))
        elif self.current_view == PlayerInfoState.MODINFO:
            self.mod_view_button.disabled = True
            if self.player.mod_history:
                self.container.add_item(discord.ui.TextDisplay(content=(
                    f"## History of moderation actions ({len(self.player.mod_history)})\n" +
                    ('\n'.join([f"➜ {f" **{entry.title}**" if entry.title else ''} (By __{entry.moderator}__ at {discord.utils.format_dt(entry.created_at)})\n> *{entry.content}*\n" for entry in self.player.mod_history])).strip()
                )))

        self.menu_row.clear_items()
        if advanced_stats or achievements:
            self.menu_row.add_item(self.stats_view_button)
        if self.player.best_weapons or self.player.avatar_mods:
            self.menu_row.add_item(self.loadout_view_button)
        if self.request_author.guild_permissions.administrator and self.player.mod_history:
            self.menu_row.add_item(self.mod_view_button)

        if len(self.menu_row.children) >= 1:
            self.container.add_item(discord.ui.Separator())
            self.container.add_item(self.menu_row)

        return self

    @menu_row.button(emoji='👤', label="View statistics")
    async def stats_view_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_view = PlayerInfoState.STATS
        self.loadout_view_button.disabled = False
        self.mod_view_button.disabled = False
        await self.generate_interface()
        await interaction.response.edit_message(view=self)

    @menu_row.button(emoji='⚔️', label="View loadout")
    async def loadout_view_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_view = PlayerInfoState.LOADOUT
        self.stats_view_button.disabled = False
        self.mod_view_button.disabled = False
        await self.generate_interface()
        await interaction.response.edit_message(view=self)

    @menu_row.button(label="Moderation history", emoji='🛡️', style=discord.ButtonStyle.danger)
    async def mod_view_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.request_author.guild_permissions.administrator or interaction.user.id != self.request_author.id:
            await interaction.response.send_message(f"> {DefaultEmojis.WARN} You don't have permission to view this.", ephemeral=True)
            return

        self.current_view = PlayerInfoState.MODINFO
        self.stats_view_button.disabled = False
        self.loadout_view_button.disabled = False
        await self.generate_interface()
        await interaction.response.edit_message(view=self)

# ---------------------------------- game status
class GameStatusView(discord.ui.LayoutView):
    select_region_row = discord.ui.ActionRow()

    def __init__(
            self, bot: commands.Bot, game_version: str | None,
            latest_game_update: datetime | None, latest_beta_update: datetime | None,
            server_stats: tuple[datetime, list[GameRegion], GameRegion] | None
        ):
        super().__init__()
        self.container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        self.add_item(self.container)

        self.bot = bot
        self.game_version = game_version
        self.latest_game_update = latest_game_update
        self.latest_beta_update = latest_beta_update

        self.is_ccu_fetched = bool(server_stats is not None)
        if self.is_ccu_fetched:
            _updated_at, _regions, _global_stats = server_stats
            self.updated_at: datetime = _updated_at
            self.regions: dict[str, GameRegion] = {region.name: region for region in _regions}
            self.selected_region: GameRegion = _global_stats # on global ccu by default
            self.global_stats: GameRegion = _global_stats

    async def generate_interface(self):
        self.remove_item(self.select_region_row)
        self.container.clear_items()

        status_lines = []
        if self.is_ccu_fetched:
            for region in self.regions.values():
                status = await region.status
                status_lines.append(f"- `{region.name}`: {status}")

        self.container.add_item(discord.ui.TextDisplay(content="To stay up to date with the latest news, check the following links"))
        announcements_channel = self.bot.get_channel(IDs.serverChannel.ANNOUNCEMENTS)
        self.container.add_item(discord.ui.ActionRow(
            discord.ui.Button(url=announcements_channel.jump_url, style=discord.ButtonStyle.link, label="📢 ANNOUNCEMENTS"),
            discord.ui.Button(url=GameUrl.UPDATES, style=discord.ButtonStyle.link, label="UPDATES")
        ))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.TextDisplay(content=(
            "### ⚙️ Latest game update" +
            (f"\nCurrent main game version: **{self.game_version}**" if self.game_version else '') +
            f"\nMain version: {f"{discord.utils.format_dt(self.latest_game_update)} ({discord.utils.format_dt(self.latest_game_update, 'R')})" if self.latest_game_update else "*Unknown*"}"
            f"\nBeta version: {f"{discord.utils.format_dt(self.latest_beta_update)} ({discord.utils.format_dt(self.latest_beta_update, 'R')})" if self.latest_beta_update else "*Unknown*"}"
        )))
        if status_lines:
            self.container.add_item(discord.ui.Separator())
            self.container.add_item(discord.ui.TextDisplay(content="### 📡 Game region servers\n" + '\n'.join(status_lines)))
        if self.is_ccu_fetched:
            self.container.add_item(discord.ui.TextDisplay(content=f"Total knights around the world: **{self.global_stats.total}**"))
        self.container.add_item(discord.ui.Separator())
        content = "### 📊 Current CCU of repuls.io\n"
        if not self.is_ccu_fetched:
            content += "*Oh! We're sorry, but something went wrong... Unable to retrieve CCU.*"
        else:
            lines: list[str] = []
            for pl in GamePlaylist:
                count = self.selected_region.get(pl)
                if pl is GamePlaylist.CUSTOMS and count == 0:
                    continue
                lines.append(f"- {pl.label}: {count}")
            content += '\n'.join(lines).strip()
        self.container.add_item(discord.ui.TextDisplay(content=content))

        if self.is_ccu_fetched and len(self.regions) >= 1:
            self.container.add_item(self.select_region_row)
            self.region_select.options = [
                discord.SelectOption(label=region.name.upper(), value=region.name, default=(region == self.selected_region))
                for region in self.regions.values()
            ]
            self.region_select.add_option(
                label=self.global_stats.name.upper(),
                value=self.global_stats.name,
                default=(self.global_stats == self.selected_region)
            )
        self.container.add_item(discord.ui.TextDisplay(content=(
            "-# Repuls live status" + (f" ・ (Data updated on {discord.utils.format_dt(self.updated_at)})" if self.is_ccu_fetched else FOOTER_EMBED)
        )))

        return self

    @select_region_row.select(min_values=1, max_values=1, placeholder="Choose a region...")
    async def region_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_region = self.regions.get(select.values[0], self.global_stats)
        await self.generate_interface()
        await interaction.response.edit_message(view=self)

class StatsCog(commands.Cog, name=CogsNames.STATS):
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot

    @app_commands.command(description="Displays some information (update, CCU, etc.) live from the game")
    async def game_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        game_version = await fetch_game_version(self.bot.playfab_manager)
        server_stats = await fetch_server_stats()
        latest_game_update = await fetch_build_date(PublicAPI.BUILD)
        latest_beta_update = await fetch_build_date(PublicAPI.BETA_BUILD)

        view = GameStatusView(self.bot, game_version, latest_game_update, latest_beta_update, server_stats)
        await view.generate_interface()
        await interaction.followup.send(view=view, ephemeral=True)

    @app_commands.command(description="Retrieves the precise in-game statistics of a given player")
    @app_commands.describe(name="The display name or username of the player to search for")
    async def player_info(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)

        player = await fetch_player(self.bot.playfab_manager, name)
        view = PlayerInfoView(name, player, interaction.user)
        await view.generate_interface()
        await interaction.followup.send(view=view, file=(view.attachment or discord.utils.MISSING), ephemeral=True)

async def setup(bot: "RepulsBot"):
    await bot.add_cog(StatsCog(bot))