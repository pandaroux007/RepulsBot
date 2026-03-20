import discord
from discord.ext import (
    commands,
    tasks
)

import time
from datetime import (
    timedelta,
    datetime
)

from enum import Enum
from collections import (
    defaultdict,
    deque
)

# bot files
from data.cogs import CogsNames
from data.constants import (
    DefaultAntiraidSettings,
    DefaultEmojis,
    AUTHORIZED_ROLES
)

from tools.log_builder import (
    LogBuilder,
    LogColor,
    BOTLOG
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

# users and channels last a maximum of 1h in the lists
MAXIMUM_ITEM_LIFESPAN = 3600

class ModActionType(Enum):
    TIMEOUT = 1
    KICK = 2
    BAN = 3

class AntiRaidCog(commands.Cog, name=CogsNames.ANTIRAID):
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot
        # https://www.geeksforgeeks.org/python/defaultdict-in-python/
        # https://www.geeksforgeeks.org/python/deque-in-python/
        self.user_messages = defaultdict(lambda: deque(maxlen=100))
        self.channel_triggers = defaultdict(lambda: deque(maxlen=50))
        self.user_triggers = defaultdict(list)

    @property
    async def config(self) -> dict | None:
        return await self.bot.moderation_storage.get_antiraid_settings()

    @property
    async def channel_lock(self) -> dict | None:
        return await self.bot.moderation_storage.load_channel_locks()

    @tasks.loop(minutes=10)
    async def memory_cleanup(self):
        now = time.time()

        inactive_users = [uid for uid, ts in self.user_messages.items()
                        if not ts or now - ts[-1] > MAXIMUM_ITEM_LIFESPAN]
        for uid in inactive_users:
            self.user_messages.pop(uid, None)
            self.user_triggers.pop(uid, None)

        inactive_channels = [cid for cid, ts in self.channel_triggers.items()
                            if not ts or now - ts[-1] > MAXIMUM_ITEM_LIFESPAN]
        for cid in inactive_channels:
            self.channel_triggers.pop(cid, None)

    async def cog_load(self):
        self.memory_cleanup.start()
        channel_locks = await self.channel_lock
        if channel_locks:
            for channel, locked_until in channel_locks.items():
                self.bot.loop.create_task(self.unlock_channel(channel, locked_until, reason="Automatic unlocking"))

    def cog_unload(self):
        self.memory_cleanup.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        config = await self.config
        if message.author.bot or not message.guild or not config or config.get("antiraid_enabled", DefaultAntiraidSettings.ANTIRAID_STATE) == 0:
            return
        if message.author.guild_permissions.administrator or any(role.id in AUTHORIZED_ROLES for role in message.author.roles):
            return

        user = message.author
        user_id = message.author.id
        channel_id = message.channel.id
        msg_time = message.created_at.timestamp()

        # ---------------------------------- user spam
        self.user_messages[user_id].append(msg_time)

        cutoff_user = msg_time - config.get("user_msg_spam_interval_s", DefaultAntiraidSettings.USER_MSG_SPAM_INTERVAL_S)
        while self.user_messages[user_id] and self.user_messages[user_id][0] < cutoff_user:
            self.user_messages[user_id].popleft()

        if len(self.user_messages[user_id]) >= config.get("user_msg_spam_threshold", DefaultAntiraidSettings.USER_MSG_SPAM_THRESHOLD):
            """
            If a member recently joined triggers the anti-spam and sends links/images,
            it will be immediately banned due to suspicious behavior.
            """
            is_recently_joined = ((discord.utils.utcnow() - message.author.joined_at) < timedelta(days=3))
            is_new_account = ((discord.utils.utcnow() - message.author.created_at) < timedelta(weeks=1))
            has_links_or_images = (bool(message.attachments) or "http" in message.content.lower())
            if is_recently_joined and has_links_or_images:
                await self.apply_mod_action(user, ModActionType.BAN, reason="New suspicious account (sending image/link)")

            """
            Otherwise, if it is simply spam, we delete + timeout (if too many times in too short a time,
            we launch a moderation action (kick/ban) on the user, depending on their seniority).
            """
            now = time.time()
            self.user_triggers[user_id].append(now)
            self.user_triggers[user_id] = [t for t in self.user_triggers[user_id] if now - t <= 1800]  # 30mn
            spam_repeat = len(self.user_triggers[user_id])

            if spam_repeat >= config.get("user_max_repeat_before_mod", DefaultAntiraidSettings.USER_MAX_TRIGGERS_BEFORE_MOD):
                if is_recently_joined or is_new_account:
                    await self.apply_mod_action(user, ModActionType.BAN, reason=f"New user/member + spam repeated {spam_repeat} times")
                else:
                    await self.apply_mod_action(user, ModActionType.KICK, reason=f"Spam repeated {spam_repeat} times")
            else:
                await message.channel.send(f"> 🚫 {message.author.mention} You sent messages too quickly!", delete_after=4)
                await self.apply_mod_action(user, ModActionType.TIMEOUT, reason=f"Spam repeated {spam_repeat} times")

            def is_spam_message(m: discord.Message) -> bool:
                return (
                    m.author.id == user_id and
                    (now - m.created_at.timestamp()) <= config.get("user_msg_spam_interval_s", DefaultAntiraidSettings.USER_MSG_SPAM_INTERVAL_S) + 5
                )
            await message.channel.purge(limit=20, oldest_first=True, check=is_spam_message, reason="Anti-spam user")
            self.user_messages.pop(user_id, None)

            # ---------------------------------- channel spam
            """
            If too much spam is detected in a channel, it is locked.
            """
            self.channel_triggers[channel_id].append(msg_time)

            cutoff_channel = msg_time - config.get("channel_triggers_interval_s", DefaultAntiraidSettings.CHANNEL_TRIGGERS_INTERVAL_S)
            while self.channel_triggers[channel_id] and self.channel_triggers[channel_id][0] < cutoff_channel:
                self.channel_triggers[channel_id].popleft()

            if len(self.channel_triggers[channel_id]) >= config.get("channel_max_triggers_before_lock", DefaultAntiraidSettings.CHANNEL_MAX_TRIGGERS_BEFORE_LOCK):
                await self.lock_channel(config, message.channel)

    async def lock_channel(self, config: dict, channel: discord.TextChannel):
        lock_duration_mn = config.get("channel_lock_duration_mn", DefaultAntiraidSettings.CHANNEL_LOCK_DURATION_MN)
        lock_until = discord.utils.utcnow() + timedelta(minutes=lock_duration_mn)
        await channel.send(embed=discord.Embed(
            color=discord.Color.brand_red(),
            title="🔒 Channel locked (spam)",
            description=f"The {channel.mention} channel will be reopened at {discord.utils.format_dt(lock_until)}"
        ))
        await channel.set_permissions(
            channel.guild.default_role, send_messages=False,
            reason=f"Antispam - channel locked for {lock_duration_mn} minutes"
        )
        await self.bot.moderation_storage.set_channel_lock(channel.id, lock_duration_mn)

    async def unlock_channel(self, channel_id: int, lock_until: datetime = None, reason: str = None):
        if lock_until is not None:
            await discord.utils.sleep_until(when=lock_until)

        await self.bot.moderation_storage.del_channel_lock(channel_id)
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        await channel.set_permissions(channel.guild.default_role, reason=reason, send_messages=True)
        await channel.send(embed=discord.Embed(
            color=discord.Color.brand_red(),
            title=f"🔓️ Channel unlocked ({reason if reason else ''})",
            description=f"The channel {channel.mention} has been reopened (reason: *{reason}*)"
        ))

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
                self.user_messages.pop(user.id, None)
                self.user_triggers.pop(user.id, None)
        except Exception as e:
            await (
                LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                .title(f"{DefaultEmojis.CRITICAL} Unable to apply a moderator action")
                .description(f"Target user: {user.id}\nModerator action attempted: {action.name}{f"\nReason: *{reason}*" if reason else ''}\n```\n{e}\n```")
                .send()
            )

async def setup(bot: "RepulsBot"):
    await bot.add_cog(AntiRaidCog(bot))