import discord
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class ServerManagement:
    """Server management functions for the Discord bot."""
    
    def __init__(self, bot: discord.Client):
        self.bot = bot
    
    async def setup_auto_role(self, guild_id: int, role_identifier: str) -> str:
        """
        Set up an auto-role that will be assigned to new members when they join.
        
        Args:
            guild_id: The ID of the Discord server
            role_identifier: The name or ID of the role to automatically assign
            
        Returns:
            str: Success or error message
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            # Find the role
            role = None
            if role_identifier.isdigit():
                role = guild.get_role(int(role_identifier))
            else:
                for guild_role in guild.roles:
                    if guild_role.name.lower() == role_identifier.lower():
                        role = guild_role
                        break
                        
            if not role:
                return f"Error: Role '{role_identifier}' not found"
                
            # Check if the bot can manage this role
            if role.position >= guild.me.top_role.position:
                return "Error: Cannot set up auto-role for a role higher than or equal to the bot's highest role"
                
            # Store this in the bot for later use with an on_member_join event
            if not hasattr(self.bot, "auto_roles"):
                self.bot.auto_roles = {}
                
            self.bot.auto_roles[guild_id] = role.id
            
            # Set up the event handler if not already done
            if not hasattr(self.bot, "_auto_role_initialized"):
                self.bot._auto_role_initialized = True
                
                @self.bot.event
                async def on_member_join(member):
                    if not hasattr(self.bot, "auto_roles"):
                        return
                        
                    guild_id = member.guild.id
                    if guild_id not in self.bot.auto_roles:
                        return
                        
                    role_id = self.bot.auto_roles[guild_id]
                    role = member.guild.get_role(role_id)
                    
                    if role:
                        try:
                            await member.add_roles(role, reason="Auto-role assignment")
                        except Exception as e:
                            logger.error(f"Error assigning auto-role: {e}")
            
            return f"✅ Auto-role set up for '{role.name}'. New members will automatically receive this role when they join."
            
        except Exception as e:
            logger.error(f"Error setting up auto-role: {e}")
            return f"Error setting up auto-role: {str(e)}"
            
    async def setup_welcome_message(self, guild_id: int, channel_identifier: str, welcome_message: str) -> str:
        """
        Set up a welcome message to be sent when new members join.
        
        Args:
            guild_id: The ID of the Discord server
            channel_identifier: The name or ID of the channel to send welcome messages
            welcome_message: The message template to send
            
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
                return f"Error: Cannot set a {channel.type} channel as welcome channel"
                
            # Store this in the bot for later use with an on_member_join event
            if not hasattr(self.bot, "welcome_channels"):
                self.bot.welcome_channels = {}
                
            self.bot.welcome_channels[guild_id] = {
                "channel_id": channel.id,
                "message": welcome_message
            }
            
            # Set up the event handler if not already done
            if not hasattr(self.bot, "_welcome_message_initialized"):
                self.bot._welcome_message_initialized = True
                
                @self.bot.event
                async def on_member_join(member):
                    if not hasattr(self.bot, "welcome_channels"):
                        return
                        
                    guild_id = member.guild.id
                    if guild_id not in self.bot.welcome_channels:
                        return
                        
                    config = self.bot.welcome_channels[guild_id]
                    channel = self.bot.get_channel(config["channel_id"])
                    
                    if channel:
                        # Replace placeholders in the message
                        message = config["message"]
                        message = message.replace("{user}", member.mention)
                        message = message.replace("{server}", member.guild.name)
                        message = message.replace("{count}", str(member.guild.member_count))
                        
                        try:
                            await channel.send(message)
                        except Exception as e:
                            logger.error(f"Error sending welcome message: {e}")
            
            return f"✅ Welcome channel set to #{channel.name} with message:\n{welcome_message}"
            
        except Exception as e:
            logger.error(f"Error setting up welcome channel: {e}")
            return f"Error setting up welcome channel: {str(e)}"

    async def backup_server(self, guild_id: int) -> str:
        """
        Create a backup of server settings including channels, roles, and permissions.
        
        Args:
            guild_id: The ID of the Discord server
            
        Returns:
            str: Success message with backup summary
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            backup = {
                "server_name": guild.name,
                "server_id": guild.id,
                "backup_time": datetime.utcnow().isoformat(),
                "roles": [],
                "categories": [],
                "channels": []
            }
            
            # Backup roles (except @everyone which is handled specially)
            for role in guild.roles:
                if not role.is_default():
                    role_data = {
                        "name": role.name,
                        "id": role.id,
                        "color": role.color.value,
                        "hoist": role.hoist,
                        "mentionable": role.mentionable,
                        "permissions": role.permissions.value,
                        "position": role.position
                    }
                    backup["roles"].append(role_data)
            
            # Backup categories
            for category in guild.categories:
                category_data = {
                    "name": category.name,
                    "id": category.id,
                    "position": category.position,
                    "overwrites": []
                }
                
                # Backup permission overwrites for the category
                for target, overwrite in category.overwrites.items():
                    overwrite_data = {
                        "id": target.id,
                        "type": "role" if isinstance(target, discord.Role) else "member",
                        "allow": overwrite.pair()[0].value,
                        "deny": overwrite.pair()[1].value
                    }
                    category_data["overwrites"].append(overwrite_data)
                
                backup["categories"].append(category_data)
            
            # Backup channels (excluding those in categories)
            for channel in guild.channels:
                if not isinstance(channel, discord.CategoryChannel) and channel.category is None:
                    channel_data = {
                        "name": channel.name,
                        "id": channel.id,
                        "type": str(channel.type),
                        "position": channel.position,
                        "overwrites": []
                    }
                    
                    # Add channel type specific properties
                    if isinstance(channel, discord.TextChannel):
                        channel_data["topic"] = channel.topic
                        channel_data["slowmode_delay"] = channel.slowmode_delay
                        channel_data["nsfw"] = channel.is_nsfw()
                    elif isinstance(channel, discord.VoiceChannel):
                        channel_data["bitrate"] = channel.bitrate
                        channel_data["user_limit"] = channel.user_limit
                    
                    # Backup permission overwrites
                    for target, overwrite in channel.overwrites.items():
                        overwrite_data = {
                            "id": target.id,
                            "type": "role" if isinstance(target, discord.Role) else "member",
                            "allow": overwrite.pair()[0].value,
                            "deny": overwrite.pair()[1].value
                        }
                        channel_data["overwrites"].append(overwrite_data)
                    
                    backup["channels"].append(channel_data)
            
            # Backup channels in categories
            for category in guild.categories:
                for channel in category.channels:
                    channel_data = {
                        "name": channel.name,
                        "id": channel.id,
                        "type": str(channel.type),
                        "position": channel.position,
                        "category_id": category.id,
                        "overwrites": []
                    }
                    
                    # Add channel type specific properties
                    if isinstance(channel, discord.TextChannel):
                        channel_data["topic"] = channel.topic
                        channel_data["slowmode_delay"] = channel.slowmode_delay
                        channel_data["nsfw"] = channel.is_nsfw()
                    elif isinstance(channel, discord.VoiceChannel):
                        channel_data["bitrate"] = channel.bitrate
                        channel_data["user_limit"] = channel.user_limit
                    
                    # Backup permission overwrites
                    for target, overwrite in channel.overwrites.items():
                        overwrite_data = {
                            "id": target.id,
                            "type": "role" if isinstance(target, discord.Role) else "member",
                            "allow": overwrite.pair()[0].value,
                            "deny": overwrite.pair()[1].value
                        }
                        channel_data["overwrites"].append(overwrite_data)
                    
                    backup["channels"].append(channel_data)
            
            # Store the backup in the bot for later use
            if not hasattr(self.bot, "server_backups"):
                self.bot.server_backups = {}
            
            self.bot.server_backups[guild_id] = backup
            
            # Generate summary
            summary = [
                f"✅ Backup created for server '{guild.name}'",
                f"• {len(backup['roles'])} roles",
                f"• {len(backup['categories'])} categories",
                f"• {len(backup['channels'])} channels",
                "\nThis backup is stored in memory and can be used with the restore_server command."
            ]
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Error during server backup: {e}")
            return f"Error during server backup: {str(e)}"
            
    async def restore_server(self, guild_id: int, backup_id: Optional[int] = None) -> str:
        """
        Restore a server from a backup.
        
        Args:
            guild_id: The ID of the Discord server to restore to
            backup_id: Optional ID of the server backup to use (defaults to same server)
            
        Returns:
            str: Success or error message
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            # Get the backup
            if not hasattr(self.bot, "server_backups"):
                return "Error: No backups available"
                
            source_id = backup_id if backup_id else guild_id
            if source_id not in self.bot.server_backups:
                return f"Error: No backup found for server ID {source_id}"
                
            backup = self.bot.server_backups[source_id]
            
            # This is a dangerous operation that should be confirmed before executing
            return (
                "⚠️ **DANGEROUS OPERATION** ⚠️\n\n"
                "Restoring a server will:\n"
                "1. Create missing roles and channels\n"
                "2. Update permissions for existing elements\n\n"
                "To proceed, please use the restore_server_confirmed command."
            )
            
        except Exception as e:
            logger.error(f"Error preparing server restore: {e}")
            return f"Error preparing server restore: {str(e)}"
            
    async def get_server_stats(self, guild_id: int) -> str:
        """
        Get statistics about a Discord server.
        
        Args:
            guild_id: The ID of the Discord server
            
        Returns:
            str: Server statistics
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            # Calculate creation date in readable format
            creation_date = guild.created_at
            created_str = f"<t:{int(creation_date.timestamp())}:F>"
            
            # Count channels by type
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            
            # Member statistics
            total_members = guild.member_count
            bots = sum(1 for member in guild.members if member.bot)
            humans = total_members - bots
            
            # Role statistics
            roles = len(guild.roles) - 1  # Exclude @everyone
            
            # Emoji statistics
            emojis = len(guild.emojis)
            emoji_limit = guild.emoji_limit
            
            # Boost status
            premium_tier = guild.premium_tier
            boosts = guild.premium_subscription_count
            
            # Format the statistics
            stats = [
                f"📊 **Server Statistics for {guild.name}**",
                f"\n**General Information:**",
                f"• ID: {guild.id}",
                f"• Owner: {guild.owner.mention if guild.owner else 'Unknown'}",
                f"• Created: {created_str}",
                f"• Region: {guild.region if hasattr(guild, 'region') else 'Auto'}",
                
                f"\n**Members:**",
                f"• Total: {total_members}",
                f"• Humans: {humans}",
                f"• Bots: {bots}",
                
                f"\n**Channels:**",
                f"• Text: {text_channels}",
                f"• Voice: {voice_channels}",
                f"• Categories: {categories}",
                f"• Total: {text_channels + voice_channels + categories}",
                
                f"\n**Other:**",
                f"• Roles: {roles}",
                f"• Emojis: {emojis}/{emoji_limit}",
                f"• Boost Level: {premium_tier}",
                f"• Boosts: {boosts}"
            ]
            
            return "\n".join(stats)
            
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            return f"Error getting server stats: {str(e)}"