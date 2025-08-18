import discord
from discord.ext import commands
from datetime import datetime, timedelta
# bot file
from constants import AUTHORISED_ROLES

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

def plurial(size: int):
    return "s" if len(size) > 1 else ''

def possessive(word: str) -> str:
    return f"{word}{'\'' if word.endswith('s') else "'s"}"