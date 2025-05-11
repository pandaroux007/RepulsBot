import discord
from discord.ext import commands
# app files
from private_data import TOKEN

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(TOKEN)