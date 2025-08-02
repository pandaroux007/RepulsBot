"""
This cog contains all the commands accessible to everyone
(information and help commands are separated in other cogs)

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
# bot files
from cogs_list import CogsNames
from constants import DefaultEmojis

# ---------------------------------- users cog (see README.md)
class UsersCog(commands.Cog, name=CogsNames.USERS):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Displays latency of the bot")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{DefaultEmojis.CHECK} **pong!** (*It took me {round(self.bot.latency * 1000, 2)}ms to respond to your command!*)")

    @app_commands.command(name="avatar", description="Displays a member's avatar")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(
            title=f"Avatar of {member.display_name}!",
            color=discord.Color.dark_blue(),
        )
        if member.avatar is not None:
            embed.set_image(url=member.avatar.url)
        else:
            embed.add_field(name="This user has no avatar", value="*nothing to display...*")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="membercount", description="Get the server member count")
    async def membercount(self, interaction: discord.Interaction):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Members", value=interaction.guild.member_count)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="esports_roadmap", description="displays the eSports competitions of the year")
    async def esports_roadmap(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Repuls eSports roadmap!",
            description="[See on the official website](https://repuls.io/esports)",
            color=discord.Color.blue()
        )
        embed.set_image(url="https://repuls.io/esports/REPULS_eSPORTS_ROADMAP.png")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(UsersCog(bot))