"""
This cog provides commands to find and start games.

:copyright: (c) 2026-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
import math
# bot files
from data.cogs import CogsNames
from data.constants import (
    DefaultEmojis,
    GameUrl,
    ASK_HELP
)

from tools.utils import (
    plurial,
    GamePlaylist
)

from tools.stats_parser import (
    fetch_regions_list,
    fetch_games_list
)

from tools.log_builder import (
    LogColor,
    BOTLOG,
    log
)

class GameBrowserView(discord.ui.LayoutView):
    pagination_row = discord.ui.ActionRow()
    region_select_row = discord.ui.ActionRow()
    playlist_select_row = discord.ui.ActionRow()

    def __init__(self, bot: commands.Bot, selected_region: str, regions: list[str]):
        super().__init__()
        self.bot = bot
        self._regions: list[str] = regions
        self._selected_playlist: GamePlaylist = GamePlaylist.WARFARE
        self._selected_region: str = selected_region
        self._selected_page: int = 1
        self._total_pages: int = 1

        self.container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        self.add_item(self.container)

    async def generate_interface(self, interaction: discord.Interaction):
        self.remove_item(self.pagination_row)
        self.remove_item(self.region_select_row)
        self.remove_item(self.playlist_select_row)
        self.container.clear_items()
        self.container.add_item(discord.ui.TextDisplay(content=(
            f"## 🌐 Game currently in progress\n"
            f"➜ region **{self._selected_region.upper()}** | playlist **{self._selected_playlist.label}**\n"
            f"-# **List updated at {discord.utils.format_dt(discord.utils.utcnow(), 'S')}**"
        )))

        games_by_playlist = await fetch_games_list(self._selected_region)
        if not games_by_playlist:
            self.container.add_item(discord.ui.TextDisplay(content=f"*Oops! No ongoing games were found?*{ASK_HELP}"))
            self.container.add_item(discord.ui.Separator())
            await log(
                bot=self.bot, type=BOTLOG, color=LogColor.ORANGE,
                title=f"{DefaultEmojis.WARN} No games in progress found",
                msg=(
                    f"The user {interaction.user.mention} attempted to find an ongoing game in the region `{self._selected_region}` "
                    f"(playlist {self._selected_playlist.label}), but `None` was returned. Is the API unavailable?"
                )
            )
        else:
            all_games = games_by_playlist.get(self._selected_playlist, [])
            filtered_games = [game for game in all_games if not game.is_full]

            MAX_CONTAINER_CHILDREN = 40
            HEADER_COST = 1 # textdisplay
            PER_GAME_COST = 1 + 1 + 1 # section + textdisplay + button
            PAGINATION = 1 + 3 # actionrow + 3 buttons
            RESERVED_FOOTER = 1 + 2 + 2 # separator + 2 actionrow + 2 selects

            available_for_games = MAX_CONTAINER_CHILDREN - RESERVED_FOOTER - HEADER_COST - PAGINATION - 1
            games_per_page = max(1, available_for_games // PER_GAME_COST)

            total_games = len(filtered_games)
            self._total_pages = max(1, math.ceil(total_games / games_per_page))

            start_idx = (self._selected_page - 1) * games_per_page
            end_idx = start_idx + games_per_page
            page_games = filtered_games[start_idx:end_idx]

            if total_games == 0:
                self.container.add_item(discord.ui.TextDisplay(content="🔎 Oops! It looks like all the games matching your settings are full...\nTry another region or another mode?"))
            else:
                for game in page_games:
                    self.container.add_item(discord.ui.Section(
                        discord.ui.TextDisplay(content=(
                            f"***{game.name}*** ({game.players} {plurial('player', game.players)})\n"
                            f"-# **{game.mode}** in **{game.map}**"
                        )),
                        accessory=discord.ui.Button(label="Join", url=f"{GameUrl.GAME}/?r={self._selected_region}&game={game.web_port}")
                    ))

                if self._total_pages > 1:
                    self.container.add_item(self.pagination_row)
                    self._prev_page.disabled = (self._selected_page <= 1)
                    self._next_page.disabled = (self._selected_page >= self._total_pages)
                    self._page_indicator.label = f"{self._selected_page}/{self._total_pages}"

        self.container.add_item(discord.ui.Separator())
        self.container.add_item(self.region_select_row)
        self.region_select.options = [
            discord.SelectOption(label=region, value=region, default=(region == self._selected_region))
            for region in self._regions
        ]
        self.container.add_item(self.playlist_select_row)
        self.playlist_select.options = [
            discord.SelectOption(
                label=playlist.label,
                value=playlist.code,
                description=playlist.description,
                default=(playlist == self._selected_playlist)
            )
            for playlist in GamePlaylist
        ]

        await interaction.response.edit_message(view=self)

    @region_select_row.select(min_values=1, max_values=1, placeholder="Choose a region...")
    async def region_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self._selected_region = select.values[0]
        self._selected_page = 1
        await self.generate_interface(interaction)

    @playlist_select_row.select(min_values=1, max_values=1, placeholder="Choose a game playlist...", )
    async def playlist_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self._selected_playlist = GamePlaylist.from_code(select.values[0])
        self._selected_page = 1
        await self.generate_interface(interaction)

    # ---------------------------------- pagination buttons
    @pagination_row.button(label="🞀", style=discord.ButtonStyle.secondary)
    async def _prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self._selected_page <= 1:
            self._selected_page = 1
        elif self._selected_page > 1:
            self._selected_page -= 1
        await self.generate_interface(interaction)

    @pagination_row.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def _page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @pagination_row.button(label="🞂", style=discord.ButtonStyle.secondary)
    async def _next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self._selected_page >= self._total_pages:
            self._selected_page = self._total_pages
        elif self._selected_page < self._total_pages:
            self._selected_page += 1
        await self.generate_interface(interaction)

class RegionSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot, options: list[discord.SelectOption], regions_list: list[str]):
        super().__init__(
            min_values=1, max_values=1,
            placeholder="Choose a region...",
            options=options
        )
        self.bot = bot
        self.regions_list = regions_list

    async def callback(self, interaction: discord.Interaction):
        game_browser = GameBrowserView(self.bot, self.values[0], self.regions_list)
        await game_browser.generate_interface(interaction)

class GameBrowserCog(commands.Cog, name=CogsNames.GAME_BROWSER):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description="Allows navigation within the current games")
    async def server_browser(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        view = discord.ui.LayoutView()
        view.add_item(container)
        container.add_item(discord.ui.TextDisplay(content="### 🧭 Select a region to search"))

        regions_list = await fetch_regions_list()

        if not regions_list:
            container.add_item(discord.ui.TextDisplay(content="*Hmm... No regions seem to be available... Please try again later?*"))
            await interaction.followup.send(view=view, ephemeral=True)
            return

        container.add_item(discord.ui.ActionRow(
            RegionSelect(
                self.bot, regions_list=regions_list,
                options = [
                    discord.SelectOption(label=region, value=region)
                    for region in regions_list
                ]
            )
        ))

        await interaction.followup.send(view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(GameBrowserCog(bot))