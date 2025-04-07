# Google Calendar setup
SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CALENDARS = [
    'dummy_calendar_id@group.calendar.google.com',
]

# Discord setup
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
GUILD_ID = 123456789012345678          # Replace with your guild ID
VOICE_CHANNEL_ID = 123456789012345678  # Replace with your voice channel ID, or None
ADMIN_USER_ID = 123456789012345678     # Replace with your admin user ID
COMMAND_PREFIX = "!"

# Bot settings
DAYS_AHEAD = 14                        # Number of days to look ahead for events
UPDATE_FREQUENCY_MINUTES = 60          # Frequency of updates in minutes
ENABLE_STATUS_UPDATE = True            # Enable or disable updating the bot's status
SERVER_TZ = 'Europe/London'            # Your server's timezone as a string, used for the bot's status
