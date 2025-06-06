import discord
from discord.ext import commands
# bot files
from private import *
from constants import *

# -------------------------------------------------------------------- discord bot creation
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

@bot.hybrid_command(name="aboutmember", description="displays information about a server member")
async def aboutmember(ctx: commands.Context, member: discord.Member):
    embed = discord.Embed(
        title=f"Information about **{member.display_name}**",
        color=discord.Color.dark_blue(),
    )
    embed.set_thumbnail(url=member.avatar.url)
    if member.id == bot.user.id:
        embed.title = f"Hi {ctx.author.display_name}! How can I help you ?"
        embed.description = BOT_DESCRIPTION.format(name=bot.user.mention,
                                                   server=DISCORD_INVITE,
                                                   game=REPULS_LINK)
    else:
        embed.add_field(name="Member name", value=f"{member.mention}", inline=False)
        embed.add_field(name="Member id:", value=f"{member.id}", inline=False)
        embed.add_field(name="Nickname:", value=f"{member.nick}", inline=False)
        embed.add_field(name="Joined at:", value=f"{member.joined_at}", inline=False)
        # https://stackoverflow.com/questions/68079391/discord-py-info-command-how-to-mention-roles-of-a-member
        roles = " ".join([role.mention for role in member.roles if role.name != "@everyone"])
        embed.add_field(name="Roles:", value=f"{roles}", inline=False)
    embed.set_footer(text=FOOTER_EMBED)
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="aboutserver", description="displays information about the server")
async def aboutserver(ctx: commands.Context):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"About *{guild.name}* server",
        description="Information about this discord server",
        color=discord.Color.dark_blue(),
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

@bot.hybrid_command(name="aboutgame", description="displays information about repuls.io game")
async def aboutgame(ctx: commands.Context):
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
        color=discord.Color.blue(),
    )
    embed.add_field(name="Leaderboard", value=f"[Leaderboard]({REPULS_LINK}leaderboard)", inline=True)
    embed.add_field(name="Updates", value=f"[Updates]({REPULS_LINK}updates)", inline=True)
    embed.add_field(name="Terms & privacy", value=f"[Privacy]({REPULS_PRIVACY_LINK})", inline=True)
    embed.set_footer(text=FOOTER_EMBED)

    await ctx.send(embed=embed, view=play_btn_view)

@bot.hybrid_command(name="avatar", description="displays a member's avatar")
async def avatar(ctx: commands.Context, member: discord.Member):
    embed = discord.Embed(
        title=f"Avatar of {member.display_name}!",
        color=discord.Color.dark_blue(),
    )
    if member.avatar != None:
        embed.add_field(name="Legal warning", value="*Please don't use other members' images without their permission*", inline=False)
        embed.set_image(url=member.avatar.url)
        embed.set_footer(text=FOOTER_EMBED)
    else:
        embed.add_field(name="This user has no avatar", value="*nothing to display...*")
        embed.set_footer(text=FOOTER_EMBED)
    
    await ctx.send(embed=embed)

@bot.tree.command(name="clean", description="allows you to clean a certain number of messages in a channel")
@admin_or_roles()
async def clean(interaction: discord.Interaction, number: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=number)
    await interaction.followup.send(f"{CHECK} {len(deleted)} messages removed!", ephemeral=True)

# ---------------------------------- events
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    elif message.channel.id == VIDEO_CHANNEL:
        if re.search(YOUTUBE_REGEX, message.content):
            await message.add_reaction(REACTION_VALIDATION)
    
    await bot.process_commands(message)

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
        # print(error)
        pass # do nothing
    else:
        await ctx.send(f"{header}*Unknown error:* `{error}`{footer}")

@bot.event
async def on_ready():
    # sync of slash and hybrid commands
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} command(s) have been synchronized")
    except Exception as e:
        print(e)
        exit(1)
    
    status_channel = bot.get_channel(STATUS_CHANNEL)
    if status_channel != None:
        await status_channel.send(f"{bot.user.mention} is now **online**! <:connecte:{CONNECTE_EMOJI}>")
    
    game = discord.Game("repuls.io")
    await bot.change_presence(activity=game)

if __name__ == "__main__":
    bot.run(TOKEN)