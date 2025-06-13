import discord
from discord import app_commands
from discord.ext import commands
# bot files
from constants import *
from utils import check_admin_or_roles

class ServerCog(commands.Cog, name=SERVER_COG):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="What am I capable of? Run this command to find out!")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(
            title=f"{BOT_NAME}'s help command",
            description="Here are the available commands :",
            color=discord.Color.dark_blue()
        )

        for cmd in self.bot.tree.get_commands():
            # mention = f"</{cmd.name}:{cmd.id}> or {CMD_PREFIX}{cmd.name}" if cmd.id else f"!{cmd.name}"
            embed.add_field(name=f"`{BOT_PREFIX}{cmd.name}`", value=cmd.description or None, inline=False)

        embed.set_footer(text=FOOTER_EMBED)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ping", description="displays latency of the bot")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"{CHECK} **pong!**\n(*It took me {round(self.bot.latency * 1000, 2)}ms to respond to your command!*)")

    @app_commands.command(name="clean", description="Allows you to clean a certain number of messages in a channel")
    @check_admin_or_roles()
    async def clean(self, interaction: discord.Interaction, number: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=number)
        await interaction.followup.send(f"{CHECK} {len(deleted)} messages removed!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerCog(bot))