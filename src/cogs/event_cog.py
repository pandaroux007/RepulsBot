import discord
from discord.ext import commands
# bot files
from constants import *

class EventCog(commands.Cog, name=EVENT_COG):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        elif message.channel.id == VIDEO_CHANNEL_ID:
            if re.search(YOUTUBE_REGEX, message.content):
                await message.add_reaction(VALIDATION_UNICODE)
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        message = f"*Unknown error:* {error}" # default

        if isinstance(error, commands.CheckFailure):
            message = f"*You do not have permission to use this command!*"
        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"*Missing argument!*{ASK_HELP}"
        elif isinstance(error, commands.CommandNotFound):
            return # do nothing

        embed = discord.Embed(
            title=f"{ERROR} Check failure!",
            color=discord.Color.brand_red(),
            description=f"{message}{ASK_HELP}"
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        # sync of slash and hybrid commands
        synced = await self.bot.tree.sync()
        print(f"{len(synced)} command(s) have been synchronized")
        
        status_channel = self.bot.get_channel(STATUS_CHANNEL_ID)
        if status_channel != None:
            await status_channel.send(f"{self.bot.user.mention} is now **online**! {await self.bot.fetch_application_emoji(CONNECTE_EMOJI_ID)}")
        
        game = discord.Game("🎮️ repuls.io browser game! 🕹️")
        await self.bot.change_presence(activity=game)

async def setup(bot: commands.Bot):
    await bot.add_cog(EventCog(bot))