import discord
from discord.ext import commands
# IDs and TOKEN file
from private_data import *
from constants import *

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

def admin_or_roles():
    async def predicate(ctx: commands.Context):
        has_admin = ctx.author.guild_permissions.administrator
        has_role = any(role.name in ["Admin", "Moderator"] for role in ctx.author.roles)
        return has_admin or has_role
    return commands.check(predicate)

# ---------------------------------- commands
@bot.hybrid_command(name="ping", description="displays latency of the bot")
async def ping(ctx: commands.Context):
    await ctx.send(f"{CHECK} **pong!**\n(*It took me {round(bot.latency * 1000, 2)}ms to respond to your command!*)")

@bot.hybrid_command(name="aboutserver", description="displays information about the server")
async def aboutserver(ctx: commands.Context):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"About *{guild.name}* server",
        description="Information about this discord server",
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(url = guild.icon.url if guild.icon else None)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Created on", value=guild.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=f"{len(guild.text_channels)} Text | {len(guild.voice_channels)} Voice", inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
    embed.add_field(name="Description", value=guild.description, inline=False)
    embed.set_footer(text=FOOTER_EMBED)
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="game", description="displays information about repuls.io game")
async def game(ctx: commands.Context):
    play_btn_view = discord.ui.View()
    play_btn = discord.ui.Button(
        style=discord.ButtonStyle.link,
        label="PLAY NOW!",
        url=REPULS_LINK
    )
    play_btn_view.add_item(play_btn)
    embed = discord.Embed(
        title=f"What is repuls.io ?",
        url=f"{REPULS_LINK}home",
        description=REPULS_DESCRIPTION,
        color=discord.Color.dark_blue(),
    )
    embed.add_field(name="Leaderboard", value=f"[Leaderboard]({REPULS_LINK}leaderboard)", inline=True)
    embed.add_field(name="Updates", value=f"[Updates]({REPULS_LINK}updates)", inline=True)
    embed.add_field(name="Terms & privacy", value=f"[Privacy]({REPULS_PRIVACY_LINK})", inline=True)
    embed.set_footer(text=FOOTER_EMBED)
    await ctx.send(embed=embed, view=play_btn_view)

@bot.tree.command(name="clean", description="allows you to clean a certain number of messages in a channel")
@admin_or_roles()
async def clean(interaction: discord.Interaction, number: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=number)
    await interaction.followup.send(f"{CHECK} {len(deleted)} messages removed!", ephemeral=True)

# ---------------------------------- bot run
@bot.event
async def on_command_error(ctx: commands.Context, error):
    header = f"{ERROR} **Check failure**!\n"
    footer = f"\n**Ask an administrator for help!**"

    if isinstance(error, commands.CheckFailure):
        await ctx.send(f"{header}*You do not have permission to use this command!*{footer}")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"{header}*Missing argument!*{footer}")
    elif isinstance(error, commands.CommandNotFound):
        pass # do nothing
    else:
        await ctx.send(f"{header}*Unknown error:* `{error}`{footer}")

@bot.event
async def on_ready():
    status_channel = bot.get_channel(STATUS_CHANNEL)
    if status_channel:
        await status_channel.send(f"{bot.user.mention} is now **online**! <:connecte:{CONNECTE_EMOJI}>")
    # sync of slash and hybrid commands
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} command(s) have been synchronized")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    bot.run(TOKEN)