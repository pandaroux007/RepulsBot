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
        
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        header = f"{ERROR} **Check failure**!\n"
        footer = f"\n**Ask an administrator for help!**"

        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"{header}*You do not have permission to use this command!*{footer}")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{header}*Missing argument!*{footer}")
        elif isinstance(error, commands.CommandNotFound):
            # print(error)
            pass # do nothing
        else:
            await ctx.send(f"{header}*Unknown error:* {error}{footer}")

    @commands.Cog.listener()
    async def on_ready(self):
        # sync of slash and hybrid commands
        try:
            synced = await self.bot.tree.sync()
            print(f"{len(synced)} command(s) have been synchronized")
        except Exception as e:
            print(e)
            exit(1)
        
        status_channel = self.bot.get_channel(STATUS_CHANNEL_ID)
        if status_channel != None:
            await status_channel.send(f"{self.bot.user.mention} is now **online**! {await self.bot.fetch_application_emoji(CONNECTE_EMOJI_ID)}")
        
        game = discord.Game("🎮️ repuls.io browser game! 🕹️")
        await self.bot.change_presence(activity=game)

async def setup(bot: commands.Bot):
    await bot.add_cog(EventCog(bot))