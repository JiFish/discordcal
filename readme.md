# Discord Calendar Bot

A lightweight self-hosted alternative to chroniclebot. This bot integrates Google Calendar with Discord, automatically creating and managing Discord events based on your Google Calendar events. 

## Features

- Fetches events from one or more Google Calendars and creates corresponding Discord events.
- Look as far ahead as you like!
- Automatically updates Discord synchronises at a configurable interval, or do a manual update via a Discord command.
- Cancels Discord events that are no longer present in the Google Calendar.
- Optionally updates the bot's status to display the next upcoming event.

## Prerequisites

1. **Google Calendar API**:
   - Create a service account in the Google Cloud Console.
   - Download the service account JSON file and save it as `service_account.json` in the same directory as the script.
   - Share your Google Calendar with the service account email (or make it public.)

2. **Discord Bot**:
   - Create a bot in the [Discord Developer Portal](https://discord.com/developers/applications).
   - Add permissions for creating and managing events.
   - Copy the bot token and invite the bot to your server.

## Configuration

All configuration variables are stored in the `config.py` file. Edit the following variables in `config.py`:

- `CALENDARS`: A list of your Google Calendar IDs.
- `TOKEN`: Your Discord bot token.
- `GUILD_ID`: Your Discord server (guild) ID.
- `VOICE_CHANNEL_ID`: The ID of the voice channel where events will be associated. Set to `None` to create events without associating them with a voice channel.
- `ADMIN_USER_ID`: Your Discord user ID for admin commands.

You may also wish to change:

- `DAYS_AHEAD`: Number of days ahead to fetch events.
- `UPDATE_FREQUENCY_MINUTES`: Frequency (in minutes) at which the bot updates events automatically.
- `ENABLE_STATUS_UPDATE`: Set to `True` to enable updating the bot's status with the next event, or `False` to disable it.
- `SERVER_TZ`: Timezone used for above status message

## Admin Commands

Command must be sent via DM.

- `!ping`: Responds with "pong!"
- `!update`: Manually fetches and creates events from Google Calendar.

## Running the Bot

1. Clone or download the repository.

2. Install the required dependencies:
   ```bash
   pip install discord.py google-api-python-client google-auth pytz
   ```

3. Run the script:
   ```bash
   python discord_calendar_bot.py
   ```

## Notes
- Excludes all-day events.
- Events are identified by start date/time. If you change the name, description or end time the event will be updated. But if you change the start time the event will be cancelled, and a new one created.
- If you need to explicitly remove all participants from an event cancel it manually, and it will be re-created on the bot's next update.
