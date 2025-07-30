import discord
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class ModerationTools:
    """Moderation tools for the Discord bot."""
    
    def __init__(self, bot: discord.Client):
        self.bot = bot
        
        # Initialize filter and spam tracking if not existing
        if not hasattr(self.bot, "word_filters"):
            self.bot.word_filters = {}
            
        if not hasattr(self.bot, "user_message_history"):
            self.bot.user_message_history = {}
            
        if not hasattr(self.bot, "anti_spam_config"):
            self.bot.anti_spam_config = {}
            
    def _setup_event_handlers(self):
        """Set up event handlers for moderation features."""
        if hasattr(self.bot, "_moderation_initialized"):
            return
            
        self.bot._moderation_initialized = True
        
        # Create message filter handler
        async def on_message_filter(message):
            # Skip bot messages and DMs
            if message.author.bot or not message.guild:
                return
                
            guild_id = message.guild.id
            
            # Check if this guild has a word filter
            if not hasattr(self.bot, "word_filters") or guild_id not in self.bot.word_filters:
                return
                
            filter_config = self.bot.word_filters[guild_id]
            content_lower = message.content.lower()
            
            # Check if any banned words are in the message
            for word in filter_config["words"]:
                if word in content_lower.split() or word in content_lower:
                    # Take action based on configuration
                    action = filter_config["action"]
                    
                    if action == "delete":
                        try:
                            await message.delete()
                            await message.channel.send(
                                f"{message.author.mention}, your message was removed for containing banned words.",
                                delete_after=5
                            )
                        except:
                            pass
                            
                    elif action == "warn":
                        try:
                            await message.channel.send(
                                f"{message.author.mention}, warning: your message contains banned words.",
                                delete_after=5
                            )
                        except:
                            pass
                            
                    elif action == "timeout":
                        try:
                            # Timeout for 10 minutes
                            duration = timedelta(minutes=10)
                            until = discord.utils.utcnow() + duration
                            await message.author.timeout(until, reason="Banned word usage")
                            await message.delete()
                            await message.channel.send(
                                f"{message.author.mention} has been timed out for 10 minutes for using banned words.",
                                delete_after=5
                            )
                        except:
                            pass
                            
                    elif action == "kick":
                        try:
                            await message.delete()
                            await message.author.kick(reason="Banned word usage")
                            await message.channel.send(
                                f"{message.author.mention} has been kicked for using banned words."
                            )
                        except:
                            pass
                            
                    # Stop checking more words once we've found one
                    break
                    
        # Create anti-spam handler
        async def on_message_spam(message):
            # Skip bot messages and DMs
            if message.author.bot or not message.guild:
                return
                
            guild_id = message.guild.id
            user_id = message.author.id
            
            # Check if this guild has anti-spam enabled
            if not hasattr(self.bot, "anti_spam_config") or guild_id not in self.bot.anti_spam_config:
                return
                
            spam_config = self.bot.anti_spam_config[guild_id]
            threshold = spam_config["threshold"]
            window = spam_config["window"]
            
            # Initialize user's message history if needed
            if not hasattr(self.bot, "user_message_history"):
                self.bot.user_message_history = {}
                
            if user_id not in self.bot.user_message_history:
                self.bot.user_message_history[user_id] = []
                
            # Add the current message timestamp
            now = discord.utils.utcnow()
            self.bot.user_message_history[user_id].append(now)
            
            # Remove old messages outside the time window
            window_start = now - timedelta(seconds=window)
            self.bot.user_message_history[user_id] = [
                ts for ts in self.bot.user_message_history[user_id] 
                if ts >= window_start
            ]
            
            # Check if user has sent too many messages
            recent_messages = len(self.bot.user_message_history[user_id])
            if recent_messages >= threshold:
                # Take action based on configuration
                action = spam_config["action"]
                
                if action == "delete":
                    try:
                        await message.delete()
                        await message.channel.send(
                            f"{message.author.mention}, please slow down! You're sending messages too quickly.",
                            delete_after=5
                        )
                    except:
                        pass
                        
                elif action == "warn":
                    try:
                        await message.channel.send(
                            f"{message.author.mention}, warning: you're sending messages too quickly. Please slow down.",
                            delete_after=5
                        )
                    except:
                        pass
                        
                elif action == "timeout":
                    try:
                        # Timeout for 5 minutes
                        duration = timedelta(minutes=5)
                        until = discord.utils.utcnow() + duration
                        await message.author.timeout(until, reason="Spamming")
                        await message.channel.send(
                            f"{message.author.mention} has been timed out for 5 minutes due to spamming."
                        )
                    except:
                        pass
                        
                elif action == "kick":
                    try:
                        await message.author.kick(reason="Spamming")
                        await message.channel.send(
                            f"{message.author.mention} has been kicked due to spamming."
                        )
                    except:
                        pass
                        
                # Reset the user's message history
                self.bot.user_message_history[user_id] = []
        
        # Add the listeners
        self.bot.add_listener(on_message_filter, "on_message")
        self.bot.add_listener(on_message_spam, "on_message")
    
    async def setup_word_filter(self, guild_id: int, banned_words: List[str], action: str = "delete") -> str:
        """
        Set up a word filter for the server.
        
        Args:
            guild_id: The ID of the Discord server
            banned_words: List of words to ban
            action: Action to take ('delete', 'warn', 'timeout', 'kick')
            
        Returns:
            str: Success or error message
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            # Validate action
            valid_actions = ["delete", "warn", "timeout", "kick"]
            if action not in valid_actions:
                return f"Error: Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
                
            # Remove any empty strings and duplicates
            banned_words = list(set(word.lower().strip() for word in banned_words if word.strip()))
            
            if not banned_words:
                return "Error: No valid banned words provided"
                
            # Store the word filter configuration
            if not hasattr(self.bot, "word_filters"):
                self.bot.word_filters = {}
                
            self.bot.word_filters[guild_id] = {
                "words": banned_words,
                "action": action
            }
            
            # Set up event listeners if not already done
            self._setup_event_handlers()
            
            return f"✅ Word filter set up with {len(banned_words)} banned words. Action: {action}"
            
        except Exception as e:
            logger.error(f"Error setting up word filter: {e}")
            return f"Error setting up word filter: {str(e)}"
            
    async def setup_anti_spam(self, guild_id: int, message_threshold: int = 5, time_window: int = 3, action: str = "timeout") -> str:
        """
        Set up anti-spam protection for the server.
        
        Args:
            guild_id: The ID of the Discord server
            message_threshold: Number of messages before triggering action
            time_window: Time window in seconds to count messages
            action: Action to take ('delete', 'warn', 'timeout', 'kick')
            
        Returns:
            str: Success or error message
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            # Validate action
            valid_actions = ["delete", "warn", "timeout", "kick"]
            if action not in valid_actions:
                return f"Error: Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
                
            # Validate parameters
            if message_threshold < 3:
                return "Error: Message threshold must be at least 3"
                
            if time_window < 1 or time_window > 60:
                return "Error: Time window must be between 1 and 60 seconds"
                
            # Store the anti-spam configuration
            if not hasattr(self.bot, "anti_spam_config"):
                self.bot.anti_spam_config = {}
                
            self.bot.anti_spam_config[guild_id] = {
                "threshold": message_threshold,
                "window": time_window,
                "action": action
            }
            
            # Initialize user message history if not already done
            if not hasattr(self.bot, "user_message_history"):
                self.bot.user_message_history = {}
                
            # Set up event listeners if not already done
            self._setup_event_handlers()
            
            return f"✅ Anti-spam protection enabled. Threshold: {message_threshold} messages in {time_window} seconds. Action: {action}"
            
        except Exception as e:
            logger.error(f"Error setting up anti-spam: {e}")
            return f"Error setting up anti-spam: {str(e)}"
            
    async def track_member_activity(self, guild_id: int, tracking_channel_identifier: str = None) -> str:
        """
        Enable tracking of member activity (joins, leaves, messages) for server analytics.
        
        Args:
            guild_id: The ID of the Discord server
            tracking_channel_identifier: Optional channel for activity logs
            
        Returns:
            str: Success or error message
        """
        try:
            from enhanced_discord_tools import DiscordTools
            tools = DiscordTools(self.bot)
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            # Set up tracking configuration
            tracking_channel = None
            if tracking_channel_identifier:
                tracking_channel = await tools.get_channel_by_name_or_id(guild_id, tracking_channel_identifier)
                if not tracking_channel:
                    return f"Error: Tracking channel '{tracking_channel_identifier}' not found"
                
                if not isinstance(tracking_channel, discord.TextChannel):
                    return f"Error: Cannot use a {tracking_channel.type} channel for activity tracking"
            
            # Initialize tracking data
            if not hasattr(self.bot, "activity_tracking"):
                self.bot.activity_tracking = {}
                
            self.bot.activity_tracking[guild_id] = {
                "enabled": True,
                "tracking_channel_id": tracking_channel.id if tracking_channel else None,
                "join_count": 0,
                "leave_count": 0,
                "message_count": 0,
                "active_users": set(),
                "start_time": datetime.utcnow()
            }
            
            # Set up event handlers if not already done
            if not hasattr(self.bot, "_activity_tracking_initialized"):
                self.bot._activity_tracking_initialized = True
                
                # Member join handler
                async def on_member_join(member):
                    guild_id = member.guild.id
                    if not hasattr(self.bot, "activity_tracking") or guild_id not in self.bot.activity_tracking:
                        return
                        
                    tracking = self.bot.activity_tracking[guild_id]
                    if not tracking["enabled"]:
                        return
                        
                    # Update counter
                    tracking["join_count"] += 1
                    
                    # Log to channel if configured
                    if tracking["tracking_channel_id"]:
                        try:
                            channel = self.bot.get_channel(tracking["tracking_channel_id"])
                            if channel:
                                await channel.send(f"📥 **Member Joined**: {member.mention} ({member}) at <t:{int(datetime.utcnow().timestamp())}:F>")
                        except Exception as e:
                            logger.error(f"Error logging member join: {e}")
                
                # Member leave handler
                async def on_member_remove(member):
                    guild_id = member.guild.id
                    if not hasattr(self.bot, "activity_tracking") or guild_id not in self.bot.activity_tracking:
                        return
                        
                    tracking = self.bot.activity_tracking[guild_id]
                    if not tracking["enabled"]:
                        return
                        
                    # Update counter
                    tracking["leave_count"] += 1
                    
                    # Log to channel if configured
                    if tracking["tracking_channel_id"]:
                        try:
                            channel = self.bot.get_channel(tracking["tracking_channel_id"])
                            if channel:
                                await channel.send(f"📤 **Member Left**: {member} at <t:{int(datetime.utcnow().timestamp())}:F>")
                        except Exception as e:
                            logger.error(f"Error logging member leave: {e}")
                
                # Message handler
                async def on_message_activity(message):
                    if message.author.bot or not message.guild:
                        return
                        
                    guild_id = message.guild.id
                    if not hasattr(self.bot, "activity_tracking") or guild_id not in self.bot.activity_tracking:
                        return
                        
                    tracking = self.bot.activity_tracking[guild_id]
                    if not tracking["enabled"]:
                        return
                        
                    # Update counters
                    tracking["message_count"] += 1
                    tracking["active_users"].add(message.author.id)
                
                # Add the listeners
                self.bot.add_listener(on_member_join, "on_member_join")
                self.bot.add_listener(on_member_remove, "on_member_remove")
                self.bot.add_listener(on_message_activity, "on_message")
            
            channel_msg = f" with logs in #{tracking_channel.name}" if tracking_channel else ""
            return f"✅ Member activity tracking enabled{channel_msg}. Use get_server_analytics to view statistics."
            
        except Exception as e:
            logger.error(f"Error setting up activity tracking: {e}")
            return f"Error setting up activity tracking: {str(e)}"