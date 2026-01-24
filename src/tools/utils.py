import discord
from discord.ext import commands
from datetime import (
    datetime,
    timedelta
)

# bot file
from data.constants import IDs

# ---------------------------------- permissions
_MAINTAINER_MEMBERS = {
    IDs.repulsTeam.BOT_DEVELOPER,
    IDs.repulsTeam.MAIN_DEVELOPER
}

_AUTHORIZED_ROLES = {
    IDs.serverRoles.ADMIN,
    IDs.serverRoles.DEVELOPER
}

def check_if_maintainer():
    async def predicate(ctx: commands.Context):
        is_authorized_member = ctx.author.id in _MAINTAINER_MEMBERS
        # ---------------------------------- check roles
        # https://www.w3schools.com/python/ref_set_intersection.asp
        _user_role_ids = {role.id for role in ctx.author.roles}
        is_admin_member = bool(_user_role_ids & _AUTHORIZED_ROLES) or ctx.author.guild_permissions.administrator
        return (is_authorized_member or is_admin_member)
    return commands.check(predicate)

# ---------------------------------- formatting
def daysdelta(days: int | float) -> datetime:
    return discord.utils.utcnow() - timedelta(days=days)

def nl(string: str) -> str:
    """ returns a string without line breaks """
    string = string.replace("\n\n", "<<DOUBLE_NEWLINE>>")
    string = string.replace('\n', ' ')
    return string.replace("<<DOUBLE_NEWLINE>>", "\n\n").strip()

def plurial(word: str, size: int):
    if type(size) is not int:
        size = len(size)
    word += "s" if size > 1 else ''
    return word

def possessive(word: str) -> str:
    return f"{word}{'\'' if word.endswith('s') else "'s"}"