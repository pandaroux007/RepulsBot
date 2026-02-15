"""
Classic ticket system, opens private channels with moderation.
This can be improved with https://github.com/Rapptz/discord.py/blob/master/examples/modals/report.py

:copyright: (c) 2025-present pandaroux007
:license: MIT, see LICENSE.txt for details.
"""

import discord
from discord.ext import commands
from discord import app_commands
import random
import string
# bot files
from data.cogs import CogsNames
from tools.utils import nl
from tools.log_builder import (
    LogBuilder,
    LogColor,
    BOTLOG
)

from data.constants import (
    IDs,
    DefaultEmojis,
    ASK_HELP,
    ADMIN_CMD
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import RepulsBot

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
            max_length=3000,
            required=True,
            placeholder="Write your ticket here..."
        )
    )
    
    def __init__(self, bot: "RepulsBot"):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        # https://github.com/Rapptz/discord.py/blob/master/examples/modals/label.py#L66
        assert isinstance(self.type.component, discord.ui.Select)
        assert isinstance(self.ticket_title.component, discord.ui.TextInput)
        assert isinstance(self.description.component, discord.ui.TextInput)

        guild = interaction.guild

        # ticket info
        ticket_author = interaction.user
        ticket_title = self.ticket_title.component.value
        ticket_content = self.description.component.value
        ticket_type = self.type.component.values[0]
        ticket_name = self._build_ticket_channel_name(ticket_type)

        # creation of the private channel
        category = discord.utils.get(guild.categories, id=IDs.serverChannel.TICKETS_CATEGORY)
        overwrites = self._build_ticket_overwrites(guild, ticket_author)
        ticket_channel = await guild.create_text_channel(ticket_name, category=category, overwrites=overwrites)
        # first channel's message
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.Section(
            f"### > {ticket_title}\n<@&{IDs.serverRoles.TICKET_HELPER}> {ticket_content}",
            accessory=discord.ui.Thumbnail(media=ticket_author.display_avatar.url)
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(content=f"-# 🎟️ Ticket of type **{self._get_ticket_label(ticket_type)}**・opened by {ticket_author.mention}"))

        view = discord.ui.LayoutView()
        view.add_item(container)
        await ticket_channel.send(view=view)

        # inform the user and log the creation of the ticket
        embed = discord.Embed(
            description=f"{DefaultEmojis.CHECK} Your ticket has been created: {ticket_channel.mention}",
            color=discord.Color.dark_blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=300) # 5 minutes
        log_msg = await (
            LogBuilder(self.bot, type=BOTLOG, color=LogColor.GREEN)
            .title(f"🎟️ New ticket [`{ticket_name}`]({ticket_channel.jump_url}) of type `{self._get_ticket_label(ticket_type)}` created by {ticket_author.mention}")
            .add_field(name="Ticket title", value=f"> {ticket_title}")
            .add_field(name="Description", value=f">>> *{ticket_content if len(ticket_content) <= 400 else ticket_content[:400].strip() + "..."}*")
            .footer(f"Author ID: {ticket_author.id}")
            .send()
        )
        if not await self.bot.tickets_storage.add_ticket(
            name=ticket_name,
            title=ticket_title,
            author=ticket_author.id,
            open_log_url=log_msg.jump_url
        ):
            raise discord.DiscordException("The ticket could not be saved in the database.")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await (
            LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
            .title(f"{DefaultEmojis.ERROR} An error occurred when {interaction.user.mention} tried to create a ticket")
            .description(f"```\n{error}\n```")
            .send()
        )
        await interaction.response.send_message(f"> {DefaultEmojis.ERROR} Oops! Something went wrong...{ASK_HELP}", ephemeral=True)

    def _get_ticket_label(self, type_abbr: str) -> str:
        return next((label for label, _, abbr in TICKET_TYPES if abbr == type_abbr), "Other")

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
        # https://gist.github.com/pythonmcpi/83b95f6e86a8155c07d4ff924967b325#file-example-py-L26
        self.container = discord.ui.Container(accent_color=discord.Color.brand_red())
        self.container.add_item(discord.ui.TextDisplay(content=f"### 🔒 Ticket will be closed in {SECONDS_BEFORE_TICKET_CLOSING}s..."))
        self.container.add_item(discord.ui.Section(
            "You can cancel the closing with the following button",
            accessory=CancelClosingButton(self.callback)
        ))
        self.add_item(self.container)

    async def callback(self, interaction: discord.Interaction):
        self.cancelled = True
        if self.message:
            self.container.clear_items()
            self.container.accent_color = discord.Color.dark_blue()
            self.container.add_item(discord.ui.TextDisplay(content="### 🔓 Ticket closure cancelled\n*You have cancelled the ticket closing.*"))
            await self.message.edit(view=self, delete_after=3)
        else:
            await interaction.response.send_message("Ticket closure cancelled.", ephemeral=True)

        self.stop()

