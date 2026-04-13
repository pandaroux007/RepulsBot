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
    ADMIN_CMD
)

from tools.log_builder import (
    LogBuilder,
    LogColor,
    BOTLOG,
    MODLOG,
    log
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

# ---------------------------------- raid status ui
class MarkAlertAsComplete(discord.ui.Button):
    def __init__(self, parent_view: "RaidStatusView"):
        super().__init__(emoji='🛡️', label="Mark as complete", style=discord.ButtonStyle.danger)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.antiraid.antiraid_current_state.active = False
        await self.parent_view.generate_interface()
        await interaction.response.edit_message(view=self.parent_view)
        await log(
            bot=self.parent_view.antiraid.bot, type=BOTLOG, color=LogColor.ORANGE,
            title=f"{DefaultEmojis.MODERATION} An antiraid alert has been cancelled by {interaction.user.mention}"
        )

class RaidStatusView(discord.ui.LayoutView):
    def __init__(self, parent_cog: "AntiraidCog"):
        super().__init__()
        self.container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        self.add_item(self.container)
        self.antiraid = parent_cog

    async def generate_interface(self):
        self.container.clear_items()

        state = self.antiraid.antiraid_current_state
        channel_locks = await self.antiraid.channels_lock
        _config = await self.antiraid.config
        antiraid_enabled = bool(_config.get("antiraid_enabled", DefaultAntiraidSettings.ANTIRAID_STATE))

        self.container.add_item(discord.ui.TextDisplay(content=(
            f"### {DefaultEmojis.MODERATION} Antiraid System Status\n"
            f"The antiraid system is currently `{f"{DefaultEmojis.ONLINE} enabled" if antiraid_enabled else f"{DefaultEmojis.OFFLINE} disabled"}`"
        )))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.TextDisplay(content=(
            f"**Users tracked**: {len(self.antiraid.user_triggers)}\n"
            f"**Channels tracked**: {len(self.antiraid.channel_triggers)}\n"
            f"**Logged messages**: {len(self.antiraid.message_log)}\n"
            f"**Scheduled unlock(s)**: {len(self.antiraid.unlock_tasks)} | {len(channel_locks)} channel(s) locked"
        )))
        self.container.add_item(discord.ui.Separator())
        raid_status = discord.ui.TextDisplay(content=(
            f"**Raid status**: {f"{DefaultEmojis.WARN} Active" if state.active else f"{DefaultEmojis.CHECK} Inactive"}\n" +
            (f"**Latest antiraid alert**: {discord.utils.format_dt(state.last_alert, style='R')}" if state.last_alert else "*No previous alerts*") +
            (f"\n> **Reason**: {state.reason}\n" if state.reason else '')
        ))
        if state.active:
            self.container.add_item(discord.ui.Section(raid_status, accessory=MarkAlertAsComplete(self)))
        else:
            self.container.add_item(raid_status)
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(discord.ui.TextDisplay(content=(
            f"-# Message retention: {MAX_MESSAGE_LIFESPAN}s | Max messages in buffer: `{MAX_LOG_MESSAGES}`\n"
            f"-# Trigger retention: {MAX_TRIGGER_LIFESPAN}s | Cooldown of antiraid alerts: {ANTIRAID_ALERTS_COOLDOWN_MN}mn"
        )))

        return self

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

