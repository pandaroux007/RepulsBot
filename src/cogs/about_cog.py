import discord
from discord.ext import commands
from discord import app_commands
import platform
# bot file
from cogs_list import CogsNames
from constants import (
    BotInfo,
    Links,
    FOOTER_EMBED,
)

from faq_data import (
    ServerFAQ,
    GameFAQ
)

REPULS_WIKI_DESCRIPTION = """
Do you love repuls.io but don't know how the game works, what maps, weapons, top players, game modes, etc. are?\n
Then you'll find everything you need on the official Wiki!
"""

REPULS_DESCRIPTION = f"""
[Repuls.io]({Links.REPULS_GAME}) is the future of browser games.
The best free instantly accessible multiplayer first-person shooter for your browser with no sign-up or payment required!\n
Tired of the same run, aim, shoot gameplay that every shooter does ?! Played one, you played them all! Repuls has you riding bikes, grappling cliffs, piloting mechs and firing miniguns and plasma rifles and stomping vehicles with a giant mech! **That's** the repuls experience son!
"""

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

# ---------------------------------- about cog (see README.md)
class AboutCog(commands.Cog, name=CogsNames.ABOUT):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="aboutmember", description="Displays information about a server member")
    async def aboutmember(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(
            title=f"Information about **{member.display_name}**",
            color=discord.Color.dark_blue(),
        )
        if member.id == self.bot.user.id: # bot presentation
            embed.title = f"Hi {interaction.user.display_name}! How can I help you ?"
            embed.description = BotInfo.DESCRIPTION.format(name=self.bot.user.mention,
                                                       server=Links.DISCORD_INVITE,
                                                       game=Links.REPULS_GAME)
            embed.add_field(name=f"{BotInfo.NAME}", value=f"v{BotInfo.VERSION}")
            embed.add_field(name="discord.py", value=f"v{discord.__version__}")
            embed.add_field(name="python", value=f"v{platform.python_version()}")
        else: # other member's informations
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Member name", value=f"{member.mention}", inline=False)
            embed.add_field(name="Member id:", value=f"{member.id}", inline=False)
            embed.add_field(name="Nickname:", value=f"{member.nick}", inline=False)
            embed.add_field(name="Joined at:", value=f"{member.joined_at}", inline=False)
            # https://stackoverflow.com/questions/68079391/discord-py-info-command-how-to-mention-roles-of-a-member
            roles = " ".join([role.mention for role in member.roles if role.name != "@everyone"])
            embed.add_field(name="Roles:", value=f"{roles}", inline=False)
        embed.set_footer(text=FOOTER_EMBED)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="aboutserver", description="Displays information about the server")
    async def aboutserver(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"About *{guild.name}* server",
            description="Information about this discord server",
            color=discord.Color.dark_blue(),
        )
        embed.set_thumbnail(url = guild.icon.url if guild.icon else None)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created on", value=guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=f"{len(guild.text_channels)} Text | {len(guild.voice_channels)} Voice", inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        if guild.description:
            embed.add_field(name="Description", value=guild.description, inline=False)
        embed.set_footer(text=FOOTER_EMBED)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="aboutgame", description="Displays information about repuls.io game")
    async def aboutgame(self, interaction: discord.Interaction):
        play_btn_view = discord.ui.View()
        play_btn = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="PLAY NOW!",
            url=Links.REPULS_GAME
        )
        play_btn_view.add_item(play_btn)
        embed = discord.Embed(
            title="What is repuls.io ?",
            url=f"{Links.REPULS_GAME}home",
            description=REPULS_DESCRIPTION,
            color=discord.Color.blue(),
        )
        embed.add_field(name="Leaderboard", value=f"[Leaderboard]({Links.REPULS_GAME}leaderboard)", inline=True)
        embed.add_field(name="Updates", value=f"[Updates]({Links.REPULS_GAME}updates)", inline=True)
        embed.add_field(name="Terms & privacy", value=f"[Privacy]({Links.GAME_PRIVACY})", inline=True)
        embed.set_footer(text=FOOTER_EMBED)

        await interaction.response.send_message(embed=embed, view=play_btn_view)

    @app_commands.command(name="wiki", description="Everything you need to know about the game")
    async def wiki(self, interaction: discord.Interaction):
        wiki_btn_view = discord.ui.View()
        wiki_btn = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Go to the repuls.io Wiki!",
            url=Links.REPULS_WIKI
        )
        wiki_btn_view.add_item(wiki_btn)
        embed = discord.Embed(
            title="Everything you need to know about repuls.io",
            description=REPULS_WIKI_DESCRIPTION,
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(embed=embed, view=wiki_btn_view)

    @app_commands.command(name="serverfaq", description="Launch the server's interactive FAQ")
    async def serverfaq(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"{interaction.guild.name}{"\'" if interaction.guild.name.endswith('s') else "'s"} server FAQ",
            description="👉️ Select a question from the drop-down menu below!",
            color=discord.Color.blue()
        )
        view = FAQView(ServerFAQ.get_data(), custom_id=ServerFAQ.get_id())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="gamefaq", description="Frequently Asked Questions about the repuls.io game")
    async def gamefaq(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Repuls.io game FAQ",
            description="👉️ Select a question from the drop-down menu below!",
            color=discord.Color.blue()
        )
        view = FAQView(GameFAQ.get_data(), custom_id=GameFAQ.get_id())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    # https://github.com/Rapptz/discord.py/blob/master/examples/views/persistent.py
    bot.add_view(FAQView(ServerFAQ.get_data(), custom_id=ServerFAQ.get_id()))
    bot.add_view(FAQView(GameFAQ.get_data(), custom_id=GameFAQ.get_id()))

    await bot.add_cog(AboutCog(bot))