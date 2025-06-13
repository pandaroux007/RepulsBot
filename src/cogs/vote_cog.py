from discord.ext import tasks, commands
from datetime import datetime, timedelta, timezone
# bot files
from constants import *
from utils import YouTubeLink

# https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
class VoteCog(commands.Cog, name=VOTE_COG):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_hidden_message(self, ctx: commands.Context, text: str):
        if ctx.interaction: # slash command
            await ctx.interaction.followup.send(text, ephemeral=True)
        else:
            await ctx.send(text, delete_after=10.0)
    
    # ---------------------------------- commands
    @commands.hybrid_command(name="addvideo", description="Post a new YouTube video (request for special roles)")
    @commands.has_any_role(YOUTUBER_ROLE_ID, STREAMER_ROLE_ID, ADMIN_ROLE_ID, DEVELOPER_ROLE_ID)
    async def addvideo(self, ctx: commands.Context, youtube_url: YouTubeLink):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        video_channel = self.bot.get_channel(VIDEO_CHANNEL_ID)
        if video_channel != None:
            # the link is already verified as a correct youtube link
            message = await video_channel.send(f"### New video posted by {ctx.author.mention}!\n{youtube_url}")
            await message.add_reaction(VALIDATION_UNICODE)
            await self.send_hidden_message(ctx=ctx, text=f"{CHECK} video posted in {video_channel.mention}!")
        else:
            await self.send_hidden_message(ctx=ctx, text=f"{ERROR} Unable to find video channel (whose ID is supposed to be {VIDEO_CHANNEL_ID}).\n**Ask an administrator for help!**")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(VoteCog(bot))