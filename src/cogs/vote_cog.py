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
import datetime
# bot files
from data.cogs import CogsNames
from tools.utils import (
    daysdelta,
    plurial
)

from tools.log_builder import (
    LogBuilder,
    LogColor,
    BOTLOG,
    log
)

from data.constants import (
    DefaultEmojis,
    PrivateData,
    IDs,
    ADMIN_CMD
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

# https://stackoverflow.com/questions/19377262/regex-for-youtube-url
YOUTUBE_REGEX = re.compile(
    r'(?:https?:)?\/\/(?:www\.|m\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be)\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?([\w\-]+)',
    re.IGNORECASE
)

# shared video (public channel)
SHARED_CHECK_HOURS = 24
SHARED_MESSAGE_LIMIT = 150
SHARED_BACK_UNTIL = 5 # scroll through messages up to 5 day ago
VOTE_REACTION = DefaultEmojis.UP_ARROW

# featured video (private channel)
FEATURED_CHECK_HOURS = 24
FEATURED_MESSAGES_LIMIT = 100
FEATURED_BACK_UNTIL = 5
# reactions placed under the videos to define its status
VALIDATED_REACTION = DefaultEmojis.CHECK
ALREADY_USED_REACTION = DefaultEmojis.NO_ENTRY

# https://apidog.com/blog/aiohttp-request/
# https://docs.aiohttp.org/en/stable/client_quickstart.html
async def send_video_to_endpoint(video_url: str) -> int | str:
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

async def get_website_featured_video() -> tuple[str | None, datetime.datetime | None]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://community.docskigames.com/api/feature-video") as resp:
                data = await resp.json()
                video_url = data.get("video_url", None)
                updated_str = data.get("updatedAt", None)
                updated_at_dt = datetime.datetime.fromisoformat(updated_str) if updated_str else None
                return video_url, updated_at_dt
    except Exception:
        return None, None

def get_yt_url(message: str, return_id: bool = False) -> str | tuple[str, str] | None:
    video_url = re.search(YOUTUBE_REGEX, message)
    if not video_url:
        return None
    if not return_id:
        return video_url.group(0) # full url
    return [video_url.group(0), video_url.group(1)] # url and video's id

# https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
class VoteCog(commands.Cog, name=CogsNames.VOTE):
    """
    Not all messages fetch are an optimization omission, they are used to update the cache,
    especially for the number of reactions (https://github.com/Rapptz/discord.py/issues/861)
    """
    # ---------------------------------- task configuration
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == IDs.serverChannel.SHARED_VIDEO:
            if re.search(YOUTUBE_REGEX, message.content):
                await message.add_reaction(VOTE_REACTION)

    def cog_load(self):
        self.vote_task.start()
        self.featured_video_task.start()

    def cog_unload(self):
        self.vote_task.cancel()
        self.featured_video_task.cancel()

    # ---------------------------------- get shared videos from public community channel
    @tasks.loop(hours=SHARED_CHECK_HOURS)
    async def vote_task(self):
        shared_videos_channel = self.bot.get_channel(IDs.serverChannel.SHARED_VIDEO)
        last_better_votes = 1 # remove bot vote
        result_videos: list[discord.Message] = []
        SEARCH_WINDOW = daysdelta(SHARED_BACK_UNTIL)
        async for message in shared_videos_channel.history(limit=SHARED_MESSAGE_LIMIT, after=SEARCH_WINDOW, oldest_first=True):
            if not re.search(YOUTUBE_REGEX, message.content):
                continue # pass all messages without youtube links

            msg = await shared_videos_channel.fetch_message(message.id)
            for reaction in msg.reactions:
                if str(reaction.emoji) == VOTE_REACTION:
                    vote = reaction.count
                    if vote > last_better_votes:
                        last_better_votes = vote
                        result_videos = [msg]
                    elif vote > 1 and vote == last_better_votes:
                        result_videos.append(msg)
                    break

        embed = discord.Embed()
        # no videos to send
        if len(result_videos) < 1:
            embed.color = discord.Color.dark_blue()
            embed.description = f"No new most voted video since {discord.utils.format_dt(SEARCH_WINDOW)}..."
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
            await shared_videos_channel.send(embed=embed)

            featured_videos_channel = self.bot.get_channel(IDs.serverChannel.FEATURED_VIDEO)
            await featured_videos_channel.send(f"The community has chosen a new video ([voting link]({winner.jump_url}))!\n➜ {get_yt_url(winner.content) or "error"}")

    # ---------------------------------- admins select the featured video
    @tasks.loop(hours=FEATURED_CHECK_HOURS)
    async def featured_video_task(self):
        featured_videos_channel = self.bot.get_channel(IDs.serverChannel.FEATURED_VIDEO)
        embed = discord.Embed(
            title="Send the video to repuls.io website...",
            color=discord.Color.brand_red()
        )
        # priority 1: forced message saved in channel topic
        forced_id, _useless_forced_until = await self.bot.youtube_storage.get_forced_video()
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
                await self.bot.youtube_storage.clear_forced_video()

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
                    await self.bot.youtube_storage.clear_forced_video()

        # priority 2: list of approved and unused videos
        validated: list[discord.Message] = []
        SEARCH_WINDOW = daysdelta(FEATURED_BACK_UNTIL)
        async for message in featured_videos_channel.history(limit=FEATURED_MESSAGES_LIMIT, after=SEARCH_WINDOW, oldest_first=True):
            if not re.search(YOUTUBE_REGEX, message.content):
                continue
            msg = await featured_videos_channel.fetch_message(message.id)
            if not msg.reactions:
                continue
            emojis = {str(r.emoji) for r in msg.reactions}
            if VALIDATED_REACTION in emojis:
                validated.append(msg)

        if not validated:
            embed.description = f"No validated video available since {discord.utils.format_dt(SEARCH_WINDOW, 'd')}. Admins must validate or force at least one of them, then restart the verification."
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

    @vote_task.before_loop
    async def before_vote_task(self):
        await self.bot.wait_until_ready()

    @featured_video_task.before_loop
    async def before_featured_task(self):
        await self.bot.wait_until_ready()

    # ---------------------------------- control commands
    @app_commands.command(description="[ADMIN] Force a \"video message\" to be featured")
    @app_commands.default_permissions(ADMIN_CMD)
    @app_commands.describe(message_link="Link to the message containing the video to force to be featured")
    @app_commands.choices(
        forced_until=[app_commands.Choice(name=f"{index} {plurial("day", index)}", value=index) for index in range(1, 8)]
    )
    async def set_forced_video(self, interaction: discord.Interaction, message_link: str, forced_until: app_commands.Choice[int]):
        await interaction.response.defer(ephemeral=True)
        result = discord.Embed(
            title="Set the forced featured video",
            color=discord.Color.dark_blue()
        )

        match = re.search(r"(\d{17,20})$", message_link)
        if not match:
            result.description = f"{DefaultEmojis.ERROR} Couldn't parse a message id from input message link"
            await interaction.followup.send(embed=result, ephemeral=True)
            return
        message_id = int(match.group(1))
        try:
            try:
                featured_videos_channel = self.bot.get_channel(IDs.serverChannel.FEATURED_VIDEO)
                message = await featured_videos_channel.fetch_message(message_id)
            except discord.NotFound:
                result.description = f"{DefaultEmojis.ERROR} The link must come from the featured videos channel"
                await interaction.followup.send(embed=result, ephemeral=True)
                return

            if not get_yt_url(message=message.content):
                result.description = f"{DefaultEmojis.ERROR} This message doesn't contain a video!"
                await interaction.followup.send(embed=result, ephemeral=True)
                return
            emojis = {str(r.emoji) for r in message.reactions}
            if VALIDATED_REACTION in emojis:
                is_validated = True
            else:
                is_validated = False
        except (discord.errors.NotFound, discord.errors.HTTPException):
            result.description = f"{DefaultEmojis.ERROR} Couldn't found the specified message from link"
            await interaction.followup.send(embed=result, ephemeral=True)
            return

        forced_until_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=forced_until.value)
        edited = await self.bot.youtube_storage.set_forced_video(message_id, forced_until_dt.isoformat())
        if edited:
            result.description = f"{DefaultEmojis.CHECK} Video {message.jump_url} set as forced featured for {forced_until.value} {plurial("day", forced_until.value)}"
            if is_validated is False:
                result.add_field(name=f"{DefaultEmojis.WARN} Pay attention!", value="*The message you forced to be featured isn't validated (no check reaction). The forcing works but be sure to **validate the video**.*")
            result.set_footer(text="To refresh the site video, please restart the system")
        else:
            result.description = f"{DefaultEmojis.ERROR} ID of {message.jump_url} registration failed"
        await interaction.followup.send(embed=result, ephemeral=True)

    @app_commands.command(description="[ADMIN] Clear the forced featured video")
    @app_commands.default_permissions(ADMIN_CMD)
    async def clear_forced_video(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = discord.Embed(
            title="Clear the forced featured video",
            color=discord.Color.dark_blue()
        )
        edited = await self.bot.youtube_storage.clear_forced_video()
        if edited:
            result.description = f"{DefaultEmojis.CHECK} Forced video cleared, the system is working normally again."
            result.set_footer(text="To refresh the site video, please restart the system")
        else:
            result.description = f"{DefaultEmojis.ERROR} An error occurred while clearing"
        await interaction.followup.send(embed=result, ephemeral=True)

    @app_commands.command(description="[ADMIN] Indicates if a video is currently being forced to feature, and more")
    @app_commands.default_permissions(ADMIN_CMD)
    async def is_forced_video(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(f"### {DefaultEmojis.INFO} Current status of forced video"))
        message_id, forced_until = await self.bot.youtube_storage.get_forced_video()
        if not message_id:
            container.add_item(discord.ui.TextDisplay("*No forced video currently (nothing in the database)*"))
        else:
            featured_videos_channel = self.bot.get_channel(IDs.serverChannel.FEATURED_VIDEO)
            video_msg = await featured_videos_channel.fetch_message(message_id)
            video_url, video_id = get_yt_url(video_msg.content, return_id=True)
            # https://stackoverflow.com/questions/2068344/how-do-i-get-a-youtube-video-thumbnail-from-the-youtube-api
            container.add_item(discord.ui.Section((
                    "➜ A video is currently being forced\n"
                    f"- Until: {discord.utils.format_dt(forced_until, 'R')}\n"
                    f"- Link: {video_url}\n"
                    f"- Taken from: [`source message`]({video_msg.jump_url})"
                ),
                accessory=discord.ui.Thumbnail(media=f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg")
            ))

        current_site_video, updated_at = await get_website_featured_video()
        if current_site_video:
            info = f"➜ {current_site_video}" + f"\n*(updated at {discord.utils.format_dt(updated_at)})*" if updated_at else ''
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"**🌐 Video currently on the site**\n{info}"))

        view.add_item(container)
        await interaction.followup.send(view=view, ephemeral=True)

    @app_commands.command(description="[ADMIN] Force the bot to find and send the featured video now")
    @app_commands.default_permissions(ADMIN_CMD)
    async def restart_featured_loop(self, interaction: discord.Interaction):
        self.featured_video_task.restart()

        result = discord.Embed(
            title="Restart the featured video loop",
            description=f"{DefaultEmojis.CHECK} Restarting the featured video system completed",
            color=discord.Color.dark_blue()
        )
        await interaction.response.send_message(embed=result, ephemeral=True)

async def setup(bot: "RepulsBot"):
    await bot.add_cog(VoteCog(bot))