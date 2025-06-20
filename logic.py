import discord
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
EVENT_SHORT_TITLES = {k.lower(): v for k, v in EVENT_SHORT_TITLES.items()} # Make find strings lowercase

# Google Calendar API Initialization
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
calendar_service = build('calendar', 'v3', credentials=credentials)

# Global Variables
fallback_voice_channel = None
guild = None
event_mappings = {}

# Utility Functions
def load_event_mappings():
    global event_mappings
    if os.path.exists(EVENT_MAPPING_FILE):
        with open(EVENT_MAPPING_FILE, 'r') as f:
            event_mappings = json.load(f)
    return {}

def save_event_mappings(mappings):
    with open(EVENT_MAPPING_FILE, 'w') as f:
        json.dump(mappings, f, indent=4)

def get_event_image(name):
    for ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        potential_path = os.path.join(IMAGE_DIRECTORY, f"{name}.{ext}")
        if os.path.isfile(potential_path):
            with open(potential_path, 'rb') as image_file:
                return image_file.read()
    return discord.utils.MISSING

def parse_event(event):
    start_raw = event['start'].get('dateTime')
    end_raw = event['end'].get('dateTime')
    start_dt = datetime.fromisoformat(start_raw).astimezone(timezone.utc)
    end_dt = datetime.fromisoformat(end_raw).astimezone(timezone.utc)

    name = event['summary']
    description = event.get('description', '')
    location = event.get('location', '').strip()

    voice_channel = fallback_voice_channel
    if location:
        for vc in guild.voice_channels:
            if vc.name.lower().strip() == location.lower():
                voice_channel = vc
                break

    if not voice_channel:
        entity_type = discord.EntityType.external
        voice_channel = discord.utils.MISSING
    else:
        entity_type = discord.EntityType.voice
        location = discord.utils.MISSING

    return {
        'name': name,
        'description': description,
        'start_time': start_dt,
        'end_time': end_dt,
        'channel': voice_channel,
        'location': location,
        'entity_type': entity_type
    }

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
        all_events.extend(
            event for event in events
            if 'dateTime' in event['start'] and 'dateTime' in event['end']
        )

    if len(CALENDARS) > 1:
        all_events.sort(key=lambda event: event['start']['dateTime'])

    return all_events

# Discord Bot Functions
async def store_server_info(bot):
    global fallback_voice_channel, guild

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found.")
        return False

    if FALLBACK_VOICE_CHANNEL_ID is None:
        return True
    
    voice_channel = guild.get_channel(FALLBACK_VOICE_CHANNEL_ID)
    if not voice_channel or not isinstance(voice_channel, discord.VoiceChannel):
        print("Voice channel not found or is not a voice channel.")
        return False
    
    fallback_voice_channel = voice_channel
    return True

async def printout(message, channel=None):
    if channel is None:
        print(message)
    else:
        await channel.send(message)

async def fetch_and_create_events(bot):
    output = ["Fetching events from Google Calendar..."]
    events = get_upcoming_events()

    existing_events = await guild.fetch_scheduled_events()
    existing_events_by_id = {event.id: event for event in existing_events}

    output += await cancel_outdated_events(events, existing_events_by_id)
    output += await create_or_update_events(events, existing_events_by_id)
    save_event_mappings(event_mappings)

    if ENABLE_STATUS_UPDATE:
        output.append(await update_bot_status(events, bot))

    return output

async def cancel_outdated_events(events, existing_events_by_id):
    output = []
    soon = datetime.now(timezone.utc) + EVENT_GRACE_TIME
    google_event_ids = {event['id'] for event in events}
    for google_id, discord_id in list(event_mappings.items()):
        if google_id not in google_event_ids:
            discord_event = existing_events_by_id.get(discord_id)
            # If the event exists and is not in it's grace period
            if discord_event and discord_event.start_time > soon:
                await discord_event.cancel()
                output.append(f"Canceled Discord event: {discord_event.name}")
            del event_mappings[google_id]
    return output

async def create_or_update_events(events, existing_events_by_id):
    output = []
    for event in events:
        google_id = event['id']
        discord_event = existing_events_by_id.get(event_mappings.get(google_id))

        if discord_event:
            output.append(await update_event_if_needed(discord_event, event))
        else:
            output.append(await create_new_event(event, google_id))
    return output

async def update_event_if_needed(discord_event, event):
    parsed_event = parse_event(event)
    name = parsed_event['name']
    has_changes = any(
        getattr(discord_event, key) != (None if value is discord.utils.MISSING else value)
        for key, value in parsed_event.items()
    )
    if has_changes:
        await discord_event.edit(**parsed_event)
        return f"Updated Discord event: {name}"
    return f"No changes for event: {name}"

async def create_new_event(event, google_id):
    parsed_event = parse_event(event)
    name = parsed_event['name']
    image_data = get_event_image(name)
    new_event = await guild.create_scheduled_event(
        privacy_level=discord.PrivacyLevel.guild_only,
        image=image_data,
        **parsed_event
    )
    event_mappings[google_id] = new_event.id
    return f"Created Discord event: {name}"

async def update_bot_status(events, bot):#EVENT_SHORT_TITLES
    if events:
        next_event_time = datetime.fromisoformat(events[0]['start']['dateTime']).astimezone(SERVER_TZ)
        event_name = events[0]['summary']
        event_name = EVENT_SHORT_TITLES.get(event_name.lower(), event_name)
        status_message = STATUS_MESSAGE_FORMAT.replace("%event", event_name.replace("%", "%%"))
        if "%next" in status_message:
            today = datetime.now(SERVER_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
            days_away = (next_event_time - today).days
            if days_away == 0:
                day_happening = "Today"
            elif days_away == 1:
                day_happening = "Tomorrow"
            elif days_away <= 7:
                day_happening = "%a"
            else:
                day_happening = "%b %d"
            status_message = status_message.replace("%next", day_happening)
        status_message = next_event_time.strftime(status_message)
    else:
        status_message = "No upcoming events"

    await bot.change_presence(activity=discord.CustomActivity(name=status_message))
    return f"Updated bot status: {status_message}"

async def update_existing_event_images():
    output = []
    for discord_id in event_mappings.values():
        try:
            discord_event = await guild.fetch_scheduled_event(discord_id)
            image_data = get_event_image(discord_event.name)
            if image_data:
                await discord_event.edit(image=image_data)
                output.append(f"Updated image for event: {discord_event.name}")
            else:
                output.append(f"No image found for event: {discord_event.name}")
        except discord.NotFound:
            output.append(f"Event with ID {discord_id} not found.")
    return output
