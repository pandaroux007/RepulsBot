import discord
from discord.ext import commands
import platform
# bot file
from cogs.cogs_info import CogsNames
from constants import (
    BotInfo,
    Links,
    FOOTER_EMBED,
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

# ---------------------------------- about cog (see README.md)
class AboutCog(commands.Cog, name=CogsNames.ABOUT):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="aboutmember", description="Displays information about a server member")
    async def aboutmember(self, ctx: commands.Context, member: discord.Member):
        embed = discord.Embed(
            title=f"Information about **{member.display_name}**",
            color=discord.Color.dark_blue(),
        )
        if member.id == self.bot.user.id: # bot presentation
            embed.title = f"Hi {ctx.author.display_name}! How can I help you ?"
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
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="aboutserver", description="Displays information about the server")
    async def aboutserver(self, ctx: commands.Context):
        guild = ctx.guild
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
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="aboutgame", description="Displays information about repuls.io game")
    async def aboutgame(self, ctx: commands.Context):
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

        await ctx.send(embed=embed, view=play_btn_view)

    @commands.hybrid_command(name="avatar", description="Displays a member's avatar")
    async def avatar(self, ctx: commands.Context, member: discord.Member):
        embed = discord.Embed(
            title=f"Avatar of {member.display_name}!",
            color=discord.Color.dark_blue(),
        )
        if member.avatar is not None:
            embed.set_image(url=member.avatar.url)
        else:
            embed.add_field(name="This user has no avatar", value="*nothing to display...*")
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="membercount", description="Get the server member count")
    async def membercount(self, ctx: commands.Context):
        embed = discord.Embed(
            color=discord.Color.dark_blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Members", value=ctx.guild.member_count)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="wiki", description="Everything you need to know about the game")
    async def wiki(self, ctx: commands.Context):
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

        await ctx.send(embed=embed, view=wiki_btn_view)

async def setup(bot: commands.Bot):
    await bot.add_cog(AboutCog(bot))