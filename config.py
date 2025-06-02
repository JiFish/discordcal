# Google Calendar setup
SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CALENDARS = [
    'dummy_calendar_id@group.calendar.google.com',
]

# Discord setup
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
GUILD_ID = 123456789012345678          # Replace with your guild ID
ADMIN_USER_IDS = [123456789012345678]  # Replace with your admin user IDs
FALLBACK_VOICE_CHANNEL_ID = None       # Set to a channel ID to make all events wihthout a voice channel use this one
COMMAND_PREFIX = "!"

# Bot settings
DAYS_AHEAD = 14                 # Number of days to look ahead for events
UPDATE_FREQUENCY_MINUTES = 60   # Frequency of updates in minutes
EVENT_GRACE_TIME = 5            # Number of minutes before an event starts when it will no longer be modified
ENABLE_STATUS_UPDATE = True     # Enable or disable updating the bot's status
SERVER_TZ = 'GMT'               # Your server's timezone as a string, used for the bot's status
# Format for the bot's status message
# %event: Event name
# %next: Day name if the event is less than 7 days away, otherwise the month name and day
# You can use any placeholders from strftime: https://strftime.org/
STATUS_MESSAGE_FORMAT = "Next: %event - %next %H:%M (GMT)"

# Frequency (in minutes) for auto-starting events if eligible. Set to None or 0 to disable.
AUTOSTART_LOOP_MINUTES = 1

# Directory for event images
IMAGE_DIRECTORY = 'images'
# File to store event mappings
EVENT_MAPPING_FILE = "event_mapping.json"
