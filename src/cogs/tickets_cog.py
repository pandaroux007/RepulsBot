import discord
from discord.ext import commands
from datetime import timedelta
import random
import string
# bot files
from utils import send_hidden_message
from constants import (
    CogsNames,
    ServerRoleIDs,
    DefaultEmojis,
    OPEN_TICKET_MSG,
)

SECONDS_BEFORE_TICKET_CLOSING = 3
PERMS_ACCESS_GRANTED = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
AUTHORIZED_MEMBERS = [
    ServerRoleIDs.ADMIN,
    ServerRoleIDs.DEVELOPER,
    ServerRoleIDs.CONTRIBUTOR
]

TICKETS_CATEGORY_NAME = "Tickets"
TICKET_TYPES = [
    ("In-game assistance", "Get help with gameplay issues", "Ing.A"),
    ("Make a report", "Report a player or server behavior", "Rep"),
    ("Role related", "Request or report issues with roles", "Rol"),
    ("Other", "Other inquiries or problems", "Other")
]

# ---------------------------------- title and description (modal)
class TicketModal(discord.ui.Modal):
    def __init__(self, ticket_type_label: str):
        super().__init__(title=f"New ticket: {ticket_type_label}")
        self.ticket_type_label = ticket_type_label
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
        guild = interaction.guild
        author = interaction.user

        # permissions to the ticket author and authorized members to view the private channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: PERMS_ACCESS_GRANTED,
        }
        for role_id in AUTHORIZED_MEMBERS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = PERMS_ACCESS_GRANTED

        # creation of the private channel
        category = await self._get_tickets_category(guild=guild)
        channel_name = self._make_ticket_channel_name(ticket_type=self.ticket_type_label)

        ticket_channel = await guild.create_text_channel(
            channel_name, category=category, overwrites=overwrites,
            topic=f"Ticket by {author} ・ **{self.ticket_type_label}** ・ {self.title_input.value}"
        )

        # first channel's message
        embed = discord.Embed(
            title=f"🎟️ {self.title_input.value}",
            description=self.description_input.value,
            color=discord.Color.dark_blue()
        )
        embed.set_footer(text=f"Ticket type ・ {self.ticket_type_label}")

        await ticket_channel.send(content=f"Opened by {author.mention}", embed=embed)
        await interaction.response.send_message(f"✅ Your ticket has been created: {ticket_channel.mention}", ephemeral=True)

    async def _get_tickets_category(self, guild: discord.Guild):
        category = discord.utils.get(guild.categories, name=TICKETS_CATEGORY_NAME)
        if category:
            return category
        else:
            overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
            return await guild.create_category(TICKETS_CATEGORY_NAME, overwrites=overwrites)
    
    # https://stackoverflow.com/questions/7591117/what-is-the-probability-of-collision-with-a-6-digit-random-alphanumeric-code
    def _make_ticket_channel_name(self, ticket_type: str):
        abbr = next((abbr for label, _, abbr in TICKET_TYPES if label == ticket_type), "Other")
        code = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{abbr.lower()}-{code}"

# ---------------------------------- ticket type selector
class TicketTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, value=label, description=desc)
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
        ticket_type_label = self.values[0]
        await interaction.response.send_modal(TicketModal(ticket_type_label))

class TicketTypeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

# ---------------------------------- tickets cog (see README.md)
class TicketsCog(commands.Cog, name=CogsNames.TICKETS):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="open_ticket", description="Opens the menu to create a ticket")
    async def open_ticket(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎟️ Open a Ticket",
            description=OPEN_TICKET_MSG,
            color=discord.Color.dark_blue()
        )
        view = TicketTypeView()
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @commands.hybrid_command(name="close_ticket", description="Close current ticket (only available in a ticket)")
    async def close_ticket(self, ctx: commands.Context):
        if ctx.channel.category and ctx.channel.category.name == TICKETS_CATEGORY_NAME:
            await ctx.send(f"🔒 Ticket will be closed in {SECONDS_BEFORE_TICKET_CLOSING}s...", ephemeral=True)
            await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=SECONDS_BEFORE_TICKET_CLOSING))
            await ctx.channel.delete()
        else:
            await send_hidden_message(ctx=ctx, text=f"{DefaultEmojis.ERROR} This command isn't available here. Try again in a ticket!")
    
    # ---------------------------------- admin command
    @commands.hybrid_command(name="setup_ticket", description="Post the unique ticket creation message (admin only)")
    @commands.has_permissions(administrator=True)
    async def setup_ticket(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎟️ Open a Ticket",
            description=OPEN_TICKET_MSG,
            color=discord.Color.dark_blue()
        )
        view = TicketTypeView()
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    bot.add_view(TicketTypeView())
    await bot.add_cog(TicketsCog(bot))