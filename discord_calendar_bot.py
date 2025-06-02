import discord
from discord.ext import commands, tasks
from config import COMMAND_PREFIX, TOKEN, ADMIN_USER_IDS, UPDATE_FREQUENCY_MINUTES, AUTOSTART_LOOP_MINUTES
from logic import fetch_and_create_events, store_server_info, update_existing_event_images, load_event_mappings, maybe_autostart_events

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Store managed events for autostart
managed_events = []

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
        if AUTOSTART_LOOP_MINUTES and AUTOSTART_LOOP_MINUTES > 0:
            autostart_loop.change_interval(minutes=AUTOSTART_LOOP_MINUTES)
            autostart_loop.start()

@bot.command()
async def ping(ctx):
    """Respond with 'pong!'"""
    if ctx.author.id in ADMIN_USER_IDS:
        await ctx.send("pong!")

@bot.command()
async def update(ctx):
    """Manually fetch and create events"""
    if ctx.author.id in ADMIN_USER_IDS:
        await ctx.send("Please wait while I fetch and create events...")
        output, events = await fetch_and_create_events(bot)
        global managed_events
        managed_events = events
        await ctx.send("\n".join(output))

@bot.command()
async def updateimg(ctx):
    """Update images for all events in event_mappings"""
    if ctx.author.id in ADMIN_USER_IDS:
        await ctx.send("Updating images for all events...")
        output = await update_existing_event_images()
        await ctx.send("\n".join(output))

@tasks.loop(minutes=UPDATE_FREQUENCY_MINUTES)
async def main_loop():
    global managed_events
    output, events = await fetch_and_create_events(bot)
    managed_events = events
    for line in output:
        print(line)

@tasks.loop(minutes=1)
async def autostart_loop():
    global managed_events
    if managed_events:
        for output in await maybe_autostart_events(managed_events):
            print(output)

bot.run(TOKEN)
