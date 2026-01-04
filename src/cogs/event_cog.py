"""
Below is the command error handling, bot startup and other discord events

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
# bot files
from data.cogs import CogsNames
from tools.log_builder import (
    LogColor,
    BOTLOG,
    log
)

from data.constants import (
    IDs,
    DefaultEmojis,
    ASK_HELP,
    AUTHORISED_SERVERS
)

class EventCog(commands.Cog, name=CogsNames.EVENT):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------------------------- error handling
    def cog_load(self):
        tree = self.bot.tree
        self._old_tree_error = tree.on_error # optional
        tree.on_error = self.on_app_command_error

    def cog_unload(self):
        tree = self.bot.tree
        tree.on_error = self._old_tree_error

    async def handle_command_error(self, source: commands.Context | discord.Interaction, error: discord.DiscordException):
        message = f"*Unknown error:* {error}" # default

        if isinstance(error, commands.CommandNotFound):
            return # do nothing
        elif isinstance(error, (commands.CheckFailure, app_commands.errors.CheckFailure)):
            message = "You do not have permission to use this command!"
        elif isinstance(error, commands.NotOwner):
            message = "Only the bot maintainer can use this command!"
        elif isinstance(error, commands.MissingRequiredArgument):
            message = "Missing argument!"
        else:
            author = source.author.mention if isinstance(source, commands.Context) else source.user.mention
            await log(
                bot=self.bot, type=BOTLOG, color=LogColor.RED,
                title=f"{DefaultEmojis.ERROR} User {author} tried to use the `{source.command.name}` command",
                msg=f"It failed with the error:\n```\n{error}\n```"
            )

        embed = discord.Embed(
            title=f"{DefaultEmojis.ERROR} Oh! We're sorry, but something went wrong...",
            description=f"> {message}{ASK_HELP}",
            color=discord.Color.brand_red()
        )
        if isinstance(source, commands.Context):
            embed.set_footer(text="This message will disappear in 20 seconds")
            await source.send(embed=embed, delete_after=20)
        elif isinstance(source, discord.Interaction):
            if source.response.is_done():
                await source.followup.send(embed=embed, ephemeral=True)
            else:
                await source.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await self.handle_command_error(ctx, error)

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await self.handle_command_error(interaction, error)

    # ---------------------------------- bot operation
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if guild.id not in AUTHORISED_SERVERS:
            await guild.leave()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        elif message.channel.id == IDs.serverChannel.RULES:
            await message.channel.send(message.content)
            await message.delete()

    @commands.Cog.listener()
    async def on_ready(self):
        game = discord.Game("🎮️ repuls.io browser game! 🕹️")
        await self.bot.change_presence(activity=game)
        await log(bot=self.bot, type=BOTLOG, title=f"{self.bot.user.mention} is now online! {DefaultEmojis.ONLINE}")

    # ---------------------------------- welcome message
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        welcome_channel = self.bot.get_channel(IDs.serverChannel.WELCOME)
        rules_channel = self.bot.get_channel(IDs.serverChannel.RULES)
        await welcome_channel.send(f"Welcome {member.mention}! Please read {rules_channel.jump_url}, then have fun!")

async def setup(bot: commands.Bot):
    await bot.add_cog(EventCog(bot))