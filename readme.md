# Discord Calendar Bot

A lightweight self-hosted alternative to chroniclebot. This bot integrates Google Calendar with Discord, automatically creating and managing Discord events based on your Google Calendar events. 

## Features

- Fetches events from one or more Google Calendars and creates corresponding Discord events.
- Look as far ahead as you like!
- Add image banners to events.
- Automatically creates, updates and cancels Discord events at a configurable interval, or do a manual update via a command.
- Optionally updates the bot's status to display the next upcoming event.
- If a Google Calendar event specifies a location, the bot will attempt to match it to a Discord channel voice channel by name. (Or configure it to associate all events with one channel.)

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

All configuration variables are stored in the `config.py` file. You must edit the following settings in `config.py`:

- `CALENDARS`: A list of your Google Calendar IDs.
- `TOKEN`: Your Discord bot token.
- `GUILD_ID`: Your Discord server (guild) ID.
- `ADMIN_USER_ID`: Your Discord user ID for admin commands.

You may also wish to change:

- `DAYS_AHEAD`: Number of days ahead to fetch events.
- `UPDATE_FREQUENCY_MINUTES`: Frequency (in minutes) at which the bot updates events automatically.
- `FALLBACK_VOICE_CHANNEL_ID`: The ID of the fallback voice channel to use if no matching channel is found for an event's location. `None` by default.
- `ENABLE_STATUS_UPDATE`: Set to `True` to enable updating the bot's status with the next event, or `False` to disable it.
- `SERVER_TZ`: Timezone used for above status message.
- `STATUS_MESSAGE_FORMAT`: The text of the status message. `%event` is replaced with the event's name. The date and time use the [strftime](https://strftime.org/) format.

To add images to events, place the image files in the `images` directory. The image file name must match the event's name (case-sensitive) and have one of the supported extensions (`.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`). Recommended image size is 800px wide, 320px tall.

## Admin Commands

Command must be sent via DM.

- `!ping`: Responds with "pong!"
- `!update`: Manually fetches and creates events from Google Calendar.
- `!updateimg`: Force updates images for all existing events with matching image files in the `images` directory.

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
- If you need to explicitly remove all participants from an event, cancel it manually, and it will be re-created on the bot's next update.
- The relationship between google calender event ids and discord event ids is saved to disk in `event_mapping.json`.
