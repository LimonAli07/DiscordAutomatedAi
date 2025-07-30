import discord
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class UtilityTools:
    """Utility tools for the Discord bot."""
    
    def __init__(self, bot: discord.Client):
        self.bot = bot
        
        # Initialize utilities data structures
        if not hasattr(self.bot, "reminders"):
            self.bot.reminders = []
        
        if not hasattr(self.bot, "scheduled_events"):
            self.bot.scheduled_events = []
            
        # Initialize event checkers
        self._setup_event_checkers()
        
    def _setup_event_checkers(self):
        """Set up background tasks for checking events and reminders."""
        if hasattr(self.bot, "_utility_initialized"):
            return
            
        self.bot._utility_initialized = True
        
        # Set up reminder checker
        async def check_reminders():
            while True:
                try:
                    now = datetime.utcnow()
                    
                    # Look for reminders to send
                    if hasattr(self.bot, "reminders"):
                        for reminder in list(self.bot.reminders):
                            # If it's time for the reminder (within the last minute)
                            time_diff = (now - reminder["time"]).total_seconds()
                            if 0 <= time_diff < 60:
                                try:
                                    channel = self.bot.get_channel(reminder["channel_id"])
                                    if channel:
                                        await channel.send(f"⏰ **REMINDER:**\n{reminder['message']}")
                                except Exception as e:
                                    logger.error(f"Error sending reminder: {e}")
                                
                                # Remove the reminder after it's been sent
                                self.bot.reminders.remove(reminder)
                    
                    # Check scheduled events
                    if hasattr(self.bot, "scheduled_events"):
                        for event in list(self.bot.scheduled_events):
                            # If it's time for the event (within the last minute)
                            time_diff = (now - event["start_time"]).total_seconds()
                            if 0 <= time_diff < 60:
                                # Send notification if a channel is specified
                                if event["notify_channel_id"]:
                                    try:
                                        channel = self.bot.get_channel(event["notify_channel_id"])
                                        if channel:
                                            await channel.send(
                                                f"🔔 **EVENT STARTING NOW**\n\n"
                                                f"**{event['title']}**\n"
                                                f"{event['description']}\n\n"
                                                f"Start time: <t:{int(event['start_time'].timestamp())}:F>"
                                            )
                                    except Exception as e:
                                        logger.error(f"Error sending event notification: {e}")
                                
                                # Remove the event after it's been notified
                                self.bot.scheduled_events.remove(event)
                    
                    # Check every 30 seconds
                    await asyncio.sleep(30)
                
                except Exception as e:
                    logger.error(f"Error in utility checker: {e}")
                    await asyncio.sleep(30)  # Keep running even after errors
        
        # Start the background task if bot has a loop
        if hasattr(self.bot, "loop"):
            self.bot.loop.create_task(check_reminders())
    
    async def set_reminder(self, guild_id: int, channel_identifier: str, message: str, time_str: str) -> str:
        """
        Set a reminder to be sent to a channel after a specified time.
        
        Args:
            guild_id: The ID of the Discord server
            channel_identifier: The name or ID of the channel
            message: The reminder message
            time_str: When to send the reminder (ISO format or relative like '+30m', '+1h')
            
        Returns:
            str: Success or error message
        """
        try:
            from enhanced_discord_tools import DiscordTools
            tools = DiscordTools(self.bot)
            
            channel = await tools.get_channel_by_name_or_id(guild_id, channel_identifier)
            if not channel:
                return f"Error: Channel '{channel_identifier}' not found"
                
            # Check if the channel is a text channel
            if not isinstance(channel, discord.TextChannel):
                return f"Error: Cannot send reminders to a {channel.type} channel"
                
            # Parse time
            reminder_time = None
            if time_str.startswith('+'):
                # Relative time
                time_str = time_str[1:].strip()
                amount = int(''.join(filter(str.isdigit, time_str)))
                unit = ''.join(filter(str.isalpha, time_str)).lower()
                
                if unit in ['m', 'min', 'mins', 'minute', 'minutes']:
                    reminder_time = datetime.utcnow() + timedelta(minutes=amount)
                elif unit in ['h', 'hr', 'hrs', 'hour', 'hours']:
                    reminder_time = datetime.utcnow() + timedelta(hours=amount)
                elif unit in ['d', 'day', 'days']:
                    reminder_time = datetime.utcnow() + timedelta(days=amount)
                else:
                    return f"Error: Invalid time unit '{unit}'"
            else:
                # Try to parse ISO format
                try:
                    reminder_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                except ValueError:
                    return f"Error: Invalid time format. Use ISO format (YYYY-MM-DDTHH:MM:SS) or relative format (+30m, +1h)"
            
            # Store reminder
            if not hasattr(self.bot, "reminders"):
                self.bot.reminders = []
                
            reminder = {
                "channel_id": channel.id,
                "message": message,
                "time": reminder_time
            }
            
            self.bot.reminders.append(reminder)
            
            # Initialize the utility checkers
            self._setup_event_checkers()
            
            # Format response
            timestamp = int(reminder_time.timestamp())
            return f"✅ Reminder set for <t:{timestamp}:F> (<t:{timestamp}:R>) in #{channel.name}"
            
        except Exception as e:
            logger.error(f"Error setting reminder: {e}")
            return f"Error setting reminder: {str(e)}"
    
    async def schedule_event(self, guild_id: int, title: str, description: str, start_time_str: str, 
                           notify_channel_identifier: str = None, duration_minutes: int = 60) -> str:
        """
        Schedule a server event.
        
        Args:
            guild_id: The ID of the Discord server
            title: Event title
            description: Event description
            start_time_str: When the event starts (ISO format or relative like '+30m', '+1h')
            notify_channel_identifier: Optional channel to notify when event starts
            duration_minutes: Event duration in minutes
            
        Returns:
            str: Success or error message
        """
        try:
            from enhanced_discord_tools import DiscordTools
            tools = DiscordTools(self.bot)
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            # Parse time
            start_time = None
            if start_time_str.startswith('+'):
                # Relative time
                time_str = start_time_str[1:].strip()
                amount = int(''.join(filter(str.isdigit, time_str)))
                unit = ''.join(filter(str.isalpha, time_str)).lower()
                
                if unit in ['m', 'min', 'mins', 'minute', 'minutes']:
                    start_time = datetime.utcnow() + timedelta(minutes=amount)
                elif unit in ['h', 'hr', 'hrs', 'hour', 'hours']:
                    start_time = datetime.utcnow() + timedelta(hours=amount)
                elif unit in ['d', 'day', 'days']:
                    start_time = datetime.utcnow() + timedelta(days=amount)
                else:
                    return f"Error: Invalid time unit '{unit}'"
            else:
                # Try to parse ISO format
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                except ValueError:
                    return f"Error: Invalid time format. Use ISO format (YYYY-MM-DDTHH:MM:SS) or relative format (+30m, +1h)"
            
            # Calculate end time
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Get notification channel if specified
            notify_channel = None
            if notify_channel_identifier:
                notify_channel = await tools.get_channel_by_name_or_id(guild_id, notify_channel_identifier)
                if not notify_channel:
                    return f"Error: Notification channel '{notify_channel_identifier}' not found"
                
                if not isinstance(notify_channel, discord.TextChannel):
                    return f"Error: Cannot send notifications to a {notify_channel.type} channel"
            
            # Initialize events list if needed
            if not hasattr(self.bot, "scheduled_events"):
                self.bot.scheduled_events = []
                
            # Create event object
            event = {
                "guild_id": guild_id,
                "title": title,
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
                "notify_channel_id": notify_channel.id if notify_channel else None
            }
            
            self.bot.scheduled_events.append(event)
            
            # Initialize the utility checkers
            self._setup_event_checkers()
            
            # Format response
            start_timestamp = int(start_time.timestamp())
            notify_msg = f" with notification in #{notify_channel.name}" if notify_channel else ""
            
            return (f"✅ Event scheduled: **{title}**\n"
                    f"Start time: <t:{start_timestamp}:F> (<t:{start_timestamp}:R>)\n"
                    f"Duration: {duration_minutes} minutes{notify_msg}")
            
        except Exception as e:
            logger.error(f"Error scheduling event: {e}")
            return f"Error scheduling event: {str(e)}"