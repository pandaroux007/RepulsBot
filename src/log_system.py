import discord
from discord.ext import commands
from typing import Self
# bot file
from constants import IDs

MODLOG = True # Log restricted to admins for server moderation
BOTLOG = False # Logs of the bot for debugging without access restrictions

class LogColor:
    BLUE = discord.Color.blue()
    RED = discord.Color.red()
    GREEN = discord.Color.green()
    ORANGE = discord.Color.orange()

class LogBuilder:
    def __init__(self, bot: commands.Bot, type: bool = MODLOG, color: discord.Color = LogColor.BLUE):
        """
        All text (titles, footer, fields, etc.) in the logs supports markdown.
        Each builder function returns the class instance to allow for fluent-style chaining.
        """
        self.bot = bot
        self.logtype = type
        self.color = color
        # log data
        self._title = None
        self._description = None
        self._footer = None
        self._fields = []
        self._mediatitle = None
        self._mediafiles = []

    def title(self, text: str) -> Self:
        self._title = text
        return self

    def description(self, desc: str | None) -> Self:
        self._description = desc
        return self

    def footer(self, text: str = '') -> Self:
        self._footer = text
        return self

    def add_field(self, name: str, value: str | None) -> Self:
        self._fields.append((name, value or ''))
        return self
    
    def add_media(self, title: str, files: list[discord.File] | discord.File = None) -> Self:
        """
        support for images (jpg, png, gif, webm, etc.)
        """
        # https://stackoverflow.com/questions/252703/what-is-the-difference-between-pythons-list-methods-append-and-extend
        if files:
            if type(files) is list:
                self._mediafiles.extend(files)
            else:
                self._mediafiles.append(files)
        self._mediatitle = title
        return self

    async def send(self) -> discord.Message | None: 
        log_channel = self.bot.get_channel(IDs.serverChannel.BOTLOG if self.logtype == BOTLOG else IDs.serverChannel.MODLOG)
        if not log_channel:
            return None
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_color = self.color)

        if self._title:
            container.add_item(discord.ui.TextDisplay(content=f"### {self._title}"))

        if self._description:
            container.add_item(discord.ui.TextDisplay(content=self._description))
            container.add_item(discord.ui.Separator())

        if self._fields:
            field = ""
            for name, value in self._fields:
                field += f"**{name}**\n{f"{value}\n" if value else ''}\n"
            container.add_item(discord.ui.TextDisplay(content=field.strip()))
            container.add_item(discord.ui.Separator())

        media_items = []
        for file in self._mediafiles:
            media_items.append(discord.MediaGalleryItem(media=file))
        if media_items:
            container.add_item(discord.ui.TextDisplay(content=f"**{self._mediatitle}**"))
            container.add_item(discord.ui.MediaGallery(*media_items))
            container.add_item(discord.ui.Separator())

        footer = f"*{self._footer}* ・ " if self._footer else '' # "・" char is U+30FB ("Katakana middle dot")
        container.add_item(discord.ui.TextDisplay(content=f"-# {footer}{discord.utils.format_dt(discord.utils.utcnow(), 'F')}"))

        view.add_item(container)
        return await log_channel.send(view=view, files=self._mediafiles, silent=True, allowed_mentions=discord.AllowedMentions.none())

# kept for compatibility
async def log(bot: commands.Bot, title: str, msg: str = '', type: bool = MODLOG, color: discord.Color = LogColor.BLUE) -> discord.Message | None:
    return await LogBuilder(bot, type=type, color=color).title(title).description(msg).send()