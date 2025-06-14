from discord.ext import commands
from constants import *

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