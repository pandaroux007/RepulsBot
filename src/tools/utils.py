from __future__ import annotations
from discord.ext import commands
from enum import Enum
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

def number(n: str) -> str:
    # https://leancrew.com/all-this/2020/06/ordinals-in-python/
    return str(n) + {1: "st", 2: "nd", 3: "rd"}.get(4 if 10 <= n % 100 < 20 else n % 10, "th")

class GamePlaylist(Enum):
    """
    Chap. 8.13.8: https://docs.python.org/3.5/library/enum.html#allowed-members-and-attributes-of-enumerations
    Example (8.13.13.4): https://docs.python.org/3.5/library/enum.html#planet
    """
    WARFARE = ("wf", "Warfare", "Team play and vehicle based maps")
    HARDCORE = ("hc", "Hardcore", "Arena maps, no vehicles")
    CASUAL = ("ws", "Casual", "Crasy modes focused on fun")
    CUSTOMS = ("cm", "Customs", "User created modes")

    def __init__(self, code: str, label: str, desc: str):
        self.code: str = code
        self.label: str = label
        self.description: str = desc

    def __str__(self):
        return self.label
    
    def __repr__(self):
        return super().__repr__()

    @classmethod
    def from_code(cls, code: str) -> GamePlaylist | None:
        code = code.lower()
        for pl in cls:
            if pl.code == code:
                return pl
        return None