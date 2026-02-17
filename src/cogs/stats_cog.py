"""
This cog doesn't just contain statistical commands; it covers
all commands that interact directly with the game via its APIs.

:copyright: (c) 2026-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
import datetime
# bot files
from data.cogs import CogsNames
from data.constants import DefaultEmojis
from tools.api_client import InfoSystemAPI

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

class StatsCog(commands.Cog, name=CogsNames.STATS):
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot

    @app_commands.command(description="Displays the current CCU of repuls (global and by region)")
    async def game_ccu(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        game_version = await InfoSystemAPI.fetch_game_version(self.bot.playfab_manager)

        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        view = discord.ui.LayoutView()
        view.add_item(container)
        container.add_item(discord.ui.TextDisplay(content="### 📊 Current CCU of repuls.io"))
        if game_version:
            container.add_item(discord.ui.TextDisplay(content=f"*Current game version: **`{game_version}`***"))

        updated_at, regions, global_stats = await InfoSystemAPI.fetch_servers()
        if not regions:
            container.add_item(discord.ui.TextDisplay(content="*Oh! We're sorry, but something went wrong... Unable to retrieve stats.*"))
            await interaction.followup.send(view=view)
            return

        lines: list = []
        for region in regions:
            # https://stackoverflow.com/questions/76674727/conditional-multi-line-string-in-python
            lines.append(
                f"({DefaultEmojis.ONLINE if region.status == "ok" else f"Status: {region.status}"}) **`{region.name}`** - {region.total} players\n"
                f"- Warfare: {region.warfare}\n"
                f"- Hardcore: {region.hardcore}\n"
                f"- Casual: {region.casual}\n"
                f"{bool(region.customs) * f"- Customs: {region.customs}\n"}"
            )

        stats_text = "\n".join(lines).strip()
        container.add_item(discord.ui.TextDisplay(content=f"Total knights around the world: **{global_stats.total}**"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(content=stats_text))
        if updated_at:
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(content=f"-# Data updated on {discord.utils.format_dt(datetime.datetime.fromisoformat(updated_at))}"))

        await interaction.followup.send(view=view)

async def setup(bot: "RepulsBot"):
    await bot.add_cog(StatsCog(bot))