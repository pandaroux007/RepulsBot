import discord
from discord.ext import commands
import asqlite
from pathlib import Path
from datetime import (
    datetime,
    timedelta
)

# bot file
from data.constants import IDs

# ---------------------------------- permissions
_AUTHORISED_ROLES = {
    IDs.serverRoles.ADMIN,
    IDs.serverRoles.DEVELOPER
}

def is_member_admin(member: discord.Member) -> bool:
    user_role_ids = {role.id for role in member.roles}
    # https://www.w3schools.com/python/ref_set_intersection.asp
    return bool(user_role_ids & _AUTHORISED_ROLES) or member.guild_permissions.administrator

def check_admin_or_roles():
    async def predicate(ctx: commands.Context):
        return is_member_admin(ctx.author)
    return commands.check(predicate)

# ---------------------------------- formatting
def hoursdelta(hours) -> datetime:
    return discord.utils.utcnow() - timedelta(hours=hours)

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

# ---------------------------------- storage
class BaseStorage():
    def __init__(self):
        self._conn: asqlite.Connection | None = None

    async def init(self, path: Path) -> None:
        if self._conn is not None:
            return
        self._conn = await asqlite.connect(path)
        await self._conn.execute("PRAGMA journal_mode = WAL;") # https://sqlite.org/wal.html
        await self._conn.execute("PRAGMA busy_timeout = 5000;") # ms (https://sqlite.org/c3ref/busy_timeout.html)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def _check_init(self):
        if self._conn is None:
            await self.init()