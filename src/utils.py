import discord
from discord.ext import commands
from datetime import datetime, timedelta
# bot file
from constants import AUTHORISED_ROLES

def is_admin(member: discord.Member) -> bool:
    user_role_ids = {role.id for role in member.roles}
    # https://www.w3schools.com/python/ref_set_intersection.asp
    return bool(user_role_ids & AUTHORISED_ROLES) or member.guild_permissions.administrator

def check_admin_or_roles():
    async def predicate(ctx: commands.Context):
        return is_admin(ctx.author)
    return commands.check(predicate)

ADMIN_CMD = "admin_only"

def hoursdelta(hours) -> datetime:
    return discord.utils.utcnow() - timedelta(hours=hours)

def nl(string: str) -> str:
    """ returns a string without line breaks """
    string = string.replace("\n\n", "<<DOUBLE_NEWLINE>>")
    string = string.replace('\n', ' ')
    return string.replace("<<DOUBLE_NEWLINE>>", "\n\n").strip()

def plurial(size: int):
    if type(size) is not int:
        size = len(size)
    return "s" if size > 1 else ''

def possessive(word: str) -> str:
    return f"{word}{'\'' if word.endswith('s') else "'s"}"

def get_leaderboard_header(index: int, additional_condition: int = 0, length: int = 2) -> str:
    if additional_condition <= 1:
        if index == 1:
            return "🥇"
        elif index == 2:
            return "🥈"
        elif index == 3:
            return "🥉"
    return f"{str(index).zfill(length)}."