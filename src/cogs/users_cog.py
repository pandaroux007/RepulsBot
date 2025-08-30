"""
This cog contains all the commands accessible to everyone
(information and help commands are separated in other cogs)

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import re
# bot files
from cogs_list import CogsNames
from utils import get_leaderboard_emote
from constants import (
    DefaultEmojis,
    Links,
    ASK_HELP
)

ESPORTS_ROADMAP_URL = "https://repuls.io/esports/REPULS_eSPORTS_ROADMAP.png"

MODE_CHOICES = {
    "Capture The Flag": "CTF",
    "Free For All": "FFA",
    "Control Point": "KOTH",
    "Team Deathmatch": "TDM"
}
PERIOD_CHOICES = ["daily", "weekly", "global"]
LEADERBOARD_API = "https://leaderboards.docskigames.com/api/getScore"

def clean_name(name: str) -> str:
    """ remove HTML color tags around clan name """
    return re.sub(r"<[^>]+>", "", name).strip()

class PageNavigator(discord.ui.ActionRow):
    def __init__(self, leaderboard_view: LeaderboardView):
        super().__init__()
        self.leaderboard_view = leaderboard_view
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.link, url=f"{Links.GAME}leaderboard", emoji="🌐"))

    def update_buttons_state(self):
        self.first_button.disabled = self.leaderboard_view.page <= 1
        self.prev_button.disabled = self.leaderboard_view.page <= 1
        self.next_button.disabled = self.leaderboard_view.page >= self.leaderboard_view.total_pages
        self.last_button.disabled = self.leaderboard_view.page >= self.leaderboard_view.total_pages

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="⏮️", label="First", custom_id="first")
    async def first_button(self, interaction: discord.Interaction, bt: discord.ui.Button):
        self.leaderboard_view.page = 1
        await self.leaderboard_view.update_leaderboard()
        self.update_buttons_state()
        await interaction.response.edit_message(view=self.leaderboard_view)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="◀️", label="Prev", custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, bt: discord.ui.Button):
        self.leaderboard_view.page -= 1
        await self.leaderboard_view.update_leaderboard()
        self.update_buttons_state()
        await interaction.response.edit_message(view=self.leaderboard_view)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="▶️", label="Next", custom_id="next")
    async def next_button(self, interaction: discord.Interaction, bt: discord.ui.Button):
        self.leaderboard_view.page += 1
        await self.leaderboard_view.update_leaderboard()
        self.update_buttons_state()
        await interaction.response.edit_message(view=self.leaderboard_view)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="⏭️", label="Last", custom_id="last")
    async def last_button(self, interaction: discord.Interaction, bt: discord.ui.Button):
        self.leaderboard_view.page = self.leaderboard_view.total_pages
        await self.leaderboard_view.update_leaderboard()
        self.update_buttons_state()
        await interaction.response.edit_message(view=self.leaderboard_view)

class SelectMode(discord.ui.ActionRow):
    def __init__(self, leaderboard_view: LeaderboardView):
        super().__init__()
        self.leaderboard_view = leaderboard_view
        self.select_mode.options = [
            discord.SelectOption(label=name, value=val, default=(val==self.leaderboard_view.mode))
            for name, val in MODE_CHOICES.items()
        ]

    @discord.ui.select(custom_id="select_mode", placeholder="Select mode...")
    async def select_mode(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.leaderboard_view.mode = select.values[0]
        self.leaderboard_view.page = 1
        await self.leaderboard_view.update_leaderboard()
        await interaction.response.edit_message(view=self.leaderboard_view)

class SelectPeriod(discord.ui.ActionRow):
    def __init__(self, leaderboard_view: LeaderboardView):
        super().__init__()
        self.leaderboard_view = leaderboard_view
        self.select_period.options = [
            discord.SelectOption(label=period.capitalize(), value=period, default=(period==self.leaderboard_view.period))
            for period in PERIOD_CHOICES
        ]

    @discord.ui.select(custom_id="select_period", placeholder="Select period...")
    async def select_period(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.leaderboard_view.period = select.values[0]
        self.leaderboard_view.page = 1
        await self.leaderboard_view.update_leaderboard()
        await interaction.response.edit_message(view=self.leaderboard_view)

class LeaderboardView(discord.ui.LayoutView):
    """ The container object must be a class attribute, not an instance attribute, for discord.py """
    container = discord.ui.Container()

    def __init__(self):
        """ However, one can construct the interface after initialization """
        super().__init__()
        self.mode = list(MODE_CHOICES.values())[0]
        self.period = PERIOD_CHOICES[0]
        self.page = 1
        self.total_pages: int = -1
        self.total_players: int = -1

    async def fetch_leaderboard_data(self) -> dict | None:
        url = f"{LEADERBOARD_API}?boardName=lb_{self.mode}_{self.period}&page={self.page}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                return await response.json()

    def build_interface(self, body: str) -> None:
        self.container.clear_items()
        self.container.accent_color = discord.Color.dark_blue()

        self.container.add_item(discord.ui.TextDisplay(content=f"## 🏆 Repuls leaderboard ({self.mode.replace('_', ' ').upper()} {self.period.capitalize()})"))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.TextDisplay(content=body))
        self.container.add_item(discord.ui.Separator())
        # ---------------------------------- navigation
        self.container.add_item(PageNavigator(self))
        self.container.add_item(SelectMode(self))
        self.container.add_item(SelectPeriod(self))

        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.TextDisplay(content=f"-# Page {self.page} of {self.total_pages} ({self.total_players} players in total)"))

    async def update_leaderboard(self) -> None:
        data = await self.fetch_leaderboard_data()
        if not data:
            content = f"{DefaultEmojis.ERROR} An error occurred while getting the leaderboard\n> API Error: Could not fetch leaderboard!{ASK_HELP}",
            self.container.accent_color = discord.Color.red()
        
        entries = data.get("data", [])
        self.total_pages = data.get("totalPages", 1)
        self.total_players = data.get("totalCount", '?')

        leaderboard_text = []
        for idx, entry in enumerate(entries, start=1): # start=1 + (self.page - 1) * len(entries)
            pseudo = clean_name(entry.get("key", "?"))
            score = entry.get("value", "?")
            header = get_leaderboard_emote(idx, self.page)
            leaderboard_text.append(f"{header} `{score}` - **{pseudo}**")
        content = '\n'.join(leaderboard_text) or "*No results for this page.*"
        
        self.build_interface(content)

# ---------------------------------- users cog (see README.md)
class UsersCog(commands.Cog, name=CogsNames.USERS):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description="Displays latency of the bot")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{DefaultEmojis.CHECK} **pong!** (*It took me {round(self.bot.latency * 1000, 2)}ms to respond to your command!*)")

    @app_commands.command(description="Displays a member's avatar")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(
            title=f"Avatar of {member.display_name}!",
            color=discord.Color.dark_blue()
        )
        if member.avatar is not None:
            embed.set_image(url=member.avatar.url)
        else:
            embed.add_field(name="This user has no avatar", value="*nothing to display...*")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Get the server member count")
    async def membercount(self, interaction: discord.Interaction):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Members", value=interaction.guild.member_count)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Displays the eSports competitions of the year")
    async def esports_roadmap(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Repuls eSports roadmap!",
            description="[See on the official website](https://repuls.io/esports)",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=ESPORTS_ROADMAP_URL)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Allows you to navigate the game leaderboard")
    async def repuls_leaderboard(self, interaction: discord.Interaction):
        leaderboard = LeaderboardView()
        await leaderboard.update_leaderboard()
        await interaction.response.send_message(view=leaderboard, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(UsersCog(bot))