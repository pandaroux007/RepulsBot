"""
This cog contains all the automatic tasks and functions to find, display
and send the best YouTube video about the game to the site.

➜ Use https://regexr.com/ to understand, create and correct regex if you are a beginner and want to contribute.

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
from cogs_list import CogsNames
from utils import (
    hoursdelta,
    plurial,
    ADMIN_CMD
)

from log_system import (
    LogBuilder,
    LogColor,
    BOTLOG,
    log
)

from constants import (
    DefaultEmojis,
    PrivateData,
    IDs
)

# https://stackoverflow.com/questions/19377262/regex-for-youtube-url
YOUTUBE_REGEX = re.compile(
    r'((?:https?:)?\/\/(?:www\.|m\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be)\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?[\w\-]+(?:\S+)?)',
    re.IGNORECASE
)

# shared video (public channel)
SHARED_CHECK_HOURS = 48
SHARED_MESSAGE_LIMIT = 100
VOTE_REACTION = DefaultEmojis.UP_ARROW

# featured video (private channel)
FEATURE_CHECK_HOURS = 48
FEATURED_MESSAGES_LIMIT = 30
# reactions placed under the videos to define its status
VALIDATED_REACTION = DefaultEmojis.CHECK
ALREADY_USED_REACTION = DefaultEmojis.NO_ENTRY

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

def get_yt_url(message: str) -> str | None:
    video_url = re.search(YOUTUBE_REGEX, message)
    return video_url.group(0) if video_url else None

# https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
# ---------------------------------- vote cog (see README.md)
class VoteCog(commands.Cog, name=CogsNames.VOTE):
    """
    Not all messages fetch are an optimization omission, they are used to update the cache,
    especially for the number of reactions (https://github.com/Rapptz/discord.py/issues/861)
    """
    # ---------------------------------- task configuration
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shared_video_task.start()
        self.featured_video_task.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        elif message.channel.id == IDs.serverChannel.SHARED_VIDEO:
            if re.search(YOUTUBE_REGEX, message.content):
                await message.add_reaction(VOTE_REACTION)

    def cog_unload(self):
        self.shared_video_task.cancel()
        self.featured_video_task.cancel()

    # ---------------------------------- get shared videos from public community channel
    @tasks.loop(hours=SHARED_CHECK_HOURS)
    async def shared_video_task(self):
        shared_videos_channel = self.bot.get_channel(IDs.serverChannel.SHARED_VIDEO)
        last_better_votes = 1 # remove bot vote
        result_videos: list[discord.Message] = []
        async for message in shared_videos_channel.history(limit=SHARED_MESSAGE_LIMIT, after=hoursdelta(SHARED_CHECK_HOURS)):
            if not re.search(YOUTUBE_REGEX, message.content):
                continue # pass all messages without youtube links
            
            msg = await shared_videos_channel.fetch_message(message.id)
            for reaction in msg.reactions:
                if str(reaction.emoji) == VOTE_REACTION:
                    vote = reaction.count
                    if vote > last_better_votes:
                        last_better_votes = vote
                        result_videos = [msg]
                    elif vote == last_better_votes:
                        result_videos.append(msg)
                    break

        embed = discord.Embed()
        # no videos to send
        if len(result_videos) < 1:
            last_check = discord.utils.format_dt(hoursdelta(SHARED_CHECK_HOURS))
            embed.color = discord.Color.dark_blue()
            embed.description = f"No new most voted video since {last_check}..."
            await shared_videos_channel.send(embed=embed)
        # one or more videos found
        else:
            winner: discord.Message = None
            # only one winning video
            if len(result_videos) == 1:
                winner = result_videos[0]
                embed.set_footer(text=f"This video was selected with {last_better_votes} votes")
            # case of equality
            else:
                winner = random.choice(result_videos)
                embed.set_footer(text=f"A tie of {last_better_votes} votes for {len(result_videos)} videos, random selection")

            embed.title = "Congrats! New most-voted video"
            embed.color = discord.Color.brand_red()
            embed.description = f"🎬️ **[Click here now to watch it]({winner.jump_url})!**"

            async for msg in shared_videos_channel.history(limit=1):
                if msg.author.id == self.bot.user.id:
                    await msg.delete()
            await shared_videos_channel.send(embed=embed)

            featured_videos_channel = self.bot.get_channel(IDs.serverChannel.FEATURED_VIDEO)
            await featured_videos_channel.send(f"The community has chosen a new video ([voting link]({winner.jump_url}))!\n➜ {get_yt_url(winner.content) or "error"}")

    # ---------------------------------- admins select the featured video
    def _get_forced_id_from_topic(self, channel: discord.TextChannel) -> int | None:
        topic = (channel.topic or "")
        match = re.search(r"forced_video:(\d+)", topic)
        return int(match.group(1)) if match else None

    async def _set_forced_id_in_topic(self, channel: discord.TextChannel, msg_id: int | None) -> bool:
        """
        store forced id in topic (overwrite previous)
        returns True if successful, False if exception.
        """
        topic = (channel.topic or "")
        topic = re.sub(r"\s*forced_video:\d+\s*", '\n', topic).strip()
        if msg_id is not None:
            topic = (topic + ' ' + f"forced_video:{msg_id}").strip()
        try:
            await channel.edit(topic=topic)
            return True
        except Exception:
            return False

    @tasks.loop(hours=FEATURE_CHECK_HOURS)
    async def featured_video_task(self):
        featured_videos_channel = self.bot.get_channel(IDs.serverChannel.FEATURED_VIDEO)
        embed = discord.Embed(
            title="Send the video to repuls.io website...",
            color=discord.Color.brand_red()
        )
        # priority 1: forced message saved in channel topic
        forced_id = self._get_forced_id_from_topic(featured_videos_channel)
        if forced_id:
            try:
                forced_msg = await featured_videos_channel.fetch_message(forced_id)
            except Exception:
                await (
                    LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                    .title(f"{DefaultEmojis.WARN} Unable to find the message for the featured forced video")
                    .add_field(name="System fallback", value="Attempting to remove the incorrect ID and reverting to the normal system")
                    .send()
                )
                forced_msg = None
                await self._set_forced_id_in_topic(featured_videos_channel, None)

            if forced_msg:
                video_url = get_yt_url(forced_msg.content)
                if video_url:
                    await forced_msg.add_reaction(ALREADY_USED_REACTION)
                    status = await send_video_to_endpoint(video_url)
                    if status == 200:
                        embed.description = f"{DefaultEmojis.CHECK} **Forced video** sent to repuls.io website {forced_msg.jump_url}"
                        embed.color = discord.Color.brand_green()
                        await featured_videos_channel.send(embed=embed)
                    else:
                        embed.description = f"{DefaultEmojis.ERROR} Forced video failed to send to repuls.io ({status} error)"
                        await featured_videos_channel.send(embed=embed)
                        await log(
                            bot=self.bot, type=BOTLOG, color=LogColor.RED,
                            title=embed.description
                        )
                    return
                else:
                    await (
                        LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                        .title(f"{DefaultEmojis.WARN} Unable to find the link to the featured forced video")
                        .add_field(name="Detailed error", value="The \"forced\" message was indeed found in the featured videos channel, but it no longer contains a YouTube link")
                        .add_field(name="System fallback", value="Attempting to remove the invalid ID and reverting to the normal system")
                        .send()
                    )
                    await self._set_forced_id_in_topic(featured_videos_channel, None)

        # priority 2: list of approved and unused videos
        validated: list[discord.Message] = []
        search_window = hoursdelta(FEATURE_CHECK_HOURS)
        async for message in featured_videos_channel.history(limit=FEATURED_MESSAGES_LIMIT, after=search_window):
            if not re.search(YOUTUBE_REGEX, message.content):
                continue
            msg = await featured_videos_channel.fetch_message(message.id)
            if not msg.reactions:
                continue
            emojis = {str(r.emoji) for r in msg.reactions}
            if VALIDATED_REACTION in emojis:
                validated.append(msg)

        if not validated:
            embed.description = f"No validated video available since {discord.utils.format_dt(search_window, 'd')}. Admins must validate or force at least one of them, then restart the verification."
            embed.color = discord.Color.dark_orange()
            await featured_videos_channel.send(embed=embed)
            return

        unused = [m for m in validated if ALREADY_USED_REACTION not in {str(r.emoji) for r in m.reactions}]
        if unused:
            chosen_msg = random.choice(unused)
        else:
            chosen_msg = random.choice(validated)

        status = await send_video_to_endpoint(get_yt_url(chosen_msg.content))
        if status == 200:
            await chosen_msg.add_reaction(ALREADY_USED_REACTION)
            embed.description = f"{DefaultEmojis.CHECK} Video sent to repuls.io website {chosen_msg.jump_url}"
            embed.color = discord.Color.brand_green()
            await featured_videos_channel.send(embed=embed)
        else:
            embed.description = f"{DefaultEmojis.ERROR} Video failed to send to repuls.io ({status} error)"
            await featured_videos_channel.send(embed=embed)
            await log(
                bot=self.bot, type=BOTLOG, color=LogColor.RED,
                title=embed.description
            )

    @shared_video_task.before_loop
    async def before_vote_task(self):
        await self.bot.wait_until_ready()

    @featured_video_task.before_loop
    async def before_featured_task(self):
        await self.bot.wait_until_ready()

    # ---------------------------------- control commands
    @app_commands.command(description="Force a \"video message\" to be featured", extras={ADMIN_CMD: True})
    @app_commands.describe(message_link="Link to the message containing the video to force to be featured")
    async def set_forced_video(self, interaction: discord.Interaction, message_link: str):
        await interaction.response.defer(ephemeral=True)
        result = discord.Embed(
            title="Set the forced featured video",
            color=discord.Color.dark_blue()
        )
        if interaction.channel_id != IDs.serverChannel.FEATURED_VIDEO:
            result.description = f"{DefaultEmojis.ERROR} This command should be used only on featured videos channel"
            await interaction.followup.send(embed=result, ephemeral=True)
            return

        match = re.search(r"(\d{17,20})$", message_link)
        if not match:
            result.description = f"{DefaultEmojis.ERROR} Couldn't parse a message id from input message link"
            await interaction.followup.send(embed=result, ephemeral=True)
            return
        message_id = int(match.group(1))
        try:
            message = await interaction.channel.fetch_message(message_id)
            emojis = {str(r.emoji) for r in message.reactions}
            if VALIDATED_REACTION in emojis:
                is_validated = True
            else:
                is_validated = False
        except (discord.errors.NotFound, discord.errors.HTTPException):
            result.description = f"{DefaultEmojis.ERROR} Couldn't found the specified message from link"
            await interaction.followup.send(embed=result, ephemeral=True)
            return

        edited = await self._set_forced_id_in_topic(interaction.channel, message_id)
        if edited:
            result.description = f"{DefaultEmojis.CHECK} Video {message.jump_url} set as forced featured"
            if is_validated is False:
                result.add_field(name=f"{DefaultEmojis.WARN} Pay attention!", value="*The message you forced to be featured isn't validated (no check reaction). The forcing works but be sure to **validate the video**.*")
        else:
            result.description = f"{DefaultEmojis.ERROR} ID of {message.jump_url} registration failed"
        await interaction.followup.send(embed=result, ephemeral=True)

    @app_commands.command(description="Clear the forced featured video", extras={ADMIN_CMD: True})
    async def clear_forced_video(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = discord.Embed(
            title="Clear the forced featured video",
            color=discord.Color.dark_blue()
        )
        if interaction.channel_id != IDs.serverChannel.FEATURED_VIDEO:
            result.description = f"{DefaultEmojis.ERROR} This command should be used only on featured videos channel"
            await interaction.followup.send(embed=result, ephemeral=True)
            return

        edited = await self._set_forced_id_in_topic(interaction.channel, None)
        if edited:
            result.description = f"{DefaultEmojis.CHECK} Forced video cleared, the system is working normally again."
            result.set_footer(text="To refresh the site video, please restart the system")
        else:
            result.description = f"{DefaultEmojis.ERROR} An error occurred while clearing"
        await interaction.followup.send(embed=result, ephemeral=True)

    @app_commands.command(description="Force the bot to find and send the featured video now", extras={ADMIN_CMD: True})
    async def restart_video_loop(self, interaction: discord.Interaction, check_shared_video: bool = False):
        """
        NOTE:
        potential bug here, the bot can return a video already sent previously, no duplicate check for now
        """
        if check_shared_video:
            self.shared_video_task.restart()
        self.featured_video_task.restart()

        result = discord.Embed(
            title=f"Restard the video {plurial("system", 2 if check_shared_video else 1)}",
            description=f"{DefaultEmojis.CHECK} Restarting the video {plurial("system", 2 if check_shared_video else 1)} completed",
            color=discord.Color.dark_blue()
        )
        await interaction.response.send_message(embed=result, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(VoteCog(bot))