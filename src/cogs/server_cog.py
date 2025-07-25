import discord
from discord import app_commands
from discord.ext import commands
# bot files
from utils import check_admin_or_roles
from cogs.cogs_info import CogsNames
from constants import (
    BotInfo,
    DefaultEmojis,
    CMD_PREFIX,
    FOOTER_EMBED
)

from faq_data import (
    ServerFAQ,
    GameFAQ
)

# ---------------------------------- faq selector
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=select#discord.ui.Select
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=view#discord.ui.View
class FAQView(discord.ui.View):
    def __init__(self, faq_entries, custom_id):
        super().__init__(timeout=None)
        self.faq_entries = faq_entries
        options = [
            discord.SelectOption(label=entry["question"], value=str(idx))
            for idx, entry in enumerate(faq_entries)
        ]
        self.add_item(FAQSelect(options, faq_entries, custom_id))

class FAQSelect(discord.ui.Select):
    def __init__(self, options, faq_entries, custom_id):
        super().__init__(placeholder="Choose a question...", options=options, custom_id=custom_id)
        self.faq_entries = faq_entries

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        entry = self.faq_entries[idx]
        embed = discord.Embed(
            title=entry["question"],
            description=entry["answer"],
            color=discord.Color.dark_blue()
        )
        await interaction.response.edit_message(embed=embed, view=self.view)

# ---------------------------------- server cog (see README.md)
class ServerCog(commands.Cog, name=CogsNames.SERVER):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------------------------- members' commands
    @commands.hybrid_command(name="ping", description="Displays latency of the bot")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"{DefaultEmojis.CHECK} **pong!**\n(*It took me {round(self.bot.latency * 1000, 2)}ms to respond to your command!*)")

    @commands.hybrid_command(name="help", description="What am I capable of? Run this command to find out!")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(
            title=f"{BotInfo.NAME}'s help command",
            description="Here are the available commands :",
            color=discord.Color.dark_blue()
        )

        for cmd in self.bot.tree.get_commands():
            # mention = f"</{cmd.name}:{cmd.id}> or {CMD_PREFIX}{cmd.name}" if cmd.id else f"!{cmd.name}"
            embed.add_field(name=f"`{CMD_PREFIX}{cmd.name}`", value=cmd.description or None, inline=False)

        embed.set_footer(text=FOOTER_EMBED)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverfaq", description="Launch the server's interactive FAQ")
    async def serverfaq(self, ctx: commands.Context):
        embed = discord.Embed(
            title=f"{ctx.guild.name}{"\'" if ctx.guild.name.endswith('s') else "'s"} server FAQ",
            description="👉️ Select a question from the drop-down menu below!",
            color=discord.Color.blue()
        )
        view = FAQView(ServerFAQ.get_data(), custom_id=ServerFAQ.get_id())
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="gamefaq", description="Frequently Asked Questions about the repuls.io game")
    async def gamefaq(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Repuls.io game FAQ",
            description="👉️ Select a question from the drop-down menu below!",
            color=discord.Color.blue()
        )
        view = FAQView(GameFAQ.get_data(), custom_id=GameFAQ.get_id())
        await ctx.send(embed=embed, view=view)
    
    # ---------------------------------- admin command
    @app_commands.command(name="clean", description="Allows you to clean a certain number of messages (request admin role)")
    @check_admin_or_roles()
    async def clean(self, interaction: discord.Interaction, number: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=number)
        await interaction.followup.send(f"{DefaultEmojis.CHECK} {len(deleted)} messages removed!", ephemeral=True)

async def setup(bot: commands.Bot):
    # https://github.com/Rapptz/discord.py/blob/master/examples/views/persistent.py
    bot.add_view(FAQView(ServerFAQ.get_data(), custom_id=ServerFAQ.get_id()))
    bot.add_view(FAQView(GameFAQ.get_data(), custom_id=GameFAQ.get_id()))

    await bot.add_cog(ServerCog(bot))