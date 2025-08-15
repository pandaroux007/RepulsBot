"""
This cog contains all the commands accessible only to server admins

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
# bot files
from cogs_list import CogsNames
from constants import DefaultEmojis
from utils import (
    check_admin_or_roles,
    log, LogColor,
    IS_ADMIN
)

MAX_PURGE = 1000

# ---------------------------------- admin cog (see README.md)
class AdminCog(commands.Cog, name=CogsNames.ADMIN):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(description="Allows you to clean a certain number of messages", extras={IS_ADMIN: True})
    @app_commands.describe(number=f"Number of messages to delete (max {MAX_PURGE})")
    @check_admin_or_roles()
    async def purge(self, interaction: discord.Interaction, number: int):
        number = max(1, min(number, MAX_PURGE))
        await interaction.response.defer(ephemeral=True)

        total_deleted = 0
        while number > 0:
            to_delete = min(100, number)
            deleted = await interaction.channel.purge(limit=to_delete)
            total_deleted += len(deleted)
            number -= to_delete
            if number > 0:
                await asyncio.sleep(1)
        
        await log(
            bot=self.bot, color=LogColor.RED,
            title=f"🗑️ {total_deleted} messages removed in {interaction.channel.jump_url} by {interaction.user.mention}"
        )
        await interaction.edit_original_response(content=f"{DefaultEmojis.CHECK} {total_deleted} messages removed!")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))