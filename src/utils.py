import aiohttp
from discord.ext import commands
# bot files
from constants import *

SUCCESS_CODE = 200

def check_admin_or_roles():
    async def predicate(ctx: commands.Context):
        has_admin = ctx.author.guild_permissions.administrator
        allowed_role_ids = {ADMIN_ROLE_ID, DEVELOPER_ROLE_ID}
        has_role = any(role.id in allowed_role_ids for role in ctx.author.roles)
        return has_admin or has_role
    return commands.check(predicate)

class YouTubeLink(commands.Converter):
    async def convert(self, ctx: commands.Context, argument):
        if not re.match(YOUTUBE_REGEX, argument):
            raise commands.BadArgument(f"Your YouTube link is invalid. Please try again.")
        return argument

async def send_hidden_message(ctx: commands.Context, text: str):
    if ctx.interaction: # slash command
        await ctx.interaction.followup.send(text, ephemeral=True)
    else:
        await ctx.send(text, delete_after=10.0)

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