import discord
from discord.ext import commands
from typing import Self
# bot file
from constants import IDs

MODLOG = True
BOTLOG = False

class LogColor:
    BLUE = discord.Color.blue()
    RED = discord.Color.red()
    GREEN = discord.Color.green()
    ORANGE = discord.Color.orange()

class LogBuilder:
    def __init__(self, bot: commands.Bot, type: bool = MODLOG, color: discord.Color = LogColor.BLUE):
        self.bot = bot
        self.logtype = type
        self.embed = discord.Embed(color=color, timestamp=discord.utils.utcnow())
        self._markdown_title = None
        self._description = None
        self._files = None

    def title(self, text: str = "", url: str = None) -> Self:
        """ adds a title to the embed with url option (doesn't support markdown) """
        self.embed.title = text
        self.embed.url = url
        return self

    def m_title(self, text: str | None, with_line_break: bool = True) -> Self:
        """ adds a title to the top of the description (supports markdown) """
        if text is not None:
            self._markdown_title = f"**{text}**{'\n' if with_line_break else ''}"
        return self

    def description(self, desc: str | None) -> Self:
        """ set the log embed description (supports markdown) """
        self._description = desc
        return self

    def footer(self, text: str, icon_url: str = None) -> Self:
        self.embed.set_footer(text=text, icon_url=icon_url)
        return self

    def author(self, name: str, author_url: str = None, icon_url: str = None) -> Self:
        self.embed.set_author(name=name, url=author_url, icon_url=icon_url)
        return self

    def add_field(self, name: str, value: str | None, inline: bool = False) -> Self:
        """ create a new field (max 25 on an embed) (title doesn't support markdown) """
        self.embed.add_field(name=name, value=value or "", inline=inline)
        return self
    
    def add_files(self, files: list[discord.File] | discord.File):
        """ attach one or more files to the log message """
        self._files = files
        return self

    async def send(self) -> discord.Message | None:
        log_channel = self.bot.get_channel(IDs.serverChannel.BOTLOG if self.logtype == BOTLOG else IDs.serverChannel.MODLOG)
        if log_channel is not None:
            desc = ""
            if self._markdown_title:
                desc += self._markdown_title
            if self._description:
                desc += self._description
            self.embed.description = desc
            return await log_channel.send(embed=self.embed, files=self._files, silent=True, allowed_mentions=discord.AllowedMentions.none())
        else:
            return None
        
# kept for compatibility
async def log(bot: commands.Bot, title: str, msg: str = "", type: bool = MODLOG, color: discord.Color = LogColor.BLUE) -> discord.Message | None:
    return await LogBuilder(bot, type=type, color=color).m_title(title).description(msg).send()