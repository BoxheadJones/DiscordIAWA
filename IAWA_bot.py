import discord
from discord.ext import commands
import os
import subprocess

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

@bot.command()
async def write_oracle(ctx):
    try:
        # Execute the other Python script
        process = subprocess.Popen(['python3', 'write_oracle.py'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=15)  # Set a timeout

        if process.returncode == 0:
            output = stdout.decode('utf-8')
            await ctx.send(f"Script executed successfully:\n```{output}```")
        else:
            error_output = stderr.decode('utf-8')
            await ctx.send(f"Error executing script:\n```{error_output}```")

    except FileNotFoundError:
        await ctx.send("Error: The script 'my_other_script.py' was not found.")
    except subprocess.TimeoutExpired:
        await ctx.send("Error: The script execution timed out.")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: `{e}`")

if __name__ == "__main__":
    bot.run(TOKEN)