"""
Classic ticket system, opens private channels with moderation.

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import random
import string
# bot files
from cogs_list import CogsNames
from utils import (
    check_admin_or_roles,
    IS_ADMIN
)

from constants import (
    IDs,
    DefaultEmojis,
    ASK_HELP
)

from log_system import (
    LogColor,
    BOTLOG,
    log
)

SECONDS_BEFORE_TICKET_CLOSING = 4
PERMS_ACCESS_GRANTED = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
AUTHORIZED_MEMBERS = [
    IDs.serverRoles.ADMIN,
    IDs.serverRoles.DEVELOPER,
]

TICKET_TYPES = [
    #     label       |       description         |   abbreviation
    ("In-game report", "Hackers and chat reports", "ing-rep"),
    ("Discord report", "Discord issues/report a member", "dis-rep"),
    ("Role related", "Applications/promotion about roles", "rol"),
    ("Other", "Other inquiries or problems", "other")
]

OPEN_TICKET_TITLE = "🎟️ Need help ? Open a Ticket"
OPEN_TICKET_MSG = """
Simply click on the type of ticket you want to open **in the selector below**, and fill up the information needed (send your images and video after creating the ticket).\n
It will create a private channel between you and **the moderation team**. This way, you can make a report, request a role, or anything else.\n
**Only create a ticket if absolutely necessary!** If you need urgent assistance, please ping or send a DM to an admin. Before creating a ticket, check if the answer to your question is not in the server FAQs (e.g., the requirements for roles are indicated there)! To report a game bug, you can use https://discord.com/channels/603655329120518223/1076163933213311067!
"""

class GoToTicketButton(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.add_item(discord.ui.Button(
            label="Go to your ticket",
            url=channel.jump_url,
            style=discord.ButtonStyle.link
        ))

# ---------------------------------- title and description (modal)
class TicketModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, ticket_type_abbr: str):
        self.ticket_type_abbr = ticket_type_abbr
        self.bot = bot
        super().__init__(title=f"New ticket {self._get_ticket_label()}")
        
        self.title_input = discord.ui.TextInput(
            label="Ticket title",
            max_length=100,
            required=True,
            placeholder="Briefly summarize your issue"
        )
        self.description_input = discord.ui.TextInput(
            label="Describe your issue",
            style=discord.TextStyle.paragraph,
            required=True,
            placeholder="Give as many details as possible"
        )
        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            author = interaction.user

            # creation of the private channel
            category = discord.utils.get(guild.categories, id=IDs.serverChannel.TICKETS_CATEGORY)
            channel_name = self._build_ticket_channel_name()
            overwrites = self._build_ticket_overwrites(guild, author)

            ticket_channel = await guild.create_text_channel(
                channel_name, category=category, overwrites=overwrites,
                topic=f"author_id: {author.id}\ntitle: {self.title_input.value}"
            )

            # first channel's message
            ticket = f"New ticket of type {self._get_ticket_label()}, opened by {author.mention}"
            embed = discord.Embed(
                title=f"{self.title_input.value}",
                description=self.description_input.value,
                color=discord.Color.dark_blue()
            )

            await ticket_channel.send(content=ticket, embed=embed)
            await interaction.response.send_message(
                f"{DefaultEmojis.CHECK} Your ticket has been created: {ticket_channel.mention}",
                view=GoToTicketButton(ticket_channel),
                ephemeral=True,
                delete_after=300 # 5 minutes
            )
            log_msg = await log(
                self.bot, type=BOTLOG, color=LogColor.GREEN,
                title=f"New ticket [`{ticket_channel.name}`]({ticket_channel.jump_url}) of type `{self._get_ticket_label()}` created by {author.mention}.",
                msg=f"Title: **{self.title_input.value}**\n>>> *{self.description_input.value}*"
            )
            await ticket_channel.edit(topic=ticket_channel.topic + f"\nlog_id: {log_msg.jump_url}")
        
        except Exception as error:
            error_msg = "An error occurred while creating the ticket!"
            await log(self.bot, type=BOTLOG, title=error_msg, msg=f"`{error}`")
            await interaction.response.send_message(f":x: {error_msg}{ASK_HELP}", ephemeral=True)

    def _build_ticket_overwrites(self, guild: discord.Guild, author: discord.Member) -> dict:
        # permissions to the bot, ticket author and authorized members to view the private channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: PERMS_ACCESS_GRANTED,
            guild.me: PERMS_ACCESS_GRANTED
        }

        for role_id in AUTHORIZED_MEMBERS:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = PERMS_ACCESS_GRANTED
        return overwrites
    
    # https://stackoverflow.com/questions/7591117/what-is-the-probability-of-collision-with-a-6-digit-random-alphanumeric-code
    def _build_ticket_channel_name(self) -> str:
        code = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{self.ticket_type_abbr.lower()}-{code}"
    
    def _get_ticket_label(self) -> str:
        return next((label for label, _, abbr in TICKET_TYPES if abbr == self.ticket_type_abbr), "Other")

# ---------------------------------- ticket type selector
class TicketTypeSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        options = [
            discord.SelectOption(label=label, value=abbr, description=desc)
            for label, desc, abbr in TICKET_TYPES
        ]
        super().__init__(
            placeholder="Select your ticket type...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="ticket_type_select"
        )

    async def callback(self, interaction: discord.Interaction):
        ticket_type_abbr = self.values[0]
        await interaction.response.send_modal(TicketModal(self.bot, ticket_type_abbr))

class TicketTypeView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect(bot))

# ---------------------------------- cancel closing button
class CancelCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=SECONDS_BEFORE_TICKET_CLOSING)
        self.cancelled: bool = False
        self.message: discord.Message = None

    @discord.ui.button(style=discord.ButtonStyle.danger, label="Cancel closing", emoji="✋")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancelled = True
        if self.message:
            new_embed = discord.Embed(
                title="🔓 Ticket closure cancelled",
                description="You have cancelled the ticket closing.",
                color=discord.Color.dark_blue()
            )
            await self.message.edit(embed=new_embed, view=None)
        else:
            await interaction.response.send_message("Ticket closure cancelled.", ephemeral=True)
        
        self.stop()

# ---------------------------------- tickets cog (see README.md)
class TicketsCog(commands.Cog, name=CogsNames.TICKETS):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------------------------- admin commands
    @app_commands.command(description="If launched in a ticket, closes it", extras={IS_ADMIN: True})
    @check_admin_or_roles()
    async def close_ticket(self, interaction: discord.Interaction, * , reason: str = None):
        if interaction.channel.category and interaction.channel.category.id == IDs.serverChannel.TICKETS_CATEGORY:
            view = CancelCloseView()
            embed = discord.Embed(
                title=f"🔒 Ticket will be closed in {SECONDS_BEFORE_TICKET_CLOSING}s...",
                description="You can cancel with the button below",
                color=discord.Color.brand_red()
            )

            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            view.message = await interaction.original_response()
            
            await view.wait() # wait view timeout (SECONDS_BEFORE_TICKET_CLOSING)

            if view.cancelled: # cancel closing
                await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=SECONDS_BEFORE_TICKET_CLOSING))
                await view.message.delete()
                return
            else: # close ticket
                # https://www.w3schools.com/python/python_ref_string.asp
                topic = interaction.channel.topic or ''
                log_msg, title = None, None
                for line in topic.splitlines():
                    if line.startswith("author_id:"):
                        author_id = int(line.split(':', 1)[1].strip())
                        author_mention = f"<@{author_id}>" if author_id else None
                    elif line.startswith("title:"):
                        title = line.split(':', 1)[1].strip()
                    elif line.startswith("log_id:"):
                        log_msg = line.split(':', 1)[1].strip()
                
                await log(
                    self.bot, type=BOTLOG, color=LogColor.RED,
                    title=f"The ticket {f"[`{interaction.channel.name}`]({log_msg})" if log_msg else f"`{interaction.channel.name}`"} has been closed by {interaction.user.mention}",
                    msg=f"Title: **{title or "Unknown"}**, author: {author_mention if author_mention else "Unknown"}\n{f"Reason: *{reason}*\n" if reason else ''}"
                )
                await interaction.channel.delete()
        else:
            await interaction.response.send_message(f"{DefaultEmojis.ERROR} This command isn't available here. Try again in a ticket!", ephemeral=True)
    
    @commands.command(description="Post the unique ticket creation message", extras={IS_ADMIN: True})
    @check_admin_or_roles()
    async def setup_ticket(self, ctx: commands.Context):
        await ctx.message.delete()
        embed = discord.Embed(
            title=OPEN_TICKET_TITLE,
            description=OPEN_TICKET_MSG,
            color=discord.Color.dark_blue()
        )
        view = TicketTypeView(self.bot)
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    bot.add_view(TicketTypeView(bot))
    await bot.add_cog(TicketsCog(bot))