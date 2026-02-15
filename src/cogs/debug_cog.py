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
from pathlib import Path
import asyncio
import math
# bot files
from tools.utils import check_if_maintainer
from data.cogs import (
    CogsNames,
    COGS_LIST
)

from data.constants import (
    BotInfo,
    DefaultEmojis,
    IDs,
    DB_PATH
)

from tools.log_builder import (
    LogBuilder,
    LogColor,
    MODLOG
)

# https://www.reddit.com/r/learnpython/comments/ukidl7/what_is_typingtype_checking_for/
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

async def get_commit():
    # https://stackoverflow.com/questions/14989858/get-the-current-git-hash-in-a-python-script
    # https://stackoverflow.com/questions/70119286/how-do-i-write-an-async-version-of-subprocess-check-output
    current_path = Path(__file__).parent
    process = await asyncio.create_subprocess_exec(
        'git', 'rev-parse', '--short', 'HEAD',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=current_path,
    )
    stdout_data, stderr_data = await process.communicate()
    if process.returncode == 0:
        return stdout_data.decode('ascii').strip()

def format_size(size_bytes, decimals=2):
    # https://www.digitalocean.com/community/tutorials/how-to-get-file-size-in-python#human-readable-size-conversion-function-bytes-kb-mb-gb
    if size_bytes == 0:
        return "0 Octet"

    power = 1024
    units = ["o", "Ko", "Mo", "Go", "To"]
    i = int(math.floor(math.log(size_bytes, power)))
    return f"{size_bytes / (power ** i):.{decimals}f} {units[i]}"

class DebugCog(commands.Cog, name=CogsNames.DEBUG):
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot

    # ---------------------------------- purely informative commands
    @commands.command(description="[DEBUG] Information about the server hosting the bot")
    @commands.guild_only()
    @check_if_maintainer()
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
            title=f"{DefaultEmojis.INFO} Information about the bot's hosting server",
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

        try:
            file_size = DB_PATH.stat().st_size
            embed.add_field(inline=False, name="Database weight", value=format_size(file_size))
        except Exception:
            pass

        current_commit = await get_commit()

        embed.add_field(inline=False, name="System software specifications", value=(
            f"{self.bot.user.display_name}: **v{BotInfo.VERSION}**\n"
            f"discord.py: **v{discord.__version__}**\n"
            f"python3: **v{platform.python_version()}**\n"
            f"git commit: ***[`{current_commit}`]({BotInfo.GITHUB}/commit/{current_commit})***" if current_commit else ''
        ))

        embed.add_field(inline=False, name="Information about the server's OS", value=f"OS: `{platform.platform(aliased=True)}`")
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
        try:
            await ctx.author.send(embed=embed)
            await ctx.send(f"{DefaultEmojis.CHECK} The debug report has been sent!", delete_after=5)
        except Exception as error:
            raise discord.DiscordException(str(error))

    # ---------------------------------- potentially risky commands.
    @commands.command(description="[DEBUG] Restart a cog via its name")
    @commands.guild_only()
    @check_if_maintainer()
    async def restart_cog(self, ctx: commands.Context, name: str):
        await ctx.message.delete()
        embed = discord.Embed(
            title=f"Restart the '{name}' cog",
            color=discord.Color.dark_gray(),
            timestamp=discord.utils.utcnow()
        )
        if name not in COGS_LIST:
            embed.description = f"{DefaultEmojis.WARN} This cog doesn't exist in the list!"
            await ctx.send(embed=embed, delete_after=5)
        else:
            try:
                await self.bot.reload_extension(name=f"cogs.{name}")
                embed.description = f"{DefaultEmojis.CHECK} Cog `{name}` successfully restarted!"
                await (
                    LogBuilder(self.bot, type=MODLOG, color=LogColor.RED)
                    .enable_ping()
                    .title(f"{DefaultEmojis.INFO} CRITICAL INFO - A cog has been restarted!")
                    .description(f"<@{IDs.repulsTeam.MAIN_DEVELOPER}>, `{name}` has been restarted by {ctx.author.mention}")
                    .send()
                )
            except Exception as e:
                embed.description = f"{DefaultEmojis.ERROR} An error occurred during the restart attempt!\n```\n{e}\n```"
            
            await ctx.author.send(embed=embed)

    @commands.command(description="[DEBUG] Reset the tickets storage in database")
    @commands.guild_only()
    @check_if_maintainer()
    async def reset_tickets_storage(self, ctx: commands.Context):
        await ctx.message.delete()
        try:
            await self.bot.tickets_storage.reset_table()

            embed = discord.Embed(
                title="Reset tickets storage in database",
                description=f"{DefaultEmojis.CHECK} Tickets storage reset!",
                color=discord.Color.dark_gray(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.author.send(embed=embed)
            await (
                LogBuilder(self.bot, type=MODLOG, color=LogColor.RED)
                .enable_ping()
                .title(f"{DefaultEmojis.INFO} CRITICAL INFO - Tickets storage in the database reset!")
                .description(f"<@{IDs.repulsTeam.MAIN_DEVELOPER}>, the tickets storage was reset by {ctx.author.mention}")
                .send()
            )
        except Exception as error:
            raise discord.DiscordException(str(error))

    @commands.command(description="[DEBUG] Reset the youtube storage in database")
    @commands.guild_only()
    @check_if_maintainer()
    async def reset_youtube_storage(self, ctx: commands.Context):
        await ctx.message.delete()
        try:
            await self.bot.youtube_storage.reset_table()

            embed = discord.Embed(
                title="Reset youtube storage in database",
                description=f"{DefaultEmojis.CHECK} Tickets storage reset!",
                color=discord.Color.dark_gray(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.author.send(embed=embed)
            await (
                LogBuilder(self.bot, type=MODLOG, color=LogColor.RED)
                .enable_ping()
                .title(f"{DefaultEmojis.INFO} CRITICAL INFO - YouTube storage in the database reset!")
                .description(f"<@{IDs.repulsTeam.MAIN_DEVELOPER}>, the youtube storage was reset by {ctx.author.mention}")
                .send()
            )
        except Exception as error:
            raise discord.DiscordException(str(error))

    # ---------------------------------- potentially destructive commands
    @commands.command(description="[DEBUG] Destroys and then recreates the database")
    @commands.guild_only()
    @check_if_maintainer()
    async def reinit_storage(self, ctx: commands.Context):
        await ctx.message.delete()
        try:
            if self.bot.db_pool is not None:
                await self.bot.db_pool.close()

            DB_PATH.unlink()
            await self.bot.setup_database()

            embed = discord.Embed(
                title="Recreating the database",
                description=f"{DefaultEmojis.CHECK} Database deleted and then recreated!",
                color=discord.Color.dark_gray(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.author.send(embed=embed)
            await (
                LogBuilder(self.bot, type=MODLOG, color=LogColor.RED)
                .enable_ping()
                .title(f"{DefaultEmojis.INFO} CRITICAL INFO - The entire database has been reset!")
                .description(f"<@{IDs.repulsTeam.MAIN_DEVELOPER}>, the bot's database was reset by {ctx.author.mention}")
                .send()
            )
        except Exception as error:
            raise discord.DiscordException(str(error))

async def setup(bot: "RepulsBot"):
    await bot.add_cog(DebugCog(bot))