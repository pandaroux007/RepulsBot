from discord.ext import commands
# bot file
from constants import IDs

# ---------------------------------- check decorator and hidden message function
def check_admin_or_roles():
    async def predicate(ctx: commands.Context):
        has_admin = ctx.author.guild_permissions.administrator
        allowed_role_ids = {IDs.serverRoles.ADMIN, IDs.serverRoles.DEVELOPER}
        has_role = any(role.id in allowed_role_ids for role in ctx.author.roles)
        return has_admin or has_role
    return commands.check(predicate)

async def send_hidden_message(ctx: commands.Context, text: str):
    if ctx.interaction: # slash command
        await ctx.interaction.followup.send(text, ephemeral=True)
    else:
        await ctx.send(text, delete_after=10.0)