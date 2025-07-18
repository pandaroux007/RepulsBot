import discord
from discord.ext import tasks, commands
import re
import aiohttp
# bot files
from utils import (
    send_hidden_message,
    hoursdelta
)

from cogs.cogs_info import CogsNames
from constants import (
    DefaultEmojis,
    Links,
    PrivateData,
    IDs,
    ASK_HELP,
    ENV,
    ENV_DEV_MODE
)

# regex for youtube links
# https://stackoverflow.com/questions/19377262/regex-for-youtube-url
YOUTUBE_REGEX = re.compile(
    r'((?:https?:)?\/\/(?:www\.|m\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be)\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?[\w\-]+(?:\S+)?)',
    re.IGNORECASE
)

VOTE_HOURS = 168 # hours (so one week)
SUCCESS_CODE = 200

FEATURED_VIDEO_MSG = """
(And you, do you want your video to appear on the game's main page? Then hurry up and post the link here,
and cross your fingers that the community votes for your message with the reaction {reaction} just below!
***I come and check the best video every {time} hours, you have every chance!***)
"""

class YouTubeLink(commands.Converter):
    async def convert(self, ctx: commands.Context, argument):
        if not re.match(YOUTUBE_REGEX, argument):
            raise commands.BadArgument("Your YouTube link is invalid. Please try again.")
        return argument

# https://apidog.com/blog/aiohttp-request/
# https://docs.aiohttp.org/en/stable/client_quickstart.html
async def send_video_to_endpoint(video_url: str):
    payload = {"video_url": video_url}
    headers = {
        "Authorization": f"Bearer {PrivateData.API_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(PrivateData.API_ENDPOINT_URL, json=payload, headers=headers) as resp:
                return resp.status
    except Exception:
        return "unknown"

# ---------------------------------- vote cog (see README.md)
# https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
class VoteCog(commands.Cog, name=CogsNames.VOTE):
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
        video_channel = self.bot.get_channel(IDs.serverChannel.VIDEO)
        if not video_channel:
            return

        better_video_msg = None
        last_better_votes = 0

        async for message in video_channel.history(limit=50, after=hoursdelta(VOTE_HOURS)):
            if not re.search(YOUTUBE_REGEX, message.content):
                continue # pass all messages without youtube links
            
            # update message cache (https://github.com/Rapptz/discord.py/issues/861)
            msg = await video_channel.fetch_message(message.id)
            for reaction in msg.reactions:
                if str(reaction.emoji) == DefaultEmojis.CHECK:
                    vote = reaction.count
                    if vote > last_better_votes:
                        last_better_votes = vote
                        better_video_msg = msg
                    break

        await self.process_winner(video_channel=video_channel, msg=better_video_msg, vote_count=last_better_votes)

    async def process_winner(self, video_channel: discord.TextChannel, msg: discord.Message, vote_count: int):
        if msg and vote_count > 0:
            embed = discord.Embed(
                title="New featured video! 🎉",
                color=discord.Color.dark_blue(),
                timestamp=discord.utils.utcnow(),
                description=FEATURED_VIDEO_MSG.format(reaction=DefaultEmojis.CHECK, time=VOTE_HOURS).replace('\n', ' ').strip()
            )
            embed.add_field(name="Watch it now!", value=msg.jump_url)

            match = re.search(YOUTUBE_REGEX, msg.content)
            code = await send_video_to_endpoint(video_url=match.group(0))
            if code == SUCCESS_CODE:
                embed.add_field(name="Website state", value=f"{await self.bot.fetch_application_emoji(IDs.customEmojis.CONNECTE)} Video sent to [repuls.io]({Links.REPULS_GAME})!")
            else:
                embed.add_field(name="Website state", value=f"{DefaultEmojis.WARN} Video failed to send to repuls.io ({code} error)!")

            await video_channel.send(embed=embed)
        else:
            await video_channel.send(f"""
I couldn't find any videos to display on the game's homepage 🫤...
**Become a <@&{IDs.serverRoles.YOUTUBER}> by respecting [the following conditions](https://discord.com/channels/603655329120518223/733177088961544202/1389263121591570496), and post your first videos!** 🚀""")
    
    # ---------------------------------- commands
    @commands.hybrid_command(name="addvideo", description="Post a new YouTube video (request for special roles)")
    @commands.has_any_role(IDs.serverRoles.YOUTUBER, IDs.serverRoles.STREAMER, IDs.serverRoles.ADMIN, IDs.serverRoles.DEVELOPER)
    async def addvideo(self, ctx: commands.Context, youtube_url: YouTubeLink):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        video_channel = self.bot.get_channel(IDs.serverChannel.VIDEO)
        if video_channel is not None:
            # the link is already verified as a correct youtube link
            await video_channel.send(f"### 📢 New YouTube video! 🎉\n{youtube_url}\n(*Posted by {ctx.author.mention}!*)")
            await send_hidden_message(ctx=ctx, text=f"{DefaultEmojis.CHECK} video posted in {video_channel.mention}!")
        else:
            self._video_channel_not_found(ctx=ctx)

    @commands.hybrid_command(name="video_leaderboard", description="Show the most voted YouTube videos")
    async def video_leaderboard(self, ctx: commands.Context, hours: int = VOTE_HOURS, message_limit: int = 50, top: int = 6):
        video_channel = self.bot.get_channel(IDs.serverChannel.VIDEO)
        if not video_channel:
            self._video_channel_not_found(ctx=ctx)
            return

        video_votes = []
        embed = discord.Embed(
            title="👏 YouTube Video Leaderboard",
            description=f"(within the last {hours}h, with a limit of {message_limit} message{"s" if message_limit > 1 else ""})",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Top {top} most voted YouTube videos")

        async for message in video_channel.history(limit=message_limit, after=hoursdelta(hours)):
            if not re.search(YOUTUBE_REGEX, message.content):
                continue

            msg = await video_channel.fetch_message(message.id)
            for reaction in msg.reactions:
                if str(reaction.emoji) == DefaultEmojis.CHECK:
                    if ENV == ENV_DEV_MODE:
                        video_votes.append((reaction.count, msg))
                    elif reaction.count > 1: # prod mode
                        video_votes.append((reaction.count, msg))
                    break

        if not video_votes:
            embed.add_field(
                name="Sorry, no voted videos found in the given timeframe...",
                value="Try broadening my search scope?",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        video_votes.sort(key=lambda x: x[0], reverse=True)
        top_videos = video_votes[:top]

        for idx, (votes, msg) in enumerate(top_videos, start=1):
            if idx == 1:
                header = "🥇"
            elif idx == 2:
                header = "🥈"
            elif idx == 3:
                header = "🥉"
            else:
                header = f"#{str(idx)}"
            embed.add_field(
                name=f"{header} - {votes} votes",
                value=f"[Watch video]({msg.jump_url}) here!" ,
                inline=False
            )

        await ctx.send(embed=embed)

    async def _video_channel_not_found(self, ctx: commands.Context):
        await send_hidden_message(ctx=ctx, text=f"{await self.bot.fetch_application_emoji(IDs.customEmojis.DECONNECTE)} Unable to find video channel (whose ID is supposed to be {IDs.serverChannel.VIDEO})!{ASK_HELP}")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(VoteCog(bot))