# ---------------------------------- open ticket
# https://github.com/Rapptz/discord.py/blob/master/examples/views/embed_like.py#L39-L73
class OpenTicketButton(discord.ui.ActionRow):
    def __init__(self, bot: "RepulsBot"):
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
    def __init__(self, bot: "RepulsBot"):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_color=discord.Color.dark_blue())
        container.add_item(discord.ui.TextDisplay(content=f"### {OPEN_TICKET_TITLE}"))
        container.add_item(discord.ui.TextDisplay(content=nl(OPEN_TICKET_MSG)))
        container.add_item(discord.ui.Separator())
        container.add_item(OpenTicketButton(bot))
        self.add_item(container)

class TicketsCog(commands.Cog, name=CogsNames.TICKETS):
    def __init__(self, bot: "RepulsBot"):
        self.bot = bot

    @app_commands.command(description="[ADMIN] If launched in a ticket, closes it")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def close_ticket(self, interaction: discord.Interaction, * , reason: str = None):
        if interaction.channel.category_id != IDs.serverChannel.TICKETS_CATEGORY:
            await interaction.response.send_message(f"{DefaultEmojis.ERROR} This command isn't available here. Try again in a ticket!", ephemeral=True)
            return

        view = CancelCloseView()
        await interaction.response.send_message(view=view, ephemeral=True)
        view.message = await interaction.original_response()
        
        await view.wait() # wait view timeout (SECONDS_BEFORE_TICKET_CLOSING)

        if view.cancelled: # cancel closing
            return
        else: # close ticket
            name = interaction.channel.name
            ticket_info = await self.bot.tickets_storage.get_ticket(name)

            log_msg = ticket_info.get("open_log_url")
            title = ticket_info.get("title", "*Unknown*")
            author_id = ticket_info.get("author_id")
            author_mention = f"<@{author_id}>" if author_id else "*Unknown*"

            await (
                LogBuilder(self.bot, type=BOTLOG, color=LogColor.RED)
                .title(f"🎟️ The ticket {f"[`{name}`]({log_msg})" if log_msg else f"`{name}`"} has been closed by {interaction.user.mention}")
                .add_field(name="Ticket Title", value=f"> {title}")
                .add_field(name="Ticket Author", value=author_mention)
                .add_field(name="Reason for closure", value=f"*{reason}*" if reason else "*No reason specified*")
                .send()
            )
            await self.bot.tickets_storage.remove_ticket(name)
            await interaction.channel.delete()

    @app_commands.command(description="[ADMIN] Post the unique ticket creation message")
    @app_commands.guild_only()
    @app_commands.default_permissions(ADMIN_CMD)
    async def setup_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        view = OpenTicketView(self.bot)
        await interaction.channel.send(view=view)
        await interaction.edit_original_response(content=f"{DefaultEmojis.CHECK} Ticket opening message configured!")

async def setup(bot: "RepulsBot"):
    bot.add_view(OpenTicketView(bot))
    await bot.add_cog(TicketsCog(bot))