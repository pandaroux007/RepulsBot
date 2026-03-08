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
import random
from datetime import timedelta
# bot files
from data.cogs import CogsNames
from tools.api_client import VideoSystemClient
from tools.utils import plurial
from tools.log_builder import (
    LogBuilder,
    LogColor,
    BOTLOG,
    log
)

from data.constants import (
    DefaultEmojis,
    IDs,
    ADMIN_CMD,
    DISCORD_MSG_ID_REGEX
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

# https://stackoverflow.com/questions/19377262/regex-for-youtube-url
YOUTUBE_REGEX = re.compile(
    r'(?:https?:)?\/\/(?:www\.|m\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be)\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?([\w\-]+)',
    re.IGNORECASE
)

# twitch-youtube (public channel)
SHARED_LOOP_HOURS = 24 # hours
SHARED_MESSAGE_LIMIT = 150
SHARED_BACK_UNTIL = 5 # scroll through messages up to 5 day ago
VOTE_REACTION = DefaultEmojis.UP_ARROW

# featured video (private channel)
FEATURED_LOOP_HOURS_SHORT = 12 # hours
FEATURED_LOOP_HOURS_LONG = 24 # hours
FEATURED_MESSAGES_LIMIT = 100
FEATURED_BACK_UNTIL = 5 # days
# reactions placed under the videos to define its status
VALIDATED_REACTION = DefaultEmojis.CHECK
ALREADY_USED_REACTION = DefaultEmojis.NO_ENTRY
REJECTED_REACTION = DefaultEmojis.CROSS

def is_unused(m: discord.Message) -> bool:
    return ALREADY_USED_REACTION not in {str(r.emoji) for r in m.reactions}

def is_validated(m: discord.Message) -> bool:
    return VALIDATED_REACTION in {str(r.emoji) for r in m.reactions}

def is_rejected(m: discord.Message) -> bool:
    return REJECTED_REACTION in {str(r.emoji) for r in m.reactions}

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
    especially for the content (https://github.com/Rapptz/discord.py/issues/861)
    """
    # ---------------------------------- task configuration
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot
        self.featured_check_interval = FEATURED_LOOP_HOURS_SHORT

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == IDs.serverChannel.SHARED_VIDEO:
            if get_yt_url(message.content):
                await message.add_reaction(VOTE_REACTION)

    def cog_load(self):
        self.vote_task.start()
        self.featured_video_task.start()

    def cog_unload(self):
        self.vote_task.cancel()
        self.featured_video_task.cancel()

    # ---------------------------------- get shared videos from public community channel
    @tasks.loop(hours=SHARED_LOOP_HOURS)
    async def vote_task(self):
        shared_videos_channel: discord.PartialMessageable = self.bot.get_partial_messageable(IDs.serverChannel.SHARED_VIDEO)

        votes_map: dict[int, list[discord.Message]] = {}
        SEARCH_WINDOW = discord.utils.utcnow() - timedelta(days=SHARED_BACK_UNTIL)
        async for message in shared_videos_channel.history(limit=SHARED_MESSAGE_LIMIT, after=SEARCH_WINDOW, oldest_first=True):
            if not get_yt_url(message.content) or not message.reactions or is_rejected(message):
                continue  # pass all messages without youtube links
            for reaction in message.reactions:
                if str(reaction.emoji) == VOTE_REACTION:
                    vote = reaction.count
                    if vote > 1: # ignore bot vote
                        votes_map.setdefault(vote, []).append(message)
                    break

        embed = discord.Embed(color=discord.Color.brand_red())
        if not votes_map: # no videos to send
            embed.color = discord.Color.dark_blue()
            embed.description = f"No new most voted video since {discord.utils.format_dt(SEARCH_WINDOW)}..."
            await shared_videos_channel.send(embed=embed)
            return

        sorted_votes = sorted(votes_map.keys(), reverse=True)
        top_vote = sorted_votes[0]
        top_msgs = votes_map[top_vote]

        winner: discord.Message | None = None
        selected_votes: int = top_vote # by default the max number of votes
        selection_reason: str = None

        unused_top = [m for m in top_msgs if is_unused(m)]
        if unused_top:
            winner = random.choice(unused_top)
            selection_reason = "random_from_top" if len(unused_top) > 1 else "only_unused_top"
        else: # search next highest unused
            for count in sorted_votes[1:]:
                unused = [m for m in votes_map[count] if is_unused(m)]
                if unused:
                    winner = unused[0]
                    selected_votes = count
                    selection_reason = "fallback_to_lower"
                    break
            if not winner:
                winner = random.choice(top_msgs)
                selection_reason = "all_used_fallback"

        await winner.add_reaction(ALREADY_USED_REACTION)

        embed.title = "🎬️ Congrats! New most-voted video submission"
        embed.description = f"**[Click here now to see the nominated video]({winner.jump_url})!**"
        embed.description += "\n*The video has been queued for review by our staff (before possible feature)*"
        if selection_reason == "only_unused_top":
            embed.set_footer(text=f"This video was nominated with {selected_votes} votes")
        elif selection_reason == "random_from_top" or selection_reason == "all_used_fallback":
            embed.set_footer(text=f"A tie of {selected_votes} votes for {len(top_msgs)} videos, random selection")
        elif selection_reason == "fallback_to_lower":
            embed.set_footer(text=f"This video was nominated with {selected_votes} votes (top was {top_vote})")
        await shared_videos_channel.send(embed=embed)

        featured_videos_channel: discord.PartialMessageable = self.bot.get_partial_messageable(IDs.serverChannel.FEATURED_VIDEO)
        await featured_videos_channel.send(f"The community has chosen a new video ([voting link]({winner.jump_url}))!\n➜ {get_yt_url(winner.content) or "error"}")

    # ---------------------------------- admins select the featured video
    @tasks.loop()
    async def featured_video_task(self):
        # update the interval in case of a restart
        self.featured_video_task.change_interval(hours=self.featured_check_interval)

        featured_videos_channel: discord.PartialMessageable = self.bot.get_partial_messageable(IDs.serverChannel.FEATURED_VIDEO)
        embed = discord.Embed(
            title="Send the video to repuls.io website...",
            color=discord.Color.brand_red()
        )
        # priority 1: forced message saved in channel topic
        message_id, days_forced, forced_until_dt = await self.bot.youtube_storage.get_forced_video()
        if message_id:
            forced_message = None
            if forced_until_dt:
                if discord.utils.utcnow() >= forced_until_dt:
                    await self.bot.youtube_storage.clear_forced_video()
            else:
                try:
                    forced_message = await featured_videos_channel.fetch_message(message_id)
                except discord.NotFound:
                    forced_message = None
                    is_clean_successful_msg_not_fount = await self.bot.youtube_storage.clear_forced_video()
                    await (
                        LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                        .title(f"{DefaultEmojis.WARN} Unable to find the message for the featured forced video")
                        .add_field(name="System fallback", value=(
                            f"Attempting to remove the incorrect ID (success: {is_clean_successful_msg_not_fount}) and reverting to the normal system"
                        ))
                        .send()
                    )

            if forced_message:
                video_url = get_yt_url(forced_message.content)
                if video_url:
                    status = await VideoSystemClient.send_video_to_endpoint(video_url)
                    if status == 200:
                        embed.description = f"{DefaultEmojis.CHECK} **Forced video** sent to repuls.io website {forced_message.jump_url}"
                        embed.color = discord.Color.brand_green()
                        await featured_videos_channel.send(embed=embed)

                        await forced_message.add_reaction(ALREADY_USED_REACTION)
                        generated_forced_until_dt = await self.bot.youtube_storage.activate_forced_video()
                        if generated_forced_until_dt:
                            await log(
                                bot=self.bot, type=BOTLOG, color=LogColor.BLUE,
                                title=f"{DefaultEmojis.INFO} The countdown for the forced video now begins",
                                msg=(
                                    f"The countdown for the following video (forced to run for {days_forced} {plurial("day", days_forced)}) has begun\n"
                                    f"➜ {video_url} (from {forced_message.jump_url})\n"
                                    f"➜ The countdown will expire on {discord.utils.format_dt(generated_forced_until_dt)}"
                                )
                            )
                        return
                    else:
                        embed.description = f"{DefaultEmojis.ERROR} **Forced video** failed to send to repuls.io ({status} error)"
                        await featured_videos_channel.send(embed=embed)
                        await log(bot=self.bot, type=BOTLOG, color=LogColor.RED, title=embed.description)
                else:
                    is_clean_successful_no_video = await self.bot.youtube_storage.clear_forced_video()
                    await (
                        LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                        .title(f"{DefaultEmojis.WARN} Unable to find the link to the featured forced video")
                        .add_field(name="Detailed error", value="The \"forced\" message was indeed found in the featured videos channel, but it no longer contains a YouTube link")
                        .add_field(name="System fallback", value=(
                            f"Attempting to remove the incorrect ID (success: {is_clean_successful_no_video}) and reverting to the normal system"
                        ))
                        .send()
                    )

        # priority 2: list of approved and unused videos
        validated: list[discord.Message] = []
        SEARCH_WINDOW = discord.utils.utcnow() - timedelta(days=FEATURED_BACK_UNTIL)
        async for message in featured_videos_channel.history(limit=FEATURED_MESSAGES_LIMIT, after=SEARCH_WINDOW, oldest_first=True):
            if not get_yt_url(message.content) or not message.reactions:
                continue
            if is_validated(message):
                validated.append(message)

        if not validated:
            embed.description = f"No validated video available since {discord.utils.format_dt(SEARCH_WINDOW, 'd')}.\nAdmins must validate or force at least one of them, then restart the verification."
            embed.color = discord.Color.dark_orange()
            await featured_videos_channel.send(embed=embed)
            return

        unused = [m for m in validated if is_unused(m)]
        chosen_msg = random.choice(unused) if unused else random.choice(validated)

        next_interval = FEATURED_LOOP_HOURS_LONG if len(unused) == 1 else FEATURED_LOOP_HOURS_SHORT
        self.featured_video_task.change_interval(hours=next_interval)
        self.featured_check_interval = next_interval

        status = await VideoSystemClient.send_video_to_endpoint(get_yt_url(chosen_msg.content))
        if status == 200:
            await chosen_msg.add_reaction(ALREADY_USED_REACTION)
            embed.description = f"{DefaultEmojis.CHECK} Video sent to repuls.io website {chosen_msg.jump_url}"
            embed.color = discord.Color.brand_green()
            await featured_videos_channel.send(embed=embed)

            shared_videos_channel: discord.PartialMessageable = self.bot.get_partial_messageable(IDs.serverChannel.SHARED_VIDEO)
            message = await shared_videos_channel.send(f"🎉 A new video has been featured on the site!\nCheck it out! {get_yt_url(chosen_msg.content)}")
            await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=2))
            await message.remove_reaction(VOTE_REACTION, self.bot.user)
        else:
            embed.description = f"{DefaultEmojis.ERROR} Video failed to send to repuls.io ({status} error)"
            await featured_videos_channel.send(embed=embed)
            await log(bot=self.bot, type=BOTLOG, color=LogColor.RED, title=embed.description)

    @vote_task.before_loop
    async def before_vote_task(self):
        await self.bot.wait_until_ready()

    @featured_video_task.before_loop
    async def before_featured_task(self):
        await self.bot.wait_until_ready()

    # ---------------------------------- control commands
    @app_commands.command(description="[ADMIN] Force a \"video message\" to be featured")
    @app_commands.guild_only()
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

        match = re.search(DISCORD_MSG_ID_REGEX, message_link)
        if not match:
            result.description = f"{DefaultEmojis.ERROR} Couldn't parse a message id from input message link"
            await interaction.followup.send(embed=result, ephemeral=True)
            return
        message_id = int(match.group(1))
        try:
            featured_videos_channel: discord.PartialMessageable = self.bot.get_partial_messageable(IDs.serverChannel.FEATURED_VIDEO)
            message = await featured_videos_channel.fetch_message(message_id)
            if not is_validated(message):
                result.description = (
                    f"{DefaultEmojis.WARN} The video you're trying to feature hasn't been approved, "
                    "so I don't know if it complies with Poki's publishing guidelines.\n\n"
                    f"If you want to force (or just feature) it, **please approve it with {VALIDATED_REACTION}**"
                )
                await interaction.followup.send(embed=result, ephemeral=True)
                return
        except discord.NotFound:
            result.description = f"{DefaultEmojis.ERROR} The link must come from the featured videos channel\n(*couldn't found the specified message from link*)"
            await interaction.followup.send(embed=result, ephemeral=True)
            return

        if not get_yt_url(message=message.content):
            result.description = f"{DefaultEmojis.ERROR} This message doesn't contain a video!"
            await interaction.followup.send(embed=result, ephemeral=True)
            return

        edited = await self.bot.youtube_storage.set_forced_video(message_id, forced_until.value)
        if edited:
            result.description = (
                f"{DefaultEmojis.CHECK} [This video has been configured]({message.jump_url}) as forced for {forced_until.value} {plurial("day", forced_until.value)}\n"
                "*Note that the countdown will start when the video is actually sent to the site, not now.* "
                "**To refresh the site video, please restart the system**"
            )
            await log(
                bot=self.bot, type=BOTLOG, color=LogColor.BLUE,
                title=f"{DefaultEmojis.INFO} {interaction.user.mention} forced a video",
                msg=f"➜ {message_link} (for {forced_until.value} {plurial("day", forced_until.value)})"
            )
        else:
            result.description = f"{DefaultEmojis.ERROR} ID of {message.jump_url} registration failed"
        await interaction.followup.send(embed=result, ephemeral=True)

    @app_commands.command(description="[ADMIN] Clear the forced featured video")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def clear_forced_video(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = discord.Embed(
            title="Clear the forced featured video",
            color=discord.Color.dark_blue()
        )
        is_clean_successful = await self.bot.youtube_storage.clear_forced_video()
        if is_clean_successful:
            result.description = f"{DefaultEmojis.CHECK} Forced video cleared, the system is working normally again."
            result.set_footer(text="To refresh the site video, please restart the system")
            await log(
                bot=self.bot, type=BOTLOG, color=LogColor.ORANGE,
                title=f"{DefaultEmojis.INFO} {interaction.user.mention} cleared the forced video"
            )
        else:
            result.description = f"{DefaultEmojis.ERROR} An error occurred while clearing"
        await interaction.followup.send(embed=result, ephemeral=True)

    @app_commands.command(description="[ADMIN] Force the bot to find and send the featured video now")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def restart_featured_loop(self, interaction: discord.Interaction, and_vote_loop: bool = False):
        self.featured_video_task.restart()
        if and_vote_loop:
            self.vote_task.restart()

        result = discord.Embed(
            title=f"Restart the video {plurial("system", 2 if and_vote_loop else 1)}",
            description=f"{DefaultEmojis.CHECK} Restarting the video {plurial("system", 2 if and_vote_loop else 1)} completed",
            color=discord.Color.dark_blue()
        )
        await interaction.response.send_message(embed=result, ephemeral=True)
        await log(
            bot=self.bot, type=BOTLOG, color=LogColor.ORANGE,
            title=f"{DefaultEmojis.INFO} {interaction.user.mention} performed a video system restart",
            msg="He/she restarted the featured video system" + (" as well as the voting system." if and_vote_loop else '')
        )

    # ---------------------------------- informative command
    @app_commands.command(description="[ADMIN] Indicates if a video is currently being forced to feature, and more")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def video_system_info(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=f"### {DefaultEmojis.INFO} Current status of forced video"))
        message_id, days_forced, forced_until_dt = await self.bot.youtube_storage.get_forced_video()
        if not message_id:
            container.add_item(discord.ui.TextDisplay(content="*No forced video currently (nothing in the database)*"))
        else:
            featured_videos_channel: discord.PartialMessageable = self.bot.get_partial_messageable(IDs.serverChannel.FEATURED_VIDEO)
            video_msg = await featured_videos_channel.fetch_message(message_id)
            video_url, video_id = get_yt_url(video_msg.content, return_id=True)
            # https://stackoverflow.com/questions/2068344/how-do-i-get-a-youtube-video-thumbnail-from-the-youtube-api
            container.add_item(discord.ui.Section((
                    "➜ A video is currently being forced\n" +
                    (f"- Until: {discord.utils.format_dt(forced_until_dt, 'R')} ({days_forced} {plurial("day", days_forced)})\n" if forced_until_dt else f"- For {days_forced} {plurial("day", days_forced)}, awaiting activation.\n") +
                    f"- Link: {video_url}\n"
                    f"- Taken from: [`source message`]({video_msg.jump_url})"
                ),
                accessory=discord.ui.Thumbnail(media=f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg")
            ))

        current_site_video, updated_at = await VideoSystemClient.get_website_featured_video()
        if current_site_video:
            info = f"➜ {current_site_video}" + f"\n*(updated at {discord.utils.format_dt(updated_at)})*" if updated_at else ''
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(content=f"**🌐 Video currently on the site**\n{info}"))

        if self.featured_video_task._next_iteration:
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(content=(
                f"The featuring loop will run {discord.utils.format_dt(self.featured_video_task._next_iteration, 'R')} ({self.featured_check_interval}h)"
            )))

        view = discord.ui.LayoutView()
        view.add_item(container)
        await interaction.followup.send(view=view, ephemeral=True)

async def setup(bot: "RepulsBot"):
    await bot.add_cog(VoteCog(bot))