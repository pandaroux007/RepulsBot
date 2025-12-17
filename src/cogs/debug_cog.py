"""
This cog allows the bot maintainers to obtain certain information
and to fix potential bugs remotely.

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

from __future__ import annotations
import discord
from discord.ext import commands
import psutil
import os
import platform
import time
# bot files
from cogs_list import CogsNames
from constants import (
    BotInfo,
    DefaultEmojis
)

# ---------------------------------- users cog (see README.md)
class DebugCog(commands.Cog, name=CogsNames.DEBUG):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(description="Information about the server hosting the bot")
    @commands.is_owner()
    async def debug_info(self, ctx: commands.Context):
        """
        Useful links for contributing
        - https://stackoverflow.com/questions/3103178/how-to-get-the-system-info-with-python
        - https://www.quora.com/What-is-1e9-in-programming
        - https://stackoverflow.com/questions/2598145/how-to-retrieve-the-process-start-time-or-uptime-in-python
        - https://github.com/giampaolo/psutil
        """
        await ctx.message.delete()
        embed = discord.Embed(
            title="Information about the bot's hosting server",
            color=discord.Color.dark_gray(),
            timestamp=discord.utils.utcnow()
        )

        bot_process = psutil.Process(os.getpid())
        bot_ram_used = round((bot_process.memory_info().rss / (1024 * 1024)), 2)
        bot_cpu_used = bot_process.cpu_percent(interval=0.1)
        bot_uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(bot_process.create_time()))

        embed.add_field(inline=False, name="Resource usage by the bot", value=(
            f"RAM: {round(bot_ram_used, 2)}MB\n"
            f"CPU: {bot_cpu_used}%\n"
            f"Up time: since {bot_uptime}"
        ))

        global_cpu_used = psutil.cpu_percent(interval=1)
        global_ram = psutil.virtual_memory()
        global_disk = psutil.disk_usage('/')
        global_uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time()))

        embed.add_field(inline=False, name="Resources used globally on the system", value=(
            f"CPU: {global_cpu_used}%\n"
            f"RAM: {global_ram.percent}% ({round(global_ram.used / 1e9, 2)}GB / {round(global_ram.total / 1e9, 2)}GB)\n"
            f"Disk: {global_disk.percent}% ({round(global_disk.used / 1e9, 2)}GB / {round(global_disk.total / 1e9, 2)}GB)\n"
            f"Boot time: since {global_uptime}"
        ))

        embed.add_field(inline=False, name="System software specifications", value=(
            f"{self.bot.user.display_name}: **v{BotInfo.VERSION}**\n"
            f"discord.py: **v{discord.__version__}**\n"
            f"python3: **v{platform.python_version()}**"
        ))

        embed.add_field(inline=False, name="Information about the server's OS", value=f"OS: `{platform.platform(aliased=True)}`")
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
        try:
            await ctx.author.send(embed=embed)
            await ctx.send(f"{DefaultEmojis.CHECK} The debug report has been sent!", delete_after=5)
        except Exception as error:
            raise discord.DiscordException(str(error))

async def setup(bot: commands.Bot):
    await bot.add_cog(DebugCog(bot))