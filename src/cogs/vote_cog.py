"""
This cog contains all the automatic tasks and functions to find, display
and send the best YouTube video about the game to the site.

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import tasks, commands
from discord import app_commands
import re
import aiohttp
import random
# bot files
from utils import (
    hoursdelta,
    nl
)

from cogs_list import CogsNames
from constants import (
    DefaultEmojis,
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

VOTE_HOURS = 48
SUCCESS_CODE = 200
REACTION = DefaultEmojis.CHECK

FEATURED_VIDEO_MSG = f"""
And you, do you want your video to appear on the game's main page?
Then hurry up and post the link here, and cross your fingers...
I come and check the best video every {VOTE_HOURS} hours, you have every chance!
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

# https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
# ---------------------------------- vote cog (see README.md)
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

        better_video_msgs = []
        last_better_votes = 0
        after_time = hoursdelta(5 * 24) # 5 days

        async for message in video_channel.history(limit=50, after=after_time):
            if not re.search(YOUTUBE_REGEX, message.content):
                continue # pass all messages without youtube links
            
            # update message cache (https://github.com/Rapptz/discord.py/issues/861)
            msg = await video_channel.fetch_message(message.id)
            for reaction in msg.reactions:
                if str(reaction.emoji) == REACTION:
                    vote = reaction.count
                    if vote > last_better_votes:
                        last_better_votes = vote
                        better_video_msgs = [msg]
                    elif vote == last_better_votes:
                        better_video_msgs.append(msg)
                    break

        await self.process_winner(video_channel, better_video_msgs, last_better_votes)

    async def process_winner(self, video_channel: discord.abc.Messageable, messages: list[discord.Message], vote_count: int):
        embed = discord.Embed(
            title="New featured video! 🎉",
            color=discord.Color.brand_red(),
            timestamp=discord.utils.utcnow()
        )
        # no videos to send, notify youtubers
        if len(messages) < 1:
            embed.title = "I couldn't find any videos to display on the game's homepage 🫤..."
            embed.description = f"Become a <@&{IDs.serverRoles.YOUTUBER}> by meeting [these conditions](https://discord.com/channels/603655329120518223/733177088961544202/1389263121591570496), and post your first videos! 🚀"
            embed.timestamp = None
        # one or more videos found to send
        else:
            winner: discord.Message = None
            # only one winning video
            if len(messages) == 1:
                winner = messages[0]
                embed.add_field(
                    name="Watch it now!",
                    value=f"🎬 [Click here to watch the video]({winner.jump_url}), by {winner.author.mention}!",
                    inline=False
                )
                embed.set_footer(text=nl(FEATURED_VIDEO_MSG))
            # case of equality
            else:
                embed.title = "👏 Bravo! Several videos are tied!"
                embed.description = f"The following videos come in first with {vote_count} votes each!"

                for idx, m in enumerate(messages, 1):
                    embed.add_field(name="", value=f"{idx}. [Video]({m.jump_url}) of {m.author.mention}", inline=False)

                winner = random.choice(messages)
                embed.add_field(name="The winner drawn at random is", value=f"This [video]({winner.jump_url}) of {winner.author.mention}!", inline=True)

            match = re.search(YOUTUBE_REGEX, winner.content)
            code = await send_video_to_endpoint(video_url=match.group(0))

            log_channel = self.bot.get_channel(IDs.serverChannel.LOG)
            if log_channel:
                if code == SUCCESS_CODE:
                    status = f"{DefaultEmojis.CHECK} Video sent to repuls.io!"
                else:
                    status = f"{DefaultEmojis.WARN} Video failed to send to repuls.io ({code} error)"
                await log_channel.send(f"**Website state** : {status}", silent=True)

        await video_channel.send(embed=embed)
    
    # ---------------------------------- command
    @app_commands.command(name="video_leaderboard", description="Show the most voted YouTube videos")
    async def video_leaderboard(self, interaction: discord.Interaction, hours: int = VOTE_HOURS, message_limit: int = 50, top: int = 6):
        video_channel = self.bot.get_channel(IDs.serverChannel.VIDEO)
        if not video_channel:
            await interaction.response.send_message(
                content=f"{await self.bot.fetch_application_emoji(IDs.customEmojis.DECONNECTE)} Unable to find video channel!{ASK_HELP}",
                ephemeral=True
            )
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
                if str(reaction.emoji) == REACTION:
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
            await interaction.response.send_message(embed=embed)
            return
        else:
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

            await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(VoteCog(bot))