import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import *
import os

# Initialize timezone
SERVER_TZ = pytz_timezone(SERVER_TZ)

# Authenticate Google Calendar API
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
calendar_service = build('calendar', 'v3', credentials=credentials)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

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
    time_max = (now + timedelta(days=DAYS_AHEAD)).isoformat()

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

    voice_channel = None
    if VOICE_CHANNEL_ID is not None:
        voice_channel = guild.get_channel(VOICE_CHANNEL_ID)
        if not voice_channel or not isinstance(voice_channel, discord.VoiceChannel):
            await printout("Voice channel not found or is not a voice channel.", channel)
            return

    await printout("Fetching events from Google Calendar...", channel)
    events = get_upcoming_events()

    # Fetch existing Discord events
    existing_events = await guild.fetch_scheduled_events()
    # Filter out events that are not created by the bot
    existing_events = [
        event for event in existing_events
        if event.creator.id == bot.user.id
    ]

    google_event_start_times = set(
        datetime.fromisoformat(event['start']['dateTime']).astimezone(timezone.utc)
        for event in events
    )

    # Cancel Discord events not in Google Calendar, that are not ongoing or imminent
    soon = datetime.now(timezone.utc) + timedelta(minutes=5)
    for discord_event in existing_events:
        if discord_event.start_time > soon and discord_event.start_time not in google_event_start_times:
            await discord_event.cancel()
            await printout(f"Canceled Discord event: {discord_event.name}", channel)

    # Create new Discord events for Google Calendar events
    for event in events:
        name = event['summary']
        description = event.get('description', '')

        start_raw = event['start'].get('dateTime')
        end_raw = event['end'].get('dateTime')

        start_dt = datetime.fromisoformat(start_raw).astimezone(timezone.utc)
        end_dt = datetime.fromisoformat(end_raw).astimezone(timezone.utc)

        # Avoid duplicates by checking existing event names and start times
        existing_event = next(
            (e for e in existing_events if e.start_time == start_dt),
            None
        )
        if existing_event:
            # Update the existing event if needed
            if existing_event.description != description or existing_event.end_time != end_dt \
            or existing_event.name != name:
                await existing_event.edit(
                    name=name,
                    description=description,
                    end_time=end_dt
                )
                await printout(f"Updated Discord event: {name}", channel)
            else:
                await printout(f"Event already exists: {name}", channel)
            continue

        # Check for an image file corresponding to the event name
        image_path = None
        for ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            potential_path = os.path.join(IMAGE_DIRECTORY, f"{name}.{ext}")
            if os.path.isfile(potential_path):
                image_path = potential_path
                break

        await guild.create_scheduled_event(
            name=name,
            description=description,
            start_time=start_dt,
            end_time=end_dt,
            channel=voice_channel,
            entity_type=discord.EntityType.voice if voice_channel else discord.EntityType.external,
            privacy_level=discord.PrivacyLevel.guild_only,
            image=open(image_path, 'rb') if image_path else None  # Use image if found
        )
        await printout(f"Created Discord event: {name}", channel)

    # Update bot status with the next upcoming event
    if ENABLE_STATUS_UPDATE:
        if events:
            # events are sorted by start time, next event is 0
            next_event_name = events[0]['summary']
            next_event_time = datetime.fromisoformat(events[0]['start']['dateTime']).astimezone(SERVER_TZ)
            human_readable_time = next_event_time.strftime('%a %-I:%M%p')
            status_message = f"Next: {next_event_name} - {human_readable_time}"
        else:
            status_message = "No upcoming events"

        await bot.change_presence(activity=discord.CustomActivity(name=status_message))
        await printout(f"Updated bot status: {status_message}", channel)

bot.run(TOKEN)
