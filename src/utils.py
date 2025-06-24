import aiohttp
import discord
from discord.ext import commands
# bot file
from constants import *

# ---------------------------------- check decorator and hidden msg function
def check_admin_or_roles():
    async def predicate(ctx: commands.Context):
        has_admin = ctx.author.guild_permissions.administrator
        allowed_role_ids = {ADMIN_ROLE_ID, DEVELOPER_ROLE_ID}
        has_role = any(role.id in allowed_role_ids for role in ctx.author.roles)
        return has_admin or has_role
    return commands.check(predicate)

async def send_hidden_message(ctx: commands.Context, text: str):
    if ctx.interaction: # slash command
        await ctx.interaction.followup.send(text, ephemeral=True)
    else:
        await ctx.send(text, delete_after=10.0)

# ---------------------------------- youtube command and task
SUCCESS_CODE = 200

class YouTubeLink(commands.Converter):
    async def convert(self, ctx: commands.Context, argument):
        if not re.match(YOUTUBE_REGEX, argument):
            raise commands.BadArgument(f"Your YouTube link is invalid. Please try again.")
        return argument

# https://apidog.com/blog/aiohttp-request/
# https://docs.aiohttp.org/en/stable/client_quickstart.html
async def send_video_to_endpoint(video_url: str):
    payload = {"video_url": video_url}
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_ENDPOINT_URL, json=payload, headers=headers) as resp:
            return resp.status

# ---------------------------------- faq selector
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=select#discord.ui.Select
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=view#discord.ui.View
class FAQView(discord.ui.View):
    def __init__(self, faq_entries):
        super().__init__(timeout=None)
        self.faq_entries = faq_entries
        options = [
            discord.SelectOption(label=entry["question"], value=str(idx))
            for idx, entry in enumerate(faq_entries)
        ]
        self.add_item(FAQSelect(options, faq_entries))

class FAQSelect(discord.ui.Select):
    def __init__(self, options, faq_entries):
        super().__init__(placeholder="Choose a question...", options=options, custom_id="faq_select")
        self.faq_entries = faq_entries

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        entry = self.faq_entries[idx]
        embed = discord.Embed(
            title=entry["question"],
            description=entry["answer"],
            color=discord.Color.dark_blue()
        )
        await interaction.response.edit_message(embed=embed, view=self.view)