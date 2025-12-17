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
# bot files
from cogs_list import CogsNames
from utils import possessive
from constants import (
    DefaultEmojis,
    Links,
    GameUrl,
    BotInfo,
    FOOTER_EMBED
)

from faq_data import (
    ServerFAQ,
    GameFAQ
)

# ---------------------------------- faq selector
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=select#discord.ui.Select
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=view#discord.ui.View
class FAQView(discord.ui.View):
    def __init__(self, faq_entries, custom_id):
        super().__init__(timeout=None)
        self.faq_entries = faq_entries
        options = [
            discord.SelectOption(label=entry["question"], value=str(idx))
            for idx, entry in enumerate(faq_entries)
        ]
        self.add_item(FAQSelect(options, faq_entries, custom_id))

class FAQSelect(discord.ui.Select):
    def __init__(self, options, faq_entries, custom_id):
        super().__init__(placeholder="Choose a question...", options=options, custom_id=custom_id)
        self.faq_entries = faq_entries

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        entry = self.faq_entries[idx]
        embed = discord.Embed(
            title=entry["question"],
            description=entry["answer"],
            color=discord.Color.dark_blue()
        )
        await interaction.response.edit_message(embed=embed, view=self.view)

REPULS_WIKI_DESCRIPTION = """
Do you love repuls.io but don't know how the game works, what maps, weapons, top players, game modes, etc. are? 
Then you'll find everything you need on the official Wiki!
"""

