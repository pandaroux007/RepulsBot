from discord.ext import tasks, commands
from datetime import datetime, timedelta, timezone
# bot files
from constants import *
from utils import YouTubeLink

# https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
class VoteCog(commands.Cog, name=VOTE_COG):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    # ---------------------------------- commands
    @commands.hybrid_command(name="addvideo", description="Post a new YouTube video (request for special roles)")
    @commands.has_any_role(YOUTUBER_ROLE_ID, STREAMER_ROLE_ID, ADMIN_ROLE_ID, DEVELOPER_ROLE_ID)
    async def addvideo(self, ctx: commands.Context, youtube_url: YouTubeLink):
        if ctx.channel.id == VIDEO_CHANNEL_ID:
            # the link is already verified as a correct youtube link
            message = await ctx.send(f"### New video posted by {ctx.author.mention}!\n{youtube_url}")
            await message.add_reaction(VALIDATION_UNICODE)
        else:
            error_msg = f"{ERROR} This command is only available in [the video-specific channel]({DISCORD_YOUTUBE_CHANNEL_LINK}).\n**Go there and try again.**"
            if ctx.interaction is not None: # slash command
                await ctx.send(error_msg, ephemeral=True)
            else:
                await ctx.send(error_msg, silent=True, delete_after=10.0)
            return

async def setup(bot: commands.Bot):
    await bot.add_cog(VoteCog(bot))