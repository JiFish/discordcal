import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import *
import os
import json

# Initialize some constants
SERVER_TZ = pytz_timezone(SERVER_TZ)
EVENT_GRACE_TIME = timedelta(minutes=EVENT_GRACE_TIME)
DAYS_AHEAD = timedelta(days=DAYS_AHEAD)

# Authenticate Google Calendar API
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
calendar_service = build('calendar', 'v3', credentials=credentials)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Load event mappings from file
def load_event_mappings():
    if os.path.exists(EVENT_MAPPING_FILE):
        with open(EVENT_MAPPING_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save event mappings to file
def save_event_mappings(mappings):
    with open(EVENT_MAPPING_FILE, 'w') as f:
        json.dump(mappings, f, indent=4)

# Initialize event mappings
event_mappings = load_event_mappings()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    main_loop.start()

@bot.command()
async def ping(ctx):
    print("Ping command received.")
    """Respond with 'pong!'"""
    if ctx.author.id == ADMIN_USER_ID:
        await ctx.send("pong!")

@bot.command()
async def update(ctx):
    """Manually fetch and create events"""
    if ctx.author.id == ADMIN_USER_ID:
        await fetch_and_create_events(ctx.channel)

@bot.command()
async def updateimg(ctx):
    """Update images for all events in event_mappings"""
    if ctx.author.id == ADMIN_USER_ID:
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            await printout("Guild not found.", ctx.channel)
            return

        for discord_id in event_mappings.values():
            try:
                discord_event = await guild.fetch_scheduled_event(discord_id)
                image_data = get_event_image(discord_event.name)
                if image_data:
                    await discord_event.edit(image=image_data)
                    await printout(f"Updated image for event: {discord_event.name}", ctx.channel)
                else:
                    await printout(f"No image found for event: {discord_event.name}", ctx.channel)
            except discord.NotFound:
                await printout(f"Event with ID {discord_id} not found.", ctx.channel)

@tasks.loop(minutes=UPDATE_FREQUENCY_MINUTES)
async def main_loop():
    await fetch_and_create_events()

# Print output to console or Discord channel
async def printout(message, channel=None):
    if channel is None:
        print(message)
    else:
        await channel.send(message)

# Fetch events from Google Calendar
def get_upcoming_events():
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + DAYS_AHEAD).isoformat()

    all_events = []
    for calendar_id in CALENDARS:
        events_result = calendar_service.events().list(
            calendarId=calendar_id, timeMin=time_min, timeMax=time_max,
            singleEvents=True, orderBy='startTime').execute()
        
        events = events_result.get('items', [])
        # Filter out all-day events (events without 'dateTime' in their start and end)
        all_events.extend(
            event for event in events
            if 'dateTime' in event['start'] and 'dateTime' in event['end']
        )

    # Sort events by start time if there are events from multiple calendars
    if len(CALENDARS) > 1:
        all_events.sort(key=lambda event: event['start']['dateTime'])

    return all_events

async def fetch_and_create_events(channel=None):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        await printout("Guild not found.", channel)
        return

    await printout("Fetching events from Google Calendar...", channel)
    events = get_upcoming_events()

    existing_events = await guild.fetch_scheduled_events()
    existing_event_ids = {event.id: event for event in existing_events}

    await cancel_outdated_events(events, existing_event_ids, channel)

    await create_or_update_events(events, existing_event_ids, guild, channel)

    save_event_mappings(event_mappings)

    if ENABLE_STATUS_UPDATE:
        await update_bot_status(events, channel)

async def get_voice_channel(guild, channel):
    if VOICE_CHANNEL_ID is not None:
        voice_channel = guild.get_channel(VOICE_CHANNEL_ID)
        if not voice_channel or not isinstance(voice_channel, discord.VoiceChannel):
            await printout("Voice channel not found or is not a voice channel.", channel)
            return None
        return voice_channel
    return None

async def cancel_outdated_events(events, existing_event_ids, channel):
    soon = datetime.now(timezone.utc) + EVENT_GRACE_TIME
    google_event_ids = {event['id'] for event in events}
    for google_id, discord_id in list(event_mappings.items()):
        if google_id not in google_event_ids:
            discord_event = existing_event_ids.get(discord_id)
            if discord_event and discord_event.start_time > soon:
                await discord_event.cancel()
                await printout(f"Canceled Discord event: {discord_event.name}", channel)
            del event_mappings[google_id]

async def create_or_update_events(events, existing_event_ids, guild, channel):
    voice_channel = await get_voice_channel(guild, channel)
    for event in events:
        google_id = event['id']
        name = event['summary']
        description = event.get('description', '')

        start_dt, end_dt = parse_event_times(event)

        discord_event = existing_event_ids.get(event_mappings.get(google_id))

        if discord_event:
            await update_event_if_needed(discord_event, name, description, start_dt, end_dt, channel)
        else:
            await create_new_event(guild, name, description, start_dt, end_dt, voice_channel, google_id, channel)

def parse_event_times(event):
    start_raw = event['start'].get('dateTime')
    end_raw = event['end'].get('dateTime')
    start_dt = datetime.fromisoformat(start_raw).astimezone(timezone.utc)
    end_dt = datetime.fromisoformat(end_raw).astimezone(timezone.utc)
    return start_dt, end_dt

async def update_event_if_needed(discord_event, name, description, start_dt, end_dt, channel):
    if discord_event.description != description or discord_event.name != name\
    or discord_event.start_time != start_dt or discord_event.end_time != end_dt:
        await discord_event.edit(
            name=name,
            description=description,
            end_time=end_dt,
            start_time=start_dt,
        )
        await printout(f"Updated Discord event: {name}", channel)
    else:
        await printout(f"Event already exists: {name}", channel)

async def create_new_event(guild, name, description, start_dt, end_dt, voice_channel, google_id, channel):
    image_data = get_event_image(name)
    new_event = await guild.create_scheduled_event(
        name=name,
        description=description,
        start_time=start_dt,
        end_time=end_dt,
        channel=voice_channel,
        entity_type=discord.EntityType.voice if voice_channel else discord.EntityType.external,
        privacy_level=discord.PrivacyLevel.guild_only,
        image=image_data
    )
    event_mappings[google_id] = new_event.id
    await printout(f"Created Discord event: {name}", channel)

def get_event_image(name):
    for ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        potential_path = os.path.join(IMAGE_DIRECTORY, f"{name}.{ext}")
        if os.path.isfile(potential_path):
            with open(potential_path, 'rb') as image_file:
                return image_file.read()
    return discord.utils.MISSING

async def update_bot_status(events, channel):
    if events:
        next_event_time = datetime.fromisoformat(events[0]['start']['dateTime']).astimezone(SERVER_TZ)
        status_message = events[0]['summary'].replace("%", "%%") 
        status_message = STATUS_MESSAGE_FORMAT.replace("%event", status_message)
        status_message = next_event_time.strftime(status_message)
    else:
        status_message = "No upcoming events"

    await bot.change_presence(activity=discord.CustomActivity(name=status_message))
    await printout(f"Updated bot status: {status_message}", channel)

bot.run(TOKEN)
