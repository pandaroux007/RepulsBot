"""
This cog contains all the commands accessible to everyone (FAQ and information
commands, among other things - help command is separated in other cog)

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
from typing import Sequence
from enum import Enum
import aiohttp
from datetime import datetime
# bot files
from data.cogs import CogsNames
from data.constants import (
    DefaultEmojis,
    GameUrl,
    FOOTER_EMBED
)

from data.faq import (
    SERVER_FAQ_DATA,
    GAME_FAQ_DATA
)

def get_roles(roles: Sequence[discord.Role]) -> str:
    # https://stackoverflow.com/questions/68079391/discord-py-info-command-how-to-mention-roles-of-a-member
    return ' '.join([role.mention for role in roles if role.name != "@everyone"])

def get_emojis(emojis: tuple[discord.Emoji]) -> str:
    return ' '.join(str(e) for e in emojis)

# ---------------------------------- game info view
class WikiSearchModal(discord.ui.Modal, title="Search on wiki"):
    header = discord.ui.TextDisplay("What do you want to search for on the Repuls wiki?")
    query = discord.ui.Label(
        text="What questions do you have?",
        component=discord.ui.TextInput(
            max_length=100,
            placeholder="Type your query here..."
        )
    )

    def __init__(self, parent: "GameInfoView"):
        super().__init__()
        self.parent_view = parent

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.current_view = GameInfoState.WIKI
        self.parent_view.latest_interaction = interaction

        assert isinstance(self.query.component, discord.ui.TextInput)
        # see https://community.fandom.com/api.php and https://www.mediawiki.org/wiki/API:Search
        query = self.query.component.value
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": 0, # articles
            "srlimit": 5,
            "format": "json"
        }
        results = []
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{GameUrl.WIKI}/api.php", params=params) as resp:
                data: dict = await resp.json()
                for hit in dict(data.get("query", {})).get("search", []):
                    assert isinstance(hit, dict)
                    results.append({
                        "title": hit["title"],
                        "pageid": hit["pageid"],
                        # "size": hit["size"],
                        "wordcount": hit.get("wordcount", 0),
                        "timestamp": datetime.fromisoformat(hit["timestamp"])
                    })

        self.parent_view.latest_wiki_query = query
        self.parent_view.latest_wiki_result = results or None
        self.parent_view.generate_interface()
        await interaction.response.edit_message(view=self.parent_view)
        self.parent_view.latest_interaction = interaction

class GameInfoState(Enum):
    HOME = 1
    SERVER_FAQ = 2
    GAME_FAQ = 3
    WIKI = 4

class GameInfoView(discord.ui.LayoutView):
    menu_row = discord.ui.ActionRow()
    select_row = discord.ui.ActionRow()

    def __init__(self, bot: commands.Bot, author: discord.Member):
        super().__init__(timeout=300)
        self.bot = bot
        self.container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        self.add_item(self.container)

        self.command_author: discord.Member = author
        self.current_faq_id: int = -1
        self.current_view: GameInfoState = GameInfoState.HOME
        self.latest_wiki_query: str | None = None
        self.latest_wiki_result: list | None = None
        self.latest_interaction: discord.Interaction | None = None

    def generate_interface(self, remove_componants: bool = False):
        self.remove_item(self.menu_row)
        self.remove_item(self.select_row)
        self.container.clear_items()

        if self.current_view == GameInfoState.SERVER_FAQ or self.current_view == GameInfoState.GAME_FAQ:
            if self.current_view == GameInfoState.SERVER_FAQ:
                self.server_faq_button.disabled = True
                data = SERVER_FAQ_DATA
            elif self.current_view == GameInfoState.GAME_FAQ:
                self.game_faq_button.disabled = True
                data = GAME_FAQ_DATA

            if not remove_componants:
                self.container.add_item(self.select_row)
                self.question_select.options = [
                    discord.SelectOption(label=entry["question"], value=str(idx), default=(idx == self.current_faq_id))
                    for idx, entry in enumerate(data)
                ]
                self.container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

            if self.current_faq_id == -1:
                content = "*➜ Select a question from the drop-down menu above!*"
            else:
                content = f"### {data[self.current_faq_id]["question"]}\n{data[self.current_faq_id]["answer"]}"
            self.container.add_item(discord.ui.TextDisplay(content=content))
        elif self.current_view == GameInfoState.WIKI:
            self.home_button.disabled = False
            self.server_faq_button.disabled = False
            self.game_faq_button.disabled = False
            if self.latest_wiki_result:
                self.container.add_item(discord.ui.TextDisplay(content=f"### 🔎 Wiki search - {len(self.latest_wiki_result)} result(s) for \"{self.latest_wiki_query}\""))
                # https://www.mediawiki.org/wiki/Help:Page_ID#How_to_access_a_page_by_page_ID
                for idx, result in enumerate(self.latest_wiki_result):
                    self.container.add_item(discord.ui.Section((
                            f"➜ **{result["title"]}**\n"
                            f"-# **Latest edition {discord.utils.format_dt(result["timestamp"], 'R')} | {result["wordcount"]} word(s)**"
                        ), accessory=discord.ui.Button(url=f"{GameUrl.WIKI}/w/index.php?curid={result["pageid"]}", label="Go read it")
                    ))
                    if not idx >= len(self.latest_wiki_result) - 1:
                        self.container.add_item(discord.ui.Separator())
            else:
                self.container.add_item(discord.ui.TextDisplay(content=f"> 🛸 No results for search `{self.latest_wiki_query}`... Try something else?"))
        else:
            self.home_button.disabled = True
            self.container.add_item(discord.ui.Section((
                    f"### What is repuls.io ?\n"
                    f"➜ [Repuls.io]({GameUrl.HOME}) is the future of browser games. "
                    "The best free instantly accessible multiplayer FPS for your browser with no sign-up or payment required!"
                ), accessory=discord.ui.Thumbnail(media=GameUrl.ICON)
            ))
            self.container.add_item(discord.ui.TextDisplay(content=(
                "Tired of the same run, aim, shoot gameplay that every shooter does ?! Played one, you played them all! "
                "Repuls has you riding bikes, grappling cliffs, piloting mechs and firing miniguns and plasma rifles and stomping vehicles with "
                "a giant mech! **That's** the repuls experience son!"
            )))
            self.container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
            self.container.add_item(discord.ui.ActionRow(
                discord.ui.Button(url=GameUrl.GAME, label="PLAY NOW!"),
                discord.ui.Button(url=GameUrl.BETA, label="BETA"),
                discord.ui.Button(url=GameUrl.LEADERBOARD, label="Leaderboard"),
                discord.ui.Button(url=GameUrl.UPDATES, label="Updates"),
                discord.ui.Button(url=GameUrl.TERMS, label="Privacy")
            ))
            if not remove_componants:
                self.container.add_item(discord.ui.TextDisplay(content="Use the menu below to navigate the FAQs or search for an article on the wiki."))

        if not remove_componants:
            self.container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
            self.container.add_item(self.menu_row)
        else:
            self.container.add_item(discord.ui.TextDisplay(content=(
                f"-# *{self.current_view.name.replace('_', ' ')} mode ・ This view expired {discord.utils.format_dt(discord.utils.utcnow(), 'R')}*"
            )))
        return self

    async def interaction_check(self, interaction: discord.Interaction):
        allowed = (interaction.user.id == self.command_author.id)
        if not allowed:
            await interaction.response.send_message(content=f"> {DefaultEmojis.NO_ENTRY} You are not the author of this command.", ephemeral=True)
        return allowed

    async def on_timeout(self):
        # https://gist.github.com/Soheab/cfd769870b7b6eaf00a7aebf5293a622
        if self.latest_interaction:
            if self.current_view == GameInfoState.SERVER_FAQ or self.current_view == GameInfoState.GAME_FAQ:
                if self.current_faq_id == -1:
                    await self.latest_interaction.delete_original_response()
                    return
            elif self.current_view == GameInfoState.WIKI and not self.latest_wiki_result:
                await self.latest_interaction.delete_original_response()
                return
            self.generate_interface(remove_componants=True)
            await self.latest_interaction.edit_original_response(view=self)

    # ---------------------------------- faq select
    @select_row.select(min_values=1, max_values=1, placeholder="Choose a question...")
    async def question_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.current_faq_id = int(select.values[0])
        self.generate_interface()
        await interaction.response.edit_message(view=self)
        self.latest_interaction = interaction

    # ---------------------------------- menu
    @menu_row.button(emoji='🏠', label="Home")
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_view = GameInfoState.HOME
        self.server_faq_button.disabled = False
        self.game_faq_button.disabled = False
        self.generate_interface()
        await interaction.response.edit_message(view=self)
        self.latest_interaction = interaction

    @menu_row.button(emoji='💬', label="Discord server FAQ")
    async def server_faq_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_view = GameInfoState.SERVER_FAQ
        self.current_faq_id = -1
        self.home_button.disabled = False
        self.game_faq_button.disabled = False
        self.generate_interface()
        await interaction.response.edit_message(view=self)
        self.latest_interaction = interaction

    @menu_row.button(emoji='🎮', label="Game FAQ")
    async def game_faq_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_view = GameInfoState.GAME_FAQ
        self.current_faq_id = -1
        self.home_button.disabled = False
        self.server_faq_button.disabled = False
        self.generate_interface()
        await interaction.response.edit_message(view=self)
        self.latest_interaction = interaction

    @menu_row.button(label="Wiki search", emoji='🔎', style=discord.ButtonStyle.primary)
    async def wiki_search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WikiSearchModal(self))
        self.latest_interaction = interaction

class UsersCog(commands.Cog, name=CogsNames.USERS):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description="Displays a member's avatar")
    @app_commands.guild_only()
    async def member_avatar(self, interaction: discord.Interaction, member: discord.Member):
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
    @app_commands.guild_only()
    async def member_count(self, interaction: discord.Interaction):
        await interaction.response.send_message(content=f"> There are currently **{interaction.guild.member_count} members** here! ({discord.utils.format_dt(discord.utils.utcnow())})")

    @app_commands.command(description="Displays the eSports competitions of the year")
    @app_commands.guild_only()
    async def esports_roadmap(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Repuls eSports roadmap!",
            description=f"[See on the official website]({GameUrl.ESPORTS_ROADMAP})",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=GameUrl.ESPORTS_ROADMAP_IMG)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="View a member's permissions in a specific channel")
    @app_commands.guild_only()
    @app_commands.describe(
        target="User to inspect (you by default)",
        channel="Channel to analyze (this one by default)"
    )
    async def viewperms(self, interaction: discord.Interaction, target: discord.Member = None, channel: discord.abc.GuildChannel = None):
        target = target or interaction.user
        channel = channel or interaction.channel

        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        view = discord.ui.LayoutView()
        view.add_item(container)
        if target.is_timed_out():
            container.add_item(discord.ui.TextDisplay(content="> *🛡️ This user currently has no permissions on this server*"))
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        allowed_list: list[str] = []
        for name, is_allowed in channel.permissions_for(target):
            if is_allowed:
                allowed_list.append(name.replace('_', ' ').title())

        container.add_item(discord.ui.TextDisplay(content=f"### Perms of {target.mention} in {channel.mention}\n"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(content=", ".join(allowed_list) if allowed_list else "*No permissions in this channel*"))

        await interaction.response.send_message(view=view, ephemeral=True)

    # ---------------------------------- "about" commands
    @app_commands.command(description="Displays information about a server member")
    @app_commands.guild_only()
    async def member_info(self, interaction: discord.Interaction, member: discord.Member):
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        if member.id == self.bot.user.id:
            container.add_item(discord.ui.TextDisplay(content="### Hi! How can I help you ?"))
            container.add_item(discord.ui.TextDisplay(content=(
                f"It's me, {self.bot.user.mention}, the official Discord bot for this server! "
                "If you need help, look at the menu `/` in the bottom right corner and click on me to see what I can do. "
                f"And if you prefer to have fun, **go meet the players on [repuls.io]({GameUrl.GAME})**!\n"
                f"-# Discord WebSocket latency: **{round(self.bot.latency * 1000, 2)}ms**"
            )))
        else:
            content = discord.ui.TextDisplay(content=(
                f"**Profile**: {member.mention}\n"
                f"**Member name**: {member.name}" + (f" | **Nickname**: {member.nick}\n" if member.nick else '\n') +
                f"**Account created**: {discord.utils.format_dt(member.created_at, 'D')}\n"
                f"**Joined guild**: {discord.utils.format_dt(member.joined_at, 'D')}\n" +
                (f"**Latest server boost**: {discord.utils.format_dt(member.premium_since)}" if member.premium_since else '')
            ))
            container.add_item(discord.ui.Section(content, accessory=discord.ui.Thumbnail(member.display_avatar.url)))
            roles_number = len(member.roles) - 1
            if roles_number >= 1:
                container.add_item(discord.ui.TextDisplay(content=(
                    f"### Roles ({roles_number})\n**Most important role**: {member.top_role.mention}\n>>> {get_roles(member.roles)}"
                )))

            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(content=f"-# Member ID: *{member.id}* ・ **{FOOTER_EMBED}**"))

        view = discord.ui.LayoutView()
        view.add_item(container)
        await interaction.response.send_message(view=view, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(description="Displays information about this discord server")
    @app_commands.guild_only()
    async def server_info(self, interaction: discord.Interaction):
        guild = interaction.guild
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        if guild.banner:
            container.add_item(discord.ui.MediaGallery(
                discord.MediaGalleryItem(guild.banner.url)
            ))
            container.add_item(discord.ui.Separator())

        content = discord.ui.TextDisplay(content=(
            f"**Owner**: {guild.owner.mention}\n" +
            (f"**Rules**: {guild.rules_channel.jump_url}\n" if guild.rules_channel else '') +
            f"**Members**: {guild.member_count}\n"
            f"**Created on**: {discord.utils.format_dt(guild.created_at)}\n"
            f"**Channels**: {len(guild.text_channels)} Text | {len(guild.voice_channels)} Voice | {len(guild.categories)} Categories\n" +
            (f"### Boosts ({len(guild.premium_subscription_count)})\n>>> **From these members**:\n{'\n'.join([f"- {member.mention} (since {discord.utils.format_dt(member.premium_since)})" for member in guild.premium_subscribers])}"  if guild.premium_subscription_count else '')
        ))
        container.add_item(discord.ui.Section(content, accessory=discord.ui.Thumbnail(guild.icon.url)) if guild.icon else content)

        if guild.description:
            container.add_item(discord.ui.TextDisplay(content=f"### Description\n>>> {guild.description}"))
        if guild.emojis:
            container.add_item(discord.ui.TextDisplay(content=f"### Emojis ({len(guild.emojis)})\n>>> {get_emojis(guild.emojis)}"))
        if guild.roles:
            container.add_item(discord.ui.TextDisplay(content=f"### Roles ({len(guild.roles)})\n>>> {get_roles(guild.roles)}"))

        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(content=f"-# **{guild.name}** Server ID: *{guild.id}* ・ **{FOOTER_EMBED}**"))

        view = discord.ui.LayoutView()
        view.add_item(container)
        await interaction.response.send_message(view=view, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(description="Displays the game summary and provides access to the FAQs and wiki")
    @app_commands.guild_only()
    async def game_info(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = GameInfoView(self.bot, interaction.user)
        view.generate_interface()
        view.latest_interaction = interaction
        await interaction.followup.send(view=view, allowed_mentions=discord.AllowedMentions.none())

async def setup(bot: commands.Bot):
    await bot.add_cog(UsersCog(bot))