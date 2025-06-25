import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta, timezone
# bot files
from constants import *
from utils import (
    YouTubeLink,
    send_hidden_message,
    send_video_to_endpoint,
    SUCCESS_CODE
)

# https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
class VoteCog(commands.Cog, name=VOTE_COG):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.vote_task.start()

    def cog_unload(self):
        self.vote_task.cancel()

    @tasks.loop(hours=VOTE_HOURS)
    async def vote_task(self):
        await self.check_better_video()

    @vote_task.before_loop
    async def before_vote_task(self):
        await self.bot.wait_until_ready()

    async def check_better_video(self):
        self.video_channel = self.bot.get_channel(VIDEO_CHANNEL_ID)
        if not self.video_channel: return

        limit_time = datetime.now(timezone.utc) - timedelta(hours=VOTE_HOURS)
        better_video_msg = None
        last_better_votes = 0

        async for message in self.video_channel.history(limit=50, after=limit_time):
            if not re.search(YOUTUBE_REGEX, message.content):
                continue
            for reaction in message.reactions:
                if str(reaction.emoji) == VALIDATION_UNICODE:
                    count = reaction.count
                    
                    if count > last_better_votes:
                        last_better_votes = count
                        better_video_msg = message
                    break

            await self.process_winner(msg=better_video_msg, vote_count=last_better_votes)

    async def process_winner(self, msg: discord.Message, vote_count: int):
        if msg and vote_count > 0:
            embed = discord.Embed(
                title=f"New featured video! 🎉",
                color=discord.Color.dark_blue(),
                timestamp=datetime.now(timezone.utc),
                description=FEATURED_VIDEO_MSG.format(reaction=CHECK, time=VOTE_HOURS).replace('\n', ' ').strip()
            )
            embed.add_field(name="Watch it now!", value=msg.jump_url)

            match = re.search(YOUTUBE_REGEX, msg.content)
            code = await send_video_to_endpoint(video_url=match.group(0))
            if code == SUCCESS_CODE:
                embed.add_field(name="Website state", value=f"{await self.bot.fetch_application_emoji(CONNECTE_EMOJI_ID)} Video sent to [repuls.io]({REPULS_LINK})!")
            else:
                embed.add_field(name="Website state", value=f"{WARN} Video failed to send to repuls.io ({code} error)!")

            await self.video_channel.send(embed=embed)
        else:
            await self.video_channel.send(f"I couldn't find any videos to display on the game's homepage 🫤...\n**<@&{YOUTUBER_ROLE_ID}>, it's your turns!** 💪")
    
    # ---------------------------------- commands
    @commands.hybrid_command(name="addvideo", description="Post a new YouTube video (request for special roles)")
    @commands.has_any_role(YOUTUBER_ROLE_ID, STREAMER_ROLE_ID, ADMIN_ROLE_ID, DEVELOPER_ROLE_ID)
    async def addvideo(self, ctx: commands.Context, youtube_url: YouTubeLink):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        video_channel = self.bot.get_channel(VIDEO_CHANNEL_ID)
        if video_channel != None:
            # the link is already verified as a correct youtube link
            await video_channel.send(f"### 📢 New YouTube video! 🎉\n{youtube_url}\n(*Posted by {ctx.author.mention}!*)")
            await send_hidden_message(ctx=ctx, text=f"{CHECK} video posted in {video_channel.mention}!")
        else:
            await send_hidden_message(ctx=ctx, text=f"{ERROR} Unable to find video channel (whose ID is supposed to be {VIDEO_CHANNEL_ID})!{ASK_HELP}")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(VoteCog(bot))