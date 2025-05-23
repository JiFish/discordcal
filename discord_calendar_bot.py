import discord
from discord.ext import commands, tasks
from config import COMMAND_PREFIX, TOKEN, ADMIN_USER_ID, UPDATE_FREQUENCY_MINUTES
from logic import fetch_and_create_events, store_server_info, update_existing_event_images, load_event_mappings

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    if not await store_server_info(bot):
        print("Failed to get Discord objects.")
        bot.close()
    else:
        load_event_mappings()
        main_loop.start()

@bot.command()
async def ping(ctx):
    """Respond with 'pong!'"""
    if ctx.author.id == ADMIN_USER_ID:
        await ctx.send("pong!")

@bot.command()
async def update(ctx):
    """Manually fetch and create events"""
    if ctx.author.id == ADMIN_USER_ID:
        await ctx.send("Please wait while I fetch and create events...")
        output = await fetch_and_create_events(bot)
        await ctx.send("\n".join(output))

@bot.command()
async def updateimg(ctx):
    """Update images for all events in event_mappings"""
    if ctx.author.id == ADMIN_USER_ID:
        await ctx.send("Updating images for all events...")
        output = await update_existing_event_images()
        await ctx.send("\n".join(output))

@tasks.loop(minutes=UPDATE_FREQUENCY_MINUTES)
async def main_loop():
    for output in await fetch_and_create_events(bot):
        print(output)

bot.run(TOKEN)
