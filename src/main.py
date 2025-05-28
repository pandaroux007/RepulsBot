import discord
from discord.ext import commands
# IDs and TOKEN file
from private_data import *

CHECK = ":white_check_mark:"
ERROR = ":x:"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

def admin_or_roles():
    async def predicate(ctx: commands.Context):
        has_admin = ctx.author.guild_permissions.administrator
        has_role = any(role.name in ["Admin", "Moderator"] for role in ctx.author.roles)
        return has_admin or has_role
    return commands.check(predicate)

# ---------------------------------- commands
@bot.hybrid_command(name="ping")
async def ping(ctx: commands.Context):
    await ctx.send(f"{CHECK} **pong!**\n(*It took me {round(bot.latency * 1000, 2)}ms to respond to your command!*)")

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