REPULS_DESCRIPTION = f"""
[Repuls.io]({GameUrl.GAME}) is the future of browser games.
The best free instantly accessible multiplayer first-person shooter for your browser with no sign-up or payment required!\n
Tired of the same run, aim, shoot gameplay that every shooter does ?! Played one, you played them all! Repuls has you riding bikes, grappling cliffs, piloting mechs and firing miniguns and plasma rifles and stomping vehicles with a giant mech! **That's** the repuls experience son!
"""

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
            description=f"[See on the official website]({GameUrl.ESPORTS})",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=GameUrl.ESPORTS_ROADMAP_URL)
        await interaction.response.send_message(embed=embed)

    # ---------------------------------- "about" commands
    def get_roles(self, roles: Sequence[discord.Role]) -> str:
        # https://stackoverflow.com/questions/68079391/discord-py-info-command-how-to-mention-roles-of-a-member
        return ' '.join([role.mention for role in roles if role.name != "@everyone"])

    def get_emojis(self, emojis: tuple[discord.Emoji]) -> str:
        return ' '.join(str(e) for e in emojis)

    @app_commands.command(description="Displays information about a server member")
    async def about_member(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(
            title=f"Information about **{member.display_name}**",
            color=discord.Color.dark_blue()
        )
        if member.id == self.bot.user.id:
            embed.title = "Hi! How can I help you ?"
            embed.description = (
                f"It's me, {self.bot.user.mention}, the official Discord bot for this server! "
                "If you need help, look at the menu `/` in the bottom right corner and click on me to see what I can do.\n"
                f"And if you prefer to have fun, **go meet the players on [repuls.io]({GameUrl.GAME})**!"
            )
            embed.add_field(
                name='', value=(
                    f"To offer your help, report a bug or give feedback, you can create a ticket, contact "
                    f"the developer <@{self.bot.owner_id}> directly, or create a [GitHub issue]({BotInfo.REPORT})"
                )
            )
        else:
            embed.description = f"Profile: {member.mention}"
            embed.set_thumbnail(url=member.display_avatar.url or None)
            embed.add_field(name="Member name", value=f"{member.name}")
            embed.add_field(name="Nickname", value=member.nick or "*no nickname*")
            embed.add_field(name="Member ID", value=member.id)
            embed.add_field(name="Account created", value=discord.utils.format_dt(member.created_at, 'D'))
            embed.add_field(name="Joined guild", value=discord.utils.format_dt(member.joined_at, 'D'))
            nitro = f"since {discord.utils.format_dt(member.premium_since)}" if member.premium_since else "*Member without nitro*"
            embed.add_field(name="Nitro subscriber", value=nitro)
            embed.add_field(name=f"Roles ({max(len(member.roles) - 1, 0)})", value=f"{self.get_roles(member.roles)}", inline=False)
        
        embed.set_footer(text=FOOTER_EMBED)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(description="Displays information about the server")
    async def about_server(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"About *{guild.name}* server",
            description=f"(**ID** {guild.id})",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=guild.banner.url if guild.banner else None)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created on", value=discord.utils.format_dt(guild.created_at), inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        embed.add_field(name="Channels", value=f"{len(guild.text_channels)} Text | {len(guild.voice_channels)} Voice", inline=True)
        if guild.rules_channel:
            embed.add_field(name="Rules", value=guild.rules_channel.jump_url)
        embed.add_field(name=f"Emojis ({len(guild.emojis)})", value=self.get_emojis(guild.emojis), inline=False)
        embed.add_field(name=f"Roles ({len(guild.roles)})", value=self.get_roles(guild.roles), inline=False)
        if guild.description:
            embed.add_field(name="Description", value=f"*{guild.description}*", inline=False)
        embed.set_footer(text=FOOTER_EMBED)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Displays information about repuls.io game")
    async def about_game(self, interaction: discord.Interaction):
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=f"### [What is repuls.io]({GameUrl.HOME}) ?\n{REPULS_DESCRIPTION}"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.ActionRow(
            discord.ui.Button(
                url=GameUrl.GAME,
                style=discord.ButtonStyle.link,
                label="PLAY NOW!"
            ),
            discord.ui.Button(
                url=GameUrl.LEADERBOARD,
                style=discord.ButtonStyle.link,
                label="Leaderboard"
            ),
            discord.ui.Button(
                url=GameUrl.UPDATES,
                style=discord.ButtonStyle.link,
                label="Updates"
            ),
            discord.ui.Button(
                url=GameUrl.TERMS,
                style=discord.ButtonStyle.link,
                label="Terms & privacy"
            )
        ))
        container.add_item(discord.ui.TextDisplay(content=f"-# **{FOOTER_EMBED}**"))
        view.add_item(container)
        await interaction.response.send_message(view=view)

    @app_commands.command(description="Everything you need to know about the game")
    async def wiki(self, interaction: discord.Interaction):
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=f"### Everything you need to know about repuls.io\n{REPULS_WIKI_DESCRIPTION}"))
        container.add_item(discord.ui.ActionRow(
            discord.ui.Button(
                url=Links.WIKI,
                style=discord.ButtonStyle.link,
                label="Go to the repuls.io Wiki!"
            )
        ))    
        container.add_item(discord.ui.TextDisplay(content=f"-# **{FOOTER_EMBED}**"))
        view.add_item(container)
        await interaction.response.send_message(view=view)

    @app_commands.command(description="Launch the server's interactive FAQ")
    async def serverfaq(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"{possessive(interaction.guild.name)} server FAQ",
            description="👉️ Select a question from the drop-down menu below!",
            color=discord.Color.dark_blue()
        )
        view = FAQView(ServerFAQ.get_data(), custom_id=ServerFAQ.get_id())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(description="Frequently Asked Questions about the repuls.io game")
    async def gamefaq(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Repuls.io game FAQ",
            description="👉️ Select a question from the drop-down menu below!",
            color=discord.Color.dark_blue()
        )
        view = FAQView(GameFAQ.get_data(), custom_id=GameFAQ.get_id())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    # https://github.com/Rapptz/discord.py/blob/master/examples/views/persistent.py
    bot.add_view(FAQView(ServerFAQ.get_data(), custom_id=ServerFAQ.get_id()))
    bot.add_view(FAQView(GameFAQ.get_data(), custom_id=GameFAQ.get_id()))
    
    await bot.add_cog(UsersCog(bot))