import discord
from discord.ext import commands
import os

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

if __name__ == "__main__":
    bot.run(TOKEN)