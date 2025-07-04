import discord
from discord.ext import commands
# bot file
from constants import (
    CogsNames,
    IDs,
    ASK_HELP
)

# ---------------------------------- event cog (see README.md)
class EventCog(commands.Cog, name=CogsNames.EVENT):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        elif message.channel.id == IDs.serverChannel.RULES:
            await message.channel.send(message.content)
            await message.delete()
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        message = f"*Unknown error:* {error}" # default

        if isinstance(error, commands.CheckFailure):
            message = "*You do not have permission to use this command!*"
        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"*Missing argument!*{ASK_HELP}"
        elif isinstance(error, commands.CommandNotFound):
            return # do nothing

        embed = discord.Embed(
            title=f"{await self.bot.fetch_application_emoji(IDs.customEmojis.DECONNECTE)} Check failure!",
            color=discord.Color.brand_red(),
            description=f"{message}{ASK_HELP}"
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        # sync of slash and hybrid commands
        synced = await self.bot.tree.sync()
        print(f"{len(synced)} command(s) have been synchronized")
        
        status_channel = self.bot.get_channel(IDs.serverChannel.STATUS)
        if status_channel is not None:
            await status_channel.send(f"{self.bot.user.mention} is now **online**! {await self.bot.fetch_application_emoji(IDs.customEmojis.CONNECTE)}")
        
        game = discord.Game("🎮️ repuls.io browser game! 🕹️")
        await self.bot.change_presence(activity=game)

async def setup(bot: commands.Bot):
    await bot.add_cog(EventCog(bot))