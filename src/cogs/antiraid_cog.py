"""
Just an automated system for managing idiots
who want to mess with the server

:copyright: (c) 2026-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
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
    DefaultEmojis
)

from tools.log_builder import (
    LogBuilder,
    LogColor,
    BOTLOG,
    MODLOG
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

MAX_MESSAGE_LIFESPAN = 60 # 1mn
MAX_TRIGGER_DURATION = 900 # 15mn
MAX_LOG_MESSAGES = 5000

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
    trigger_count: int = 0
    reason: str | None = None

class AntiRaidCog(commands.Cog, name=CogsNames.ANTIRAID):
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot
        self.antiraid_current_state = AntiraidState()
        # https://www.geeksforgeeks.org/python/defaultdict-in-python/
        # https://www.geeksforgeeks.org/python/deque-in-python/
        self.message_log: deque[LoggedMessage] = deque(maxlen=MAX_LOG_MESSAGES)
        self.user_triggers = defaultdict(deque)
        self.channel_triggers = defaultdict(deque)
        self.unlock_tasks: set[asyncio.Task] = set()

    # ---------------------------------- utility functions
    @property
    async def config(self) -> dict | None:
        return await self.bot.moderation_storage.get_antiraid_settings()

    @tasks.loop(seconds=60)
    async def memory_cleanup(self):
        print("ANTIRAID > memory_cleanup")
        NOW = time.time()

        for user_id in list(self.user_triggers.keys()):
            dq = self.user_triggers[user_id]
            print(f"ANTIRAID > memory cleanup: user {user_id} | {dq}")
            while dq and NOW - dq[0] > MAX_TRIGGER_DURATION:
                print(f"ANTIRAID > trigger cleaned (user {user_id}, {len(dq)} triggers)")
                dq.popleft()
            if not dq:
                print(f"ANTIRAID > triggers entry for user {user_id} deleted")
                del self.user_triggers[user_id]

        for channel_id in list(self.channel_triggers.keys()):
            dq = self.channel_triggers[channel_id]
            print(f"ANTIRAID > memory cleanup: channel {channel_id} | {dq}")
            while dq and NOW - dq[0] > MAX_TRIGGER_DURATION:
                print(f"ANTIRAID > trigger cleaned (channel {channel_id}, {len(dq)} triggers)")
                dq.popleft()
            if not dq:
                print(f"ANTIRAID > triggers entry for channel {channel_id} deleted")
                del self.channel_triggers[channel_id]

        message_cleaned_count = 0
        while self.message_log and (NOW - self.message_log[0].timestamp) > MAX_MESSAGE_LIFESPAN:
            self.message_log.popleft()
            message_cleaned_count += 1
        print(f"ANTIRAID > {message_cleaned_count} messages cleaned")

    async def cog_load(self):
        print("ANTIRAID > cog_load")
        channel_locks = await self.bot.moderation_storage.load_channel_locks()
        if channel_locks:
            now = discord.utils.utcnow()
            for channel_id, locked_until in channel_locks.items():
                task = self.bot.loop.create_task(
                    self.unlock_channel(channel_id, locked_until, "Expired lock on restart" if (now >= locked_until) else "Automatic unlocking")
                )
                self.unlock_tasks.add(task)
                task.add_done_callback(lambda t: self.unlock_tasks.discard(t))

        self.memory_cleanup.start()

    def cog_unload(self):
        print("ANTIRAID > cog_unload")
        self.memory_cleanup.cancel()

        for task in self.unlock_tasks:
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
        print(f"ANTIRAID > get_user_messages performed on {len(messages)} messages")
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
        print(f"ANTIRAID > get_channel_messages performed on {len(messages)} messages")
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
        while dq and now - dq[0] > MAX_TRIGGER_DURATION:
            dq.popleft()
        print(f"ANTIRAID > trigger added for user {user_id} (total {len(dq)}): {dq}")
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
        while dq and now - dq[0] > MAX_TRIGGER_DURATION:
            dq.popleft()
        print(f"ANTIRAID > trigger added for channel {channel_id} (total {len(dq)}): {dq}")
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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        config = await self.config
        user = message.author

        if user.bot or not message.guild or not config or config.get("antiraid_enabled", DefaultAntiraidSettings.ANTIRAID_STATE) == 0:
            return
        # if user.guild_permissions.administrator or any(role.id in AUTHORIZED_ROLES for role in user.roles):
        #     return

        print(f"ANTIRAID > start handling message {message.jump_url}")
        start_time = time.perf_counter()
        NOW = time.time()
        is_recently_joined = False # bool(isinstance(user, discord.Member) and (discord.utils.utcnow() - user.joined_at) < timedelta(days=3))
        is_new_account = False # bool((discord.utils.utcnow() - user.created_at) < timedelta(weeks=1))

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
            print(f"ANTIRAID > burst_spam detected for user {user.id}")
            burst_spam = True

        # Rapid spamming between multiple channels
        CHANNELS_SPAM_THRESHOLD = config.get("user_channel_spam_threshold", DefaultAntiraidSettings.USER_CHANNEL_SPAM_THRESHOLD)
        CHANNELS_SPAM_WINDOW = config.get("user_channel_spam_interval_s", DefaultAntiraidSettings.USER_CHANNEL_SPAM_INTERVAL_S)
        user_channel_count = len(set(msg.channel_id for msg in self.get_user_messages(entry.user_id, CHANNELS_SPAM_WINDOW, NOW)))
        if user_channel_count >= CHANNELS_SPAM_THRESHOLD:
            print(f"ANTIRAID > multi_channel_spam detected for user {user.id}")
            multi_channel_spam = True

        if burst_spam or multi_channel_spam:
            user_triggers = self.add_user_trigger(entry.user_id, NOW) if not trigger_recorded else len(self.user_triggers[entry.user_id])
            trigger_recorded = True
            MAX_USER_TRIGGERS = config.get("user_max_triggers_before_mod", DefaultAntiraidSettings.USER_MAX_TRIGGERS_BEFORE_MOD)

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
            print(f"ANTIRAID > spam in channel {entry.channel_id} detected")
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
                        LogBuilder(self.bot, type=BOTLOG, color=LogColor.ORANGE)
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
        print(f"ANTIRAID > end handling message {message.jump_url} ({time.perf_counter() - start_time:.4f}s)")

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
            task = self.bot.loop.create_task(
                self.unlock_channel(channel.id, lock_until, "Automatic unlock")
            )
            self.unlock_tasks.add(task)
            task.add_done_callback(lambda t: self.unlock_tasks.discard(t))
            await (
                LogBuilder(self.bot, type=MODLOG, color=LogColor.ORANGE)
                .title(f"{DefaultEmojis.MODERATION} Channel {channel.mention} locked")
                .description(f"Auto lock (by anti-spam) until: {discord.utils.format_dt(lock_until)}")
                .send()
            )
            print(f"ANTIRAID > locked {channel.jump_url}")
        except Exception as e:
            await (
                LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                .title(f"{DefaultEmojis.CRITICAL} Unable to perform a channel lock")
                .description(f"Target channel: {channel.mention}\n```\n{e}\n```")
                .send()
            )

    async def unlock_channel(self, channel_id: int, lock_until: datetime = None, reason: str = None):
        if lock_until is not None:
            # If the datetime is in the past, the function will execute instantly
            await discord.utils.sleep_until(when=lock_until)

        await self.bot.moderation_storage.del_channel_lock(channel_id)
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        try:
            await channel.set_permissions(channel.guild.default_role, reason=reason, send_messages=True)
            await channel.send(embed=discord.Embed(
                color=discord.Color.dark_blue(),
                title=f"🔓️ Channel unlocked ({reason if reason else ''})",
                description=f"The channel {channel.mention} has been reopened (reason: *{reason}*)"
            ))
            await (
                LogBuilder(self.bot, type=MODLOG, color=LogColor.ORANGE)
                .title(f"{DefaultEmojis.MODERATION} Channel {channel.mention} unlocked")
                .send()
            )
        except Exception as e:
            await (
                LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                .title(f"{DefaultEmojis.CRITICAL} Unable to perform a channel lock")
                .description(f"Target channel: {channel.mention}\n```\n{e}\n```")
                .send()
            )

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
                self.user_triggers.pop(user.id, None)
                """
                NOTE: There's no need to purge messages here; it will
                be done when they expire via the cleanup loop.
                """
            print(f"ANTIRAID > mod action applied on {user.id} (reason: {reason}) {action.name}")
        except Exception as e:
            await (
                LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                .title(f"{DefaultEmojis.CRITICAL} Unable to apply a moderator action")
                .description(f"Target user: {user.id}\nModerator action attempted: {action.name}{f"\nReason: *{reason}*" if reason else ''}\n```\n{e}\n```")
                .send()
            )

async def setup(bot: "RepulsBot"):
    await bot.add_cog(AntiRaidCog(bot))