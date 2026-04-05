"""
Just an automated system for managing idiots
who want to mess with the server

:copyright: (c) 2026-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import (
    commands,
    tasks
)
import asyncio

import time
from datetime import (
    timedelta,
    datetime
)

from enum import Enum
from dataclasses import dataclass
from collections import (
    defaultdict,
    deque
)

# bot files
from data.cogs import CogsNames
from data.constants import (
    DefaultAntiraidSettings,
    DefaultEmojis,
    IDs,
    AUTHORIZED_ROLES,
    ADMIN_CMD,
    CMD_PREFIX
)

from tools.log_builder import (
    LogBuilder,
    LogColor,
    BOTLOG,
    MODLOG,
    # log
)

from typing import (
    Callable,
    Coroutine,
    Optional,
    TYPE_CHECKING
)
if TYPE_CHECKING:
    from main import RepulsBot

# ---------------------------------- unlock command interface
class UnlockButton(discord.ui.Button):
    def __init__(self, bot: RepulsBot, callback: Callable[[], Coroutine]):
        super().__init__(label="Unlock", emoji='🔓')
        self.bot = bot
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        is_success = await self.callback_func()
        view = discord.ui.LayoutView()
        container = discord.ui.Container()
        if is_success:
            container.accent_color = discord.Color.brand_green()
            container.add_item(discord.ui.TextDisplay(content=f"> {DefaultEmojis.CHECK} The operation was executed successfully."))
        else:
            container.accent_color = discord.Color.dark_orange()
            container.add_item(discord.ui.TextDisplay(content=f"> {DefaultEmojis.WARN} Something seems to have gone wrong (*see logs for details*)"))
        view.add_item(container)
        await interaction.response.edit_message(view=view)

# ---------------------------------- raid alerts ui
...

# ---------------------------------- antiraid config
MAX_MESSAGE_LIFESPAN = 60 # 1mn
MAX_TRIGGER_LIFESPAN = 900 # 15mn
MAX_LOG_MESSAGES = 5000
ANTIRAID_ALERTS_COOLDOWN_MN = 10

class ModActionType(Enum):
    TIMEOUT = 1
    KICK = 2
    BAN = 3

@dataclass
class LoggedMessage:
    user_id: int
    channel_id: int
    message_id: int
    timestamp: float
    # content: str
    has_medias: bool

@dataclass
class AntiraidState:
    active: bool = False
    last_alert: datetime | None = None
    reason: str | None = None

class AntiRaidCog(commands.Cog, name=CogsNames.ANTIRAID):
    def __init__(self, bot: RepulsBot):
        self.bot = bot
        self.antiraid_current_state = AntiraidState()
        # https://www.geeksforgeeks.org/python/defaultdict-in-python/
        # https://www.geeksforgeeks.org/python/deque-in-python/
        self.message_log: deque[LoggedMessage] = deque(maxlen=MAX_LOG_MESSAGES)
        self.user_triggers = defaultdict(deque)
        self.channel_triggers = defaultdict(deque)
        self.unlock_tasks: dict[int, asyncio.Task] = {}

    # ---------------------------------- utility functions
    @property
    async def config(self) -> dict | None:
        return await self.bot.moderation_storage.get_antiraid_settings()

    @property
    async def channels_lock(self) -> dict | None:
        return await self.bot.moderation_storage.load_channel_locks()

    @tasks.loop(seconds=60)
    async def memory_cleanup(self):
        NOW = time.time()

        for user_id in list(self.user_triggers.keys()):
            dq = self.user_triggers[user_id]
            while dq and NOW - dq[0] > MAX_TRIGGER_LIFESPAN:
                dq.popleft()
            if not dq:
                del self.user_triggers[user_id]

        for channel_id in list(self.channel_triggers.keys()):
            dq = self.channel_triggers[channel_id]
            while dq and NOW - dq[0] > MAX_TRIGGER_LIFESPAN:
                dq.popleft()
            if not dq:
                del self.channel_triggers[channel_id]

        message_cleaned_count = 0
        while self.message_log and (NOW - self.message_log[0].timestamp) > MAX_MESSAGE_LIFESPAN:
            self.message_log.popleft()
            message_cleaned_count += 1

    async def cog_load(self):
        channel_locks = await self.channels_lock
        if channel_locks:
            now = discord.utils.utcnow()
            for channel_id, locked_until in channel_locks.items():
                is_in_past = bool(now >= locked_until)
                task = self.bot.loop.create_task(
                    self.unlock_channel(channel_id, None if is_in_past else locked_until, "Expired lock on restart" if is_in_past else "Automatic unlocking")
                )
                self.unlock_tasks[channel_id] = task
                task.add_done_callback(lambda t, cid=channel_id: self.unlock_tasks.pop(cid, None))

        if not self.memory_cleanup.is_running():
            self.memory_cleanup.start()

    def cog_unload(self):
        self.memory_cleanup.cancel()

        for task in list(self.unlock_tasks.values()):
            if not task.done():
                task.cancel()
        self.unlock_tasks.clear()

        self.message_log.clear()
        self.user_triggers.clear()
        self.channel_triggers.clear()

    # ---------------------------------- the various anti-spam systems (combined to form the antiraid)
    """
    NOTE: I use the timestamp of the calling function rather than
    regenerating it in the functions below, to avoid incompatibilities.
    """

    def get_user_messages(self, user_id: int, window_s: int, now: float) -> list[LoggedMessage]:
        """
        Returns
        --------
        `list[LoggedMessage]`
            Messages from the targeted user
        """
        messages = []
        for msg in reversed(self.message_log):
            if now - msg.timestamp > window_s:
                break
            if msg.user_id == user_id:
                messages.append(msg)
        return messages

    def get_channel_messages(self, channel_id: int, window_s: int, now: float) -> list[LoggedMessage]:
        """
        Returns
        --------
        `list[LoggedMessage]`
            Messages from the targeted channel
        """
        messages = []
        for msg in reversed(self.message_log):
            if now - msg.timestamp > window_s:
                break
            if msg.channel_id == channel_id:
                messages.append(msg)
        return messages

    def add_user_trigger(self, user_id: int, now: float) -> int:
        """
        Increments the trigger counter for the given user

        Returns
        --------
        `int`: The number of recent triggers for this user
        """
        dq = self.user_triggers[user_id]
        dq.append(now)
        while dq and now - dq[0] > MAX_TRIGGER_LIFESPAN:
            dq.popleft()
        return len(dq)
    
    def add_channel_trigger(self, channel_id: int, now: float) -> int:
        """
        Increments the trigger counter for the given channel

        Returns
        --------
        `int`: The number of recent triggers for this channel
        """
        dq = self.channel_triggers[channel_id]
        dq.append(now)
        while dq and now - dq[0] > MAX_TRIGGER_LIFESPAN:
            dq.popleft()
        return len(dq)

    def get_spam_message(self, user_id: int, window_s: int, now: float) -> dict[int, list[discord.Object]]:
        channel_with_msg_ids = defaultdict(list)
        message_count = 0
        for msg in reversed(self.message_log):
            if now - msg.timestamp > window_s:
                break
            if msg.user_id == user_id:
                channel_with_msg_ids[msg.channel_id].append(discord.Object(id=msg.message_id))
                message_count += 1
                if message_count >= 100:
                    break
        return dict(channel_with_msg_ids)

    async def trigger_raid_alert(self, reason: str, affected_channels: Optional[list[discord.TextChannel]] = None):
        now = discord.utils.utcnow()

        self.antiraid_current_state.active = True
        self.antiraid_current_state.last_alert = now
        self.antiraid_current_state.reason = reason

        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=f"### {DefaultEmojis.CRITICAL} Potential raid detected\n**Reason**:\n*{reason}*"))
        if affected_channels:
            display = '\n'.join(f"- {channel.jump_url}" for channel in affected_channels)
            container.add_item(discord.ui.TextDisplay(content=f"**Affected channels**\n{display}"))

        container.add_item(discord.ui.Separator())
        """ async def _mark_raid_complete():
            self.antiraid_current_state.active = False
            return True """

        container.add_item(discord.ui.Section(
            discord.ui.TextDisplay(content=f"-# Next alert available: {discord.utils.format_dt((now + timedelta(minutes=ANTIRAID_ALERTS_COOLDOWN_MN)), 'R')}"),
            accessory=discord.ui.Button(label="Mark the raid as complete", emoji='🛡️')
        ))
        view.add_item(container)
        log_channel = self.bot.get_partial_messageable(IDs.serverChannel.BOTLOG)
        await log_channel.send(view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        config = await self.config
        user = message.author

        if user.bot or not message.guild or not config or config.get("antiraid_enabled", DefaultAntiraidSettings.ANTIRAID_STATE) == 0:
            return
        if user.guild_permissions.administrator or any(role.id in AUTHORIZED_ROLES for role in user.roles):
            return

        NOW = time.time()
        is_recently_joined = bool(isinstance(user, discord.Member) and (discord.utils.utcnow() - user.joined_at) < timedelta(days=3))
        is_new_account = bool((discord.utils.utcnow() - user.created_at) < timedelta(weeks=1))

        entry = LoggedMessage(
            user_id=user.id,
            channel_id=message.channel.id,
            message_id=message.id,
            timestamp=message.created_at.timestamp(),
            # content=message.content,
            has_medias=(bool(message.attachments) or "http" in message.content.lower())
        )
        self.message_log.append(entry)

        # ---------------------------------- spam detections & raid alert
        burst_spam = False
        multi_channel_spam = False
        action = None
        reason = None
        trigger_recorded = False

        # Prevent newer members from sending media
        if is_recently_joined and entry.has_medias:
            try:
                await message.delete()
                await message.channel.send(f"> ⚠️ {user.mention} You are too new to send links or files here.", delete_after=5)
            except Exception as e:
                await (
                    LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                    .title(f"{DefaultEmojis.CRITICAL} Unable to perform message cleanup")
                    .description(f"Member {user.mention} is too new to send media\n```\n{e}\n```")
                    .send()
                )
            self.add_user_trigger(entry.user_id, NOW)
            trigger_recorded = True

        # Burst spam detection on a single channel and user
        MSG_SPAM_THRESHOLD = config.get("user_msg_spam_threshold", DefaultAntiraidSettings.USER_MSG_SPAM_THRESHOLD)
        MSG_SPAM_WINDOW = config.get("user_msg_spam_interval_s", DefaultAntiraidSettings.USER_MSG_SPAM_INTERVAL_S)
        user_msg_count = len(self.get_user_messages(entry.user_id, MSG_SPAM_WINDOW, NOW))
        if user_msg_count >= MSG_SPAM_THRESHOLD:
            burst_spam = True

        # Rapid spamming between multiple channels
        CHANNELS_SPAM_THRESHOLD = config.get("user_channel_spam_threshold", DefaultAntiraidSettings.USER_CHANNEL_SPAM_THRESHOLD)
        CHANNELS_SPAM_WINDOW = config.get("user_channel_spam_interval_s", DefaultAntiraidSettings.USER_CHANNEL_SPAM_INTERVAL_S)
        user_channel_count = len(set(msg.channel_id for msg in self.get_user_messages(entry.user_id, CHANNELS_SPAM_WINDOW, NOW)))
        if user_channel_count >= CHANNELS_SPAM_THRESHOLD:
            multi_channel_spam = True

        MAX_USER_TRIGGERS = config.get("user_max_triggers_before_mod", DefaultAntiraidSettings.USER_MAX_TRIGGERS_BEFORE_MOD)
        if burst_spam or multi_channel_spam:
            user_triggers = self.add_user_trigger(entry.user_id, NOW) if not trigger_recorded else len(self.user_triggers[entry.user_id])
            trigger_recorded = True

            if user_triggers >= MAX_USER_TRIGGERS:
                if is_recently_joined or is_new_account:
                    action = ModActionType.BAN
                    reason = "New user/member + repeated spam"
                else:
                    action = ModActionType.KICK
                    reason = "Repeated spam in too short a time"
            else:
                action = ModActionType.TIMEOUT
                reason = f"Spam detected (burst: {burst_spam} | multi-channel: {multi_channel_spam})"
                await message.channel.send(f"> 🚫 {message.author.mention} You sent messages too quickly!", delete_after=4)

        # Spam (potentially from multiple members) on a single channel
        CHANNEL_SPAM_THRESHOLD = config.get("channel_spam_threshold", DefaultAntiraidSettings.CHANNEL_SPAM_THRESHOLD)
        CHANNEL_SPAM_WINDOW = config.get("channel_spam_interval_s", DefaultAntiraidSettings.CHANNEL_SPAM_INTERVAL_S)
        channel_msg_count = len(self.get_channel_messages(entry.channel_id, CHANNEL_SPAM_WINDOW, NOW))
        if channel_msg_count >= CHANNEL_SPAM_THRESHOLD:
            self.add_channel_trigger(entry.channel_id, NOW)

        MAX_CHANNEL_TRIGGERS = config.get("channel_max_triggers_before_lock", DefaultAntiraidSettings.CHANNEL_MAX_TRIGGERS_BEFORE_LOCK)
        channel_triggers_count = len(self.channel_triggers[entry.channel_id])
        if channel_triggers_count >= MAX_CHANNEL_TRIGGERS:
            await self.lock_channel(config, message.channel)

        # If necessary, apply a moderation action to the user
        if action:
            await self.apply_mod_action(user, action, reason)
            if action != ModActionType.BAN:
                PURGE_REASON = "Anti-spam cleanup"
                PURGE_WINDOW = (CHANNELS_SPAM_WINDOW if multi_channel_spam else MSG_SPAM_WINDOW) + 5

                try:
                    deleted_count = 0
                    channels_to_delete = self.get_spam_message(user.id, PURGE_WINDOW, NOW)
                    for channel_id, messages in channels_to_delete.items():
                        deleted_count += len(messages)
                        channel = message.guild.get_channel(int(channel_id))
                        await channel.delete_messages(messages, reason=PURGE_REASON)

                    await (
                        LogBuilder(self.bot, type=MODLOG, color=LogColor.ORANGE)
                        .title(f"{DefaultEmojis.MODERATION} Purge(s) performed")
                        .description(f"Target user: {user.id}\nReason: {PURGE_REASON}\n**{len(channels_to_delete.keys())}** channel(s) | **{deleted_count}** messages")
                        .send()
                    )
                except Exception as e:
                    await (
                        LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                        .title(f"{DefaultEmojis.CRITICAL} Unable to perform a purge")
                        .description(f"Target user: {user.id}\nReason: {PURGE_REASON}\n```\n{e}\n```")
                        .send()
                    )

        # Check if too many events have occurred to trigger a raid alert
        if self.antiraid_current_state.last_alert is None or (discord.utils.utcnow() - self.antiraid_current_state.last_alert).total_seconds() >= ANTIRAID_ALERTS_COOLDOWN_MN * 60:
            channels_currently_locked = len(self.channel_triggers)
            if channels_currently_locked >= 3:
                channel_locks = await self.channels_lock
                await self.trigger_raid_alert(
                    reason=f"{channels_currently_locked} channels currently locked",
                    affected_channels=[self.bot.get_channel(cid) for cid in channel_locks]
                )
                return
            problematic_users = len(set(user_id for user_id in self.user_triggers if len(self.user_triggers[user_id]) >= MAX_USER_TRIGGERS))
            if problematic_users >= 5:
                await self.trigger_raid_alert(reason=f"{channels_currently_locked} users above the detection thresholds")

    # ---------------------------------- lock/unlock channel
    async def lock_channel(self, config: dict, channel: discord.TextChannel):
        lock_duration_mn = config.get("channel_lock_duration_mn", DefaultAntiraidSettings.CHANNEL_LOCK_DURATION_MN)
        lock_until = discord.utils.utcnow() + timedelta(minutes=lock_duration_mn)
        try:
            await channel.send(embed=discord.Embed(
                color=discord.Color.brand_red(),
                title="🔒 Channel locked (spam)",
                description=f"The {channel.mention} channel will be reopened at {discord.utils.format_dt(lock_until)}"
            ))
            await channel.set_permissions(
                channel.guild.default_role, send_messages=False,
                reason=f"Antispam - channel locked for {lock_duration_mn} minutes"
            )
            await self.bot.moderation_storage.set_channel_lock(channel.id, lock_until)
            task = self.bot.loop.create_task(self.unlock_channel(channel.id, lock_until, "Automatic unlock"))
            previous_task = self.unlock_tasks.pop(channel.id, None)
            if previous_task and not previous_task.done():
                previous_task.cancel()
            self.unlock_tasks[channel.id] = task
            task.add_done_callback(lambda t, cid=channel.id: self.unlock_tasks.pop(cid, None))
            await (
                LogBuilder(self.bot, type=MODLOG, color=LogColor.ORANGE)
                .title(f"{DefaultEmojis.MODERATION} Channel {channel.mention} locked")
                .description(f"Auto lock (by anti-spam) until: {discord.utils.format_dt(lock_until)}")
                .send()
            )
        except Exception as e:
            await (
                LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                .title(f"{DefaultEmojis.CRITICAL} Unable to perform a channel lock")
                .description(f"Target channel: {channel.mention}\n```\n{e}\n```")
                .send()
            )

    async def unlock_channel(self, channel_id: int, lock_until: datetime = None, reason: str = None) -> bool:
        if lock_until is not None:
            # If the datetime is in the past, the function will execute instantly
            await discord.utils.sleep_until(when=lock_until)

        self.unlock_tasks.pop(channel_id, None)
        await self.bot.moderation_storage.del_channel_lock(channel_id)
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return False
        try:
            await channel.set_permissions(channel.guild.default_role, reason=reason, send_messages=True)
            await channel.send(embed=discord.Embed(
                color=discord.Color.dark_blue(),
                title="🔓️ Channel unlocked",
                description=(
                    f"The channel {channel.mention} has been reopened" +
                    (f"\n**Reason**: *{reason}*" if reason else '')
                )
            ))
            await (
                LogBuilder(self.bot, type=MODLOG, color=LogColor.ORANGE)
                .title(f"{DefaultEmojis.MODERATION} Channel {channel.mention} unlocked")
                .description(f"> {reason}" if reason else None)
                .send()
            )
            return True
        except Exception as e:
            await (
                LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                .title(f"{DefaultEmojis.CRITICAL} Unable to perform a channel lock")
                .description(f"Target channel: {channel.mention}\n```\n{e}\n```")
                .send()
            )
            return False

    async def apply_mod_action(self, user: discord.Member, action: ModActionType, reason: str = None):
        try:
            if action == ModActionType.TIMEOUT:
                # https://discordpy.readthedocs.io/en/latest/api.html#discord.Member.timeout
                timeout_until = discord.utils.utcnow() + timedelta(minutes=5)
                await user.timeout(timeout_until, reason=reason)
            else:
                if action == ModActionType.KICK:
                    await user.kick(reason=reason)
                elif action == ModActionType.BAN:
                    await user.ban(reason=reason)
                """
                NOTE: There's no need to purge messages here; it will
                be done when they expire via the cleanup loop.

                Furthermore, we retain the triggers until they are deleted in order to keep
                track of the number of actions and use this as a basis for raising alerts.
                """
            await (
                LogBuilder(self.bot, type=MODLOG, color=LogColor.ORANGE)
                .title(f"{DefaultEmojis.MODERATION} Moderation action performed")
                .description((
                    f"Target user: {user.mention if action == ModActionType.TIMEOUT else f"**{user.display_name}** ({user.id})"}\n"
                    f"Moderator action attempted: {action.name}" +
                    (f"\nReason: *{reason}*" if reason else '')
                ))
                .send()
            )
        except Exception as e:
            await (
                LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                .title(f"{DefaultEmojis.CRITICAL} Unable to apply a moderator action")
                .description(f"Target user: {user.mention}\nModerator action attempted: {action.name}{f"\nReason: *{reason}*" if reason else ''}\n```\n{e}\n```")
                .send()
            )

    @commands.command(description="[ADMIN] Allows you to define the value of an antiraid threshold")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def antiraid_set_param(self, ctx: commands.Context, param: str, value: int):
        await ctx.message.delete()
        if await self.bot.moderation_storage.set_antiraid_setting(ctx.author, param, value):
            await ctx.send(content=f"> {DefaultEmojis.CHECK} `{param}` set to the value `{value}`", delete_after=4)
        else:
            await ctx.send(content=f"> {DefaultEmojis.ERROR} Recording failed (does the parameter/value exist?). *See logs for details*.", delete_after=4)

    @commands.command(description="[ADMIN] Resets all settings to default values (antiraid enabled)")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def antiraid_set_default(self, ctx: commands.Context):
        await ctx.message.delete()
        if await self.bot.moderation_storage.set_antiraid_default(ctx.author):
            await ctx.send(content=(
                f"> {DefaultEmojis.CHECK} Anriraid settings reset to default\n"
                f"➜ *To change a specific setting, use `{CMD_PREFIX}antiraid_set_param`: **`param`**, **`value`***\n"
                f"➜ *To view current settings, use `{CMD_PREFIX}view_antiraid_settings`*"
            ), delete_after=4)
        else:
            await ctx.send(content=f"> {DefaultEmojis.ERROR} Default values cannot be used. *See logs for details*.", delete_after=4)

    @commands.command(description="[ADMIN] Display a simple view of the current settings")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def view_antiraid_settings(self, ctx: commands.Context):
        await ctx.message.delete()
        config = await self.config
        if config:
            display = '\n'.join(f"- `{param}`: ***`{value}`***" for param, value in config.items())
            await ctx.author.send(content=f"> {DefaultEmojis.CHECK} Raw list of current parameters\n{display}")
        else:
            await ctx.send(content=f"> {DefaultEmojis.ERROR} Unable to access values.. *See logs for details*.", delete_after=4)

    @app_commands.command(description="[ADMIN] Display the current antiraid system state")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def antiraid_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        state = self.antiraid_current_state
        _config = await self.config
        antiraid_enabled = bool(_config.get("antiraid_enabled", DefaultAntiraidSettings.ANTIRAID_STATE))
 
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=(
            f"### {DefaultEmojis.MODERATION} Antiraid System Status\n"
            f"The antiraid system is currently `{f"{DefaultEmojis.ONLINE} enabled" if antiraid_enabled else f"{DefaultEmojis.OFFLINE} disabled"}`"
            f"\n**Available antiraid commands**:\n{'\n'.join(f"➜ `{CMD_PREFIX}{cmd.name}`: {'\u0020'.join(f"***`{param}`***" for param in cmd.params)}" for cmd in self.get_commands())}"
        )))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(content=(
            f"**Users tracked**: {len(self.user_triggers)}\n"
            f"**Channels tracked**: {len(self.channel_triggers)}\n"
            f"**Logged messages**: {len(self.message_log)}\n"
            f"**Scheduled unlocks**: {len(self.unlock_tasks)}"
        )))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(content=(
            f"**Raid status**: {f"{DefaultEmojis.WARN} Active" if state.active else f"{DefaultEmojis.CHECK} Inactive"}\n" +
            (f"**Latest antiraid alert**: {discord.utils.format_dt(state.last_alert, style='R')}" if state.last_alert else "*No previous alerts*") +
            (f"\n> **Reason**: {state.reason}\n" if state.reason else '')
        )))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(content=(
            f"-# Message retention: {MAX_MESSAGE_LIFESPAN}s | Max messages in buffer: `{MAX_LOG_MESSAGES}`\n"
            f"-# Trigger retention: {MAX_TRIGGER_LIFESPAN}s | Cooldown of antiraid alerts: {ANTIRAID_ALERTS_COOLDOWN_MN}mn"
        )))
        view.add_item(container)
        await interaction.followup.send(view=view, ephemeral=True)

    @app_commands.command(description="[ADMIN] Allows you to unlock a channel for everyone")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    @app_commands.describe(channel="The channel you want to unlock now (by default this one)")
    async def unlock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel]):
        await interaction.response.defer(ephemeral=True)

        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=f"### {DefaultEmojis.MODERATION} Manual unlocking"))

        channel = channel if channel else interaction.channel
        lock_until = await self.bot.moderation_storage.get_channel_lock(channel.id)
        if lock_until is not None:
            container.add_item(discord.ui.TextDisplay(content=f"{channel.mention} has been locked until {discord.utils.format_dt(lock_until)}"))
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.Section(
                discord.ui.TextDisplay(content=f"> Do you want to reopen {channel.mention} now ?"),
                accessory=UnlockButton(self.bot, callback=lambda: self.unlock_channel(channel.id, reason=f"Administrator {interaction.user.mention} manually reopened the channel"))
            ))
        else:
            container.add_item(discord.ui.TextDisplay(content=(
                f"{channel.mention} is not currently locked\n"
                f"*There are currently `{len(self.channel_triggers.get(channel.id, []))}` antispam triggers here.*"
            )))

        view.add_item(container)
        await interaction.followup.send(view=view, ephemeral=True)

async def setup(bot: "RepulsBot"):
    await bot.add_cog(AntiRaidCog(bot))