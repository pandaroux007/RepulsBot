import discord
from discord.ext import commands
from datetime import datetime, timedelta
# bot file
from constants import (
    IDs,
    AUTHORISED_ROLES
)

def check_admin_or_roles():
    async def predicate(ctx: commands.Context):
        is_admin = ctx.author.guild_permissions.administrator
        has_role = any(role.id in AUTHORISED_ROLES for role in ctx.author.roles)
        return is_admin or has_role
    return commands.check(predicate)

def hoursdelta(hours) -> datetime:
    return discord.utils.utcnow() - timedelta(hours=hours)

def nl(string: str) -> str:
    """ returns a string without line breaks """
    return string.replace('\n', ' ').strip()

# ---------------------------------- log system
class LogColor:
    DEFAULT = discord.Color.blue()
    LEAVE = discord.Color.red()
    CREATE = discord.Color.green()
    DELETE = discord.Color.red()

MODLOG = True
BOTLOG = False

async def log(bot: commands.Bot, title: str, msg: str = "", type: bool = MODLOG, color: LogColor = LogColor.DEFAULT):
    log_channel = bot.get_channel(IDs.serverChannel.BOTLOG if type == BOTLOG else IDs.serverChannel.MODLOG)
    if log_channel is not None:
        log_embed = discord.Embed(
            description=f"**{title}**\n{msg}",
            color=color,
            timestamp=discord.utils.utcnow()
        )
        await log_channel.send(embed=log_embed, silent=True, allowed_mentions=discord.AllowedMentions.none())