class AntiraidCog(commands.Cog, name=CogsNames.ANTIRAID):
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
        await self.bot.wait_until_ready()
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

    # ---------------------------------- handle raid alerts
    async def trigger_raid_alert(self, reason: str, affected_channels: Optional[list[discord.TextChannel]] = None):
        now = discord.utils.utcnow()

        self.antiraid_current_state.active = True
        self.antiraid_current_state.last_alert = now
        self.antiraid_current_state.reason = reason

        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=(
            f"### {DefaultEmojis.CRITICAL} <@&{IDs.serverRoles.ADMIN}> Potential raid detected\n"
            f"**Reason**: *{reason}*\n"
        )))
        if affected_channels:
            display = ", ".join(channel.jump_url for channel in affected_channels)
            container.add_item(discord.ui.TextDisplay(content=f"**Affected channels**\n{display}"))

        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(content=(
            f"-# Next alert available: {discord.utils.format_dt((now + timedelta(minutes=ANTIRAID_ALERTS_COOLDOWN_MN)), 'R')}. "
            f"{DefaultEmojis.WARN} *The system will not return to normal alert status until an admin has completed the raid via the `status` command!*"
        )))

        view.add_item(container)
        log_channel = self.bot.get_partial_messageable(IDs.serverChannel.BOTLOG)
        await log_channel.send(view=view)

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
                    purged_message_ids = set()
                    for channel_id, messages in channels_to_delete.items():
                        deleted_count += len(messages)
                        channel = message.guild.get_channel(int(channel_id))
                        await channel.delete_messages(messages, reason=PURGE_REASON)
                        purged_message_ids.update(msg.id for msg in messages)
                    if purged_message_ids:
                        self.message_log = deque(
                            [msg for msg in self.message_log if msg.message_id not in purged_message_ids],
                            maxlen=MAX_LOG_MESSAGES
                        )

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
            channels_currently_locked = len(self.unlock_tasks)
            if channels_currently_locked:
                if channels_currently_locked >= 2:
                    await self.trigger_raid_alert(
                        reason=f"{channels_currently_locked} channels currently locked",
                        affected_channels=[self.bot.get_channel(cid) for cid in self.unlock_tasks]
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

        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return False
            await channel.set_permissions(channel.guild.default_role, reason=reason, send_messages=True)
            await channel.send(embed=discord.Embed(
                color=discord.Color.dark_blue(),
                title="🔓️ Channel unlocked",
                description=(
                    f"The channel {channel.mention} has been reopened" +
                    (f"\n**Reason**: *{reason}*" if reason else '')
                )
            ))
            self.unlock_tasks.pop(channel_id, None)
            await self.bot.moderation_storage.del_channel_lock(channel_id)
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

    # ---------------------------------- discord commands
    # https://about.abstractumbra.dev/discord.py/2023/01/30/app-command-examples.html#cog-opt
    antiraid = app_commands.Group(
        name="antiraid", guild_only=True, default_permissions=ADMIN_CMD,
        description="[ADMIN] Allows you to manage the entire antiraid system"
    )

    @antiraid.command(description="[ADMIN] Allows you to define the value of an antiraid threshold")
    async def set_param(self, interaction: discord.Interaction, param: str, value: int):
        is_edited = await self.bot.moderation_storage.set_antiraid_setting(interaction.user, param, value)
        if is_edited:
            await interaction.response.send_message(
                content=f"> {DefaultEmojis.CHECK} `{param}` set to the value `{value}`",
                ephemeral=True
            )
            await log(
                bot=self.bot, type=BOTLOG, color=LogColor.ORANGE,
                title=f"{DefaultEmojis.CRITICAL} Modifying an antiraid setting",
                msg=f"Param `{param}` set to the value `{value}` by {interaction.user.mention}"
            )
        else:
            await interaction.response.send_message(
                content=f"> {DefaultEmojis.ERROR} Recording failed (does the parameter/value exist?). *See logs for details*.",
                ephemeral=True
            )

    @antiraid.command(description="[ADMIN] Resets all settings to default values (antiraid enabled)")
    async def reset_default(self, interaction: discord.Interaction):
        if await self.bot.moderation_storage.set_antiraid_default(interaction.user):
            await interaction.response.send_message(content=(
                f"> {DefaultEmojis.CHECK} Anriraid settings reset to default\n"
            ), ephemeral=True)
            await log(
                bot=self.bot, type=BOTLOG, color=LogColor.ORANGE,
                title=f"{DefaultEmojis.CRITICAL} Antiraid setting reset to default values (by {interaction.user.mention})"
            )
        else:
            await interaction.response.send_message(content=f"> {DefaultEmojis.ERROR} Default values cannot be used. *See logs for details*.", ephemeral=True)

    @antiraid.command(description="[ADMIN] Display a simple view of the current settings")
    async def view_settings(self, interaction: discord.Interaction):
        config = await self.config
        if config:
            display = '\n'.join(f"- `{param}`: ***`{value}`***" for param, value in config.items())
            await interaction.response.send_message(content=f"> {DefaultEmojis.CHECK} Raw list of current parameters\n{display}")
        else:
            await interaction.response.send_message(
                content=f"> {DefaultEmojis.ERROR} Unable to access values.. *See logs for details*.",
                ephemeral=True
            )

    @antiraid.command(description="[ADMIN] Display the current antiraid system state")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        view = RaidStatusView(self)
        await view.generate_interface()
        await interaction.followup.send(view=view, ephemeral=True)

    @antiraid.command(description="[ADMIN] Allows you to unlock a channel (this one by default) for everyone")
    async def unlock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel]):
        await interaction.response.defer(ephemeral=True)

        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=f"### {DefaultEmojis.MODERATION} Manual unlocking"))

        channel = channel or interaction.channel
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
    await bot.add_cog(AntiraidCog(bot))