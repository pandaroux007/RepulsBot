"""
This cog contains all the commands accessible only to server admins

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

from discord.ext import commands
# bot files
from utils import check_admin_or_roles
from cogs_list import CogsNames
from constants import DefaultEmojis

# ---------------------------------- server cog (see README.md)
class AdminCog(commands.Cog, name=CogsNames.ADMIN):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="clean", description="Allows you to clean a certain number of messages")
    @check_admin_or_roles()
    async def clean(self, ctx: commands.Context, number: int):
        deleted = await ctx.channel.purge(limit=number+1)
        await ctx.send(f"{DefaultEmojis.CHECK} {len(deleted)} messages removed!")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))