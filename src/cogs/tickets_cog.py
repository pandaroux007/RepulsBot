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
    nl,
    ADMIN_CMD
)

from constants import (
    IDs,
    DefaultEmojis,
    ASK_HELP
)

from log_system import (
    LogBuilder,
    LogColor,
    BOTLOG
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
Before creating a new ticket, make sure your question isn't answered **in the FAQs** (for example, if role requirements are listed there).
**To report a bug, use the https://discord.com/channels/603655329120518223/1076163933213311067 channel**.

Tickets should only be used **for non-urgent questions or requests**. In cases of true urgency, send a DM or ping the admins instead.
However, you should only create a ticket if absolutely necessary!

>>> **To open a new ticket**, simply click the button below and fill in the information.
A private channel will be created between you and the moderation team.
You can report an issue, a member, request a role, or take any other action.
You will likely be asked for proof, so **send your images and videos after creating the ticket**.
"""

# ---------------------------------- writing and creating the ticket
class GoToTicketButton(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.add_item(discord.ui.Button(
            label="Go to your ticket",
            url=channel.jump_url,
            style=discord.ButtonStyle.link
        ))

# https://github.com/Rapptz/discord.py/blob/master/examples/modals/label.py
# https://discord.com/developers/docs/components/using-modal-components
class TicketModal(discord.ui.Modal, title="Create a new ticket"):
    type = discord.ui.Label(
        text="Ticket type",
        description="Select the type of ticket you are opening",
        component=discord.ui.Select(
            options = [
                discord.SelectOption(label=label, value=abbr, description=desc)
                for label, desc, abbr in TICKET_TYPES
            ],
            placeholder="Choose...",
            min_values=1, max_values=1
        )
    )
    ticket_title = discord.ui.Label(
        text="Ticket title",
        component=discord.ui.TextInput(
            max_length=100,
            required=True,
            placeholder="Briefly summarize your issue..."
        )
    )
    description = discord.ui.Label(
        text="Describe your issue",
        description="Please provide as much detail as possible!",
        component=discord.ui.TextInput(
            style=discord.TextStyle.paragraph,
            required=True,
            placeholder="Write your ticket here..."
        )
    )
    
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        # https://github.com/Rapptz/discord.py/blob/master/examples/modals/label.py#L66
        assert isinstance(self.type.component, discord.ui.Select)
        assert isinstance(self.ticket_title.component, discord.ui.TextInput)
        assert isinstance(self.description.component, discord.ui.TextInput)

        guild = interaction.guild
        author = interaction.user

        # ticket info
        ticket_title = self.ticket_title.component.value
        ticket_content = self.description.component.value
        ticket_type = self.type.component.values[0]

        # creation of the private channel
        category = discord.utils.get(guild.categories, id=IDs.serverChannel.TICKETS_CATEGORY)
        channel_name = self._build_ticket_channel_name(ticket_type)
        overwrites = self._build_ticket_overwrites(guild, author)

        ticket_channel = await guild.create_text_channel(
            channel_name, category=category, overwrites=overwrites,
            topic=f"author_id: {author.id}\ntitle: {ticket_title}"
        )

        # first channel's message
        header = f"> <@&{IDs.serverRoles.TICKET_HELPER}> New ticket of type **{self._get_ticket_label(ticket_type)}**, opened by {author.mention}"
        ticket = discord.Embed(
            title=ticket_title,
            description=ticket_content,
            color=discord.Color.dark_blue()
        )

        await ticket_channel.send(content=header, embed=ticket)
        await interaction.response.send_message(
            f"{DefaultEmojis.CHECK} Your ticket has been created: {ticket_channel.mention}",
            view=GoToTicketButton(ticket_channel),
            ephemeral=True,
            delete_after=300 # 5 minutes
        )
        log_msg = await (
            LogBuilder(self.bot, type=BOTLOG, color=LogColor.GREEN)
            .title(f"🎟️ New ticket [`{ticket_channel.name}`]({ticket_channel.jump_url}) of type `{self._get_ticket_label(ticket_type)}` created by {author.mention}")
            .add_field(name="Ticket title", value=f"> {ticket_title}")
            .add_field(name="Description", value=f">>> *{ticket_content}*")
            .footer(f"Author ID: {author.id}")
            .send()
        )
        await ticket_channel.edit(topic=ticket_channel.topic + f"\nlog_id: {log_msg.jump_url}")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await (
            LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
            .title(f"{DefaultEmojis.ERROR} An error occurred when {interaction.user.mention} tried to create a ticket")
            .description(f"```\n{error}\n```")
            .send()
        )
        await interaction.response.send_message(f"> {DefaultEmojis.ERROR} Oops! Something went wrong...{ASK_HELP}", ephemeral=True)

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
    
    def _build_ticket_channel_name(self, type_abbr: str) -> str:
        # https://stackoverflow.com/questions/7591117/what-is-the-probability-of-collision-with-a-6-digit-random-alphanumeric-code
        code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{type_abbr.lower()}-{code}"
    
    def _get_ticket_label(self, type_abbr: str) -> str:
        return next((label for label, _, abbr in TICKET_TYPES if abbr == type_abbr), "Other")

# ---------------------------------- closing and cancel closing view
class CancelClosingButton(discord.ui.Button):
    def __init__(self, callback: callable):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Cancel closing",
            emoji="✋"
        )
        self.callback_func = callback

    async def callback(self, interaction: discord.Interaction):
        await self.callback_func(interaction)

class CancelCloseView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=SECONDS_BEFORE_TICKET_CLOSING)
        self.cancelled = False
        self.message: discord.Message = None
        self.button = CancelClosingButton(self.callback)
        # https://gist.github.com/pythonmcpi/83b95f6e86a8155c07d4ff924967b325#file-example-py-L26
        self.container = discord.ui.Container(accent_color=discord.Color.brand_red())
        self.container.add_item(discord.ui.TextDisplay(content=f"### 🔒 Ticket will be closed in {SECONDS_BEFORE_TICKET_CLOSING}s..."))
        section = discord.ui.Section(
            "You can cancel the closing with the following button",
            accessory=self.button
        )
        self.container.add_item(section)
        self.add_item(self.container)

    async def callback(self, interaction: discord.Interaction):
        self.cancelled = True
        if self.message:
            self.container.clear_items()
            self.container.accent_color = discord.Color.dark_blue()
            self.container.add_item(discord.ui.TextDisplay(content="### 🔓 Ticket closure cancelled\n*You have cancelled the ticket closing.*"))
            await self.message.edit(view=self)
        else:
            await interaction.response.send_message("Ticket closure cancelled.", ephemeral=True)

        self.stop()

# ---------------------------------- open ticket
# https://github.com/Rapptz/discord.py/blob/master/examples/views/embed_like.py#L39-L73
class OpenTicketButton(discord.ui.ActionRow):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(
        style=discord.ButtonStyle.secondary,
        emoji="🎟️",
        label="Click here to open a new ticket",
        custom_id="open_ticket"
    )
    async def new_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal(self.bot))

class OpenTicketView(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=f"### {OPEN_TICKET_TITLE}"))
        container.add_item(discord.ui.TextDisplay(content=nl(OPEN_TICKET_MSG)))
        container.add_item(discord.ui.Separator())
        container.add_item(OpenTicketButton(bot))
        self.add_item(container)

# ---------------------------------- tickets cog (see README.md)
class TicketsCog(commands.Cog, name=CogsNames.TICKETS):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------------------------- admin commands
    @app_commands.command(description="If launched in a ticket, closes it", extras={ADMIN_CMD: True})
    @check_admin_or_roles()
    async def close_ticket(self, interaction: discord.Interaction, * , reason: str = None):
        if interaction.channel.category and interaction.channel.category.id == IDs.serverChannel.TICKETS_CATEGORY:
            view = CancelCloseView()
            await interaction.response.send_message(view=view, ephemeral=True)
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
                
                await (
                    LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                    .title(f"🎟️ The ticket {f"[`{interaction.channel.name}`]({log_msg})" if log_msg else f"`{interaction.channel.name}`"} has been closed by {interaction.user.mention}")
                    .add_field(name="Ticket Title", value=f"> {title or "*Unknown*"}")
                    .add_field(name="Ticket Author", value=author_mention if author_mention else "*Unknown*")
                    .add_field(name="Reason for closure", value=f"*{reason}*" if reason else '')
                    .send()
                )
                await interaction.channel.delete()
        else:
            await interaction.response.send_message(f"{DefaultEmojis.ERROR} This command isn't available here. Try again in a ticket!", ephemeral=True)
    
    @commands.command(description="Post the unique ticket creation message", extras={ADMIN_CMD: True})
    @check_admin_or_roles()
    async def setup_ticket(self, ctx: commands.Context):
        await ctx.message.delete()
        view = OpenTicketView(self.bot)
        await ctx.send(view=view)

async def setup(bot: commands.Bot):
    bot.add_view(OpenTicketView(bot))
    await bot.add_cog(TicketsCog(bot))