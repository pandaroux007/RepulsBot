import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional
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

IS_ADMIN = "admin_only"

def hoursdelta(hours) -> datetime:
    return discord.utils.utcnow() - timedelta(hours=hours)

def nl(string: str) -> str:
    """ returns a string without line breaks """
    return string.replace('\n', ' ').strip()

def gettimestamp(time: datetime, format: Optional[str] = "F"):
    """ returns a discord markdown timestamp """
    return f"<t:{int(time.timestamp())}{f":{format}" if format else ""}>"

# ---------------------------------- log system
class LogColor:
    BLUE = discord.Color.blue()
    RED = discord.Color.red()
    GREEN = discord.Color.green()

MODLOG = True
BOTLOG = False

async def log(bot: commands.Bot, title: str, msg: str = "", type: bool = MODLOG, color: LogColor = LogColor.BLUE) -> discord.Message | None:
    log_channel = bot.get_channel(IDs.serverChannel.BOTLOG if type == BOTLOG else IDs.serverChannel.MODLOG)
    if log_channel is not None:
        log_embed = discord.Embed(
            description=f"**{title}**\n{msg}",
            color=color,
            timestamp=discord.utils.utcnow()
        )
        log_msg = await log_channel.send(embed=log_embed, silent=True, allowed_mentions=discord.AllowedMentions.none())
        return log_msg
    return None