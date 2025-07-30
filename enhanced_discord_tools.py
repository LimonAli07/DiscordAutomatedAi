import discord
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

# Expanded list of dangerous functions that require confirmation
DANGEROUS_FUNCTIONS = [
    'delete_channel',
    'delete_role',
    'ban_member',
    'kick_member',
    'update_role_permissions',
    'delete_message_bulk',
    'create_invite_with_perms',
    'execute_cross_server_clone',
    'delete_category_and_channels',
    'purge_messages',
    'timeout_member',
    'clean_server',
    'reset_server',
    'delete_all_channels',
    'restore_server',
    'setup_word_filter',
    'setup_anti_spam',
    'create_channel',  # Added channel creation to require confirmation
]

class DiscordTools:
    """Expanded toolbox of Discord server management functions for the AI agent."""
    
    def __init__(self, bot: discord.Client):
        self.bot = bot
    
    async def list_channels(self, guild_id: int) -> str:
        """
        List all channels in a Discord server.
        
        Args:
            guild_id (int): The ID of the Discord server
            
        Returns:
            str: A formatted list of all channels with their types and IDs
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            # Group channels by category
            channels_by_category = {}
            
            # Add uncategorized channels
            channels_by_category[None] = []
            
            for channel in guild.channels:
                if isinstance(channel, discord.CategoryChannel):
                    channels_by_category[channel] = []
            
            for channel in guild.channels:
                if not isinstance(channel, discord.CategoryChannel):
                    channels_by_category[channel.category].append(channel)
            
            # Format the output
            output_lines = [f"Channels in {guild.name}:"]
            
            # First list categories with their channels
            for category, channels in channels_by_category.items():
                if category:
                    output_lines.append(f"\n📁 {category.name} (Category) - ID: {category.id}")
                    for channel in channels:
                        channel_type = str(channel.type).replace('_', ' ').title()
                        output_lines.append(f"  {'#' if isinstance(channel, discord.TextChannel) else '🔊'} {channel.name} ({channel_type}) - ID: {channel.id}")
                
            # Then list uncategorized channels
            if channels_by_category[None]:
                output_lines.append("\n📄 Uncategorized Channels:")
                for channel in channels_by_category[None]:
                    channel_type = str(channel.type).replace('_', ' ').title()
                    output_lines.append(f"  {'#' if isinstance(channel, discord.TextChannel) else '🔊'} {channel.name} ({channel_type}) - ID: {channel.id}")
            
            if not output_lines[1:]:
                output_lines.append("No channels found in this server.")
            
            return "\n".join(output_lines)
        
        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            return f"Error listing channels: {str(e)}"
    
    async def get_channel_by_name_or_id(self, guild_id: int, channel_identifier: str) -> Optional[discord.abc.GuildChannel]:
        """
        Get a channel by its name or ID.
        
        Args:
            guild_id: The ID of the Discord server
            channel_identifier: The name or ID of the channel to find
            
        Returns:
            Optional[discord.abc.GuildChannel]: The channel object if found, None otherwise
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return None
            
            # Try to parse as ID first (if it's numeric or a mention)
            channel_id = None
            
            # Handle Discord mentions like <#1234567890>
            if channel_identifier.startswith('<#') and channel_identifier.endswith('>'):
                try:
                    channel_id = int(channel_identifier[2:-1])
                except ValueError:
                    pass
            # Handle direct ID numbers
            elif channel_identifier.isdigit():
                channel_id = int(channel_identifier)
            
            # If we have an ID, try to get channel by ID
            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel:
                    return channel
            
            # Otherwise, search by name
            # Remove # prefix if present
            channel_name = channel_identifier.lstrip('#')
            
            for channel in guild.channels:
                if channel.name.lower() == channel_name.lower():
                    return channel
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting channel by name or ID: {e}")
            return None

    async def timeout_member(self, guild_id: int, member_identifier: str, duration_minutes: int, reason: str = None) -> str:
        """
        Timeout (mute) a member in the Discord server.
        
        Args:
            guild_id: The ID of the Discord server
            member_identifier: The name or ID of the member to timeout
            duration_minutes: Duration of the timeout in minutes
            reason: Optional reason for the timeout
            
        Returns:
            str: Success or error message
        """
        try:
            member = await self.get_member_by_name_or_id(guild_id, member_identifier)
            if not member:
                return f"Error: Member '{member_identifier}' not found"
            
            if member.guild_permissions.administrator:
                return "Error: Cannot timeout administrators"
            
            # Calculate end time for the timeout
            duration = timedelta(minutes=duration_minutes)
            until = discord.utils.utcnow() + duration
            
            # Apply the timeout
            timeout_reason = reason or "Timeout applied by AI bot"
            await member.timeout(until, reason=timeout_reason)
            
            return f"✅ Successfully timed out member '{member.display_name}' for {duration_minutes} minutes"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to timeout members"
        except Exception as e:
            logger.error(f"Error timing out member: {e}")
            return f"Error timing out member: {str(e)}"
    
    async def remove_timeout(self, guild_id: int, member_identifier: str) -> str:
        """
        Remove a timeout from a member in the Discord server.
        
        Args:
            guild_id: The ID of the Discord server
            member_identifier: The name or ID of the member
            
        Returns:
            str: Success or error message
        """
        try:
            member = await self.get_member_by_name_or_id(guild_id, member_identifier)
            if not member:
                return f"Error: Member '{member_identifier}' not found"
            
            # Remove the timeout by setting it to None
            await member.timeout(None, reason="Timeout removed by AI bot")
            
            return f"✅ Successfully removed timeout from member '{member.display_name}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to manage timeouts"
        except Exception as e:
            logger.error(f"Error removing timeout: {e}")
            return f"Error removing timeout: {str(e)}"
    
    async def purge_messages(self, guild_id: int, channel_identifier: str, limit: int, from_user: Optional[str] = None) -> str:
        """
        Bulk delete messages from a channel.
        
        Args:
            guild_id: The ID of the Discord server
            channel_identifier: The name or ID of the channel
            limit: Number of messages to delete (max 100)
            from_user: Optional user ID or name to filter messages from
            
        Returns:
            str: Success or error message
        """
        try:
            # Validate the limit
            if limit <= 0 or limit > 100:
                return "Error: Limit must be between 1 and 100 messages"
            
            # Get the channel
            channel = await self.get_channel_by_name_or_id(guild_id, channel_identifier)
            if not channel:
                return f"Error: Channel '{channel_identifier}' not found"
            
            # Check if the channel is a text channel
            if not isinstance(channel, discord.TextChannel):
                return f"Error: Cannot purge messages from a {channel.type} channel"
            
            # Check if we need to filter by user
            member = None
            if from_user:
                member = await self.get_member_by_name_or_id(guild_id, from_user)
                if not member:
                    return f"Error: User '{from_user}' not found"
            
            # Define the check function if filtering by user
            def check_user(message):
                return message.author.id == member.id if member else True
            
            # Delete the messages
            deleted = await channel.purge(limit=limit, check=check_user)
            
            user_filter = f" from user '{member.display_name}'" if member else ""
            return f"✅ Successfully deleted {len(deleted)} messages{user_filter} in channel '{channel.name}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to delete messages"
        except discord.HTTPException as e:
            if e.code == 50034:
                return "Error: Cannot bulk delete messages older than 14 days"
            logger.error(f"HTTP error purging messages: {e}")
            return f"Error purging messages: {str(e)}"
        except Exception as e:
            logger.error(f"Error purging messages: {e}")
            return f"Error purging messages: {str(e)}"
    
    async def set_slowmode(self, guild_id: int, channel_identifier: str, seconds: int) -> str:
        """
        Set slowmode in a text channel.
        
        Args:
            guild_id: The ID of the Discord server
            channel_identifier: The name or ID of the channel
            seconds: Slowmode delay in seconds (0 to disable, max 21600)
            
        Returns:
            str: Success or error message
        """
        try:
            # Validate seconds
            if seconds < 0 or seconds > 21600:
                return "Error: Slowmode delay must be between 0 and 21600 seconds (6 hours)"
            
            # Get the channel
            channel = await self.get_channel_by_name_or_id(guild_id, channel_identifier)
            if not channel:
                return f"Error: Channel '{channel_identifier}' not found"
            
            # Check if the channel is a text channel
            if not isinstance(channel, discord.TextChannel):
                return f"Error: Cannot set slowmode on a {channel.type} channel"
            
            # Set slowmode
            await channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                return f"✅ Slowmode disabled for channel '{channel.name}'"
            else:
                return f"✅ Slowmode set to {seconds} seconds for channel '{channel.name}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to modify channel settings"
        except Exception as e:
            logger.error(f"Error setting slowmode: {e}")
            return f"Error setting slowmode: {str(e)}"
    
    async def lock_channel(self, guild_id: int, channel_identifier: str) -> str:
        """
        Lock a channel to prevent everyone from sending messages.
        
        Args:
            guild_id: The ID of the Discord server
            channel_identifier: The name or ID of the channel
            
        Returns:
            str: Success or error message
        """
        try:
            channel = await self.get_channel_by_name_or_id(guild_id, channel_identifier)
            if not channel:
                return f"Error: Channel '{channel_identifier}' not found"
            
            # Check if the channel is a text channel
            if not isinstance(channel, discord.TextChannel):
                return f"Error: Cannot lock a {channel.type} channel"
            
            # Get the @everyone role
            guild = self.bot.get_guild(guild_id)
            everyone_role = guild.default_role
            
            # Update permissions to prevent sending messages
            await channel.set_permissions(
                everyone_role,
                send_messages=False,
                reason="Channel locked by AI bot"
            )
            
            return f"🔒 Channel '{channel.name}' has been locked. Only staff can send messages."
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to manage channel permissions"
        except Exception as e:
            logger.error(f"Error locking channel: {e}")
            return f"Error locking channel: {str(e)}"
    
    async def unlock_channel(self, guild_id: int, channel_identifier: str) -> str:
        """
        Unlock a channel to allow everyone to send messages.
        
        Args:
            guild_id: The ID of the Discord server
            channel_identifier: The name or ID of the channel
            
        Returns:
            str: Success or error message
        """
        try:
            channel = await self.get_channel_by_name_or_id(guild_id, channel_identifier)
            if not channel:
                return f"Error: Channel '{channel_identifier}' not found"
            
            # Check if the channel is a text channel
            if not isinstance(channel, discord.TextChannel):
                return f"Error: Cannot unlock a {channel.type} channel"
            
            # Get the @everyone role
            guild = self.bot.get_guild(guild_id)
            everyone_role = guild.default_role
            
            # Update permissions to allow sending messages
            await channel.set_permissions(
                everyone_role,
                send_messages=True,
                reason="Channel unlocked by AI bot"
            )
            
            return f"🔓 Channel '{channel.name}' has been unlocked. Everyone can now send messages."
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to manage channel permissions"
        except Exception as e:
            logger.error(f"Error unlocking channel: {e}")
            return f"Error unlocking channel: {str(e)}"
    
    async def set_nickname(self, guild_id: int, member_identifier: str, nickname: Optional[str] = None) -> str:
        """
        Change a member's nickname.
        
        Args:
            guild_id: The ID of the Discord server
            member_identifier: The name or ID of the member
            nickname: The new nickname (leave empty to reset)
            
        Returns:
            str: Success or error message
        """
        try:
            member = await self.get_member_by_name_or_id(guild_id, member_identifier)
            if not member:
                return f"Error: Member '{member_identifier}' not found"
            
            # Check if trying to change a higher-up member
            if member.top_role.position >= member.guild.me.top_role.position and member.id != member.guild.owner_id:
                return "Error: Cannot change nickname of members with higher or equal roles"
            
            old_name = member.display_name
            await member.edit(nick=nickname, reason="Nickname changed by AI bot")
            
            if nickname:
                return f"✅ Changed nickname of '{old_name}' to '{nickname}'"
            else:
                return f"✅ Reset nickname of '{old_name}' to their username"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to manage nicknames"
        except Exception as e:
            logger.error(f"Error setting nickname: {e}")
            return f"Error setting nickname: {str(e)}"
    
    async def unban_member(self, guild_id: int, user_identifier: str, reason: Optional[str] = None) -> str:
        """
        Unban a member from the Discord server.
        
        Args:
            guild_id: The ID of the Discord server
            user_identifier: The ID or username of the banned user
            reason: Optional reason for the unban
            
        Returns:
            str: Success or error message
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            # Get ban entries
            bans = [entry async for entry in guild.bans()]
            
            # Try to find the banned user
            banned_user = None
            
            # If user_identifier is a user ID
            if user_identifier.isdigit():
                user_id = int(user_identifier)
                for ban_entry in bans:
                    if ban_entry.user.id == user_id:
                        banned_user = ban_entry.user
                        break
            
            # If not found by ID, try by name
            if not banned_user:
                for ban_entry in bans:
                    if (ban_entry.user.name.lower() == user_identifier.lower() or 
                        str(ban_entry.user).lower() == user_identifier.lower()):
                        banned_user = ban_entry.user
                        break
            
            if not banned_user:
                return f"Error: Could not find banned user '{user_identifier}'"
            
            # Unban the user
            unban_reason = reason or "Unbanned by AI bot"
            await guild.unban(banned_user, reason=unban_reason)
            
            return f"✅ Successfully unbanned user '{banned_user.name}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to unban members"
        except Exception as e:
            logger.error(f"Error unbanning member: {e}")
            return f"Error unbanning member: {str(e)}"
    
    # Re-implementation of the original methods from discord_tools.py
    
    async def delete_channel(self, guild_id: int, channel_identifier: str) -> str:
        """
        Delete a channel from the Discord server by name or ID.
        
        Args:
            guild_id (int): The ID of the Discord server
            channel_identifier (str): The name or ID of the channel to delete
            
        Returns:
            str: Success or error message
        """
        try:
            channel = await self.get_channel_by_name_or_id(guild_id, channel_identifier)
            if not channel:
                return f"Error: Channel '{channel_identifier}' not found"
            
            channel_name_display = channel.name
            await channel.delete(reason="Deleted by AI bot on owner's request")
            return f"Successfully deleted channel '#{channel_name_display}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to delete channels"
        except Exception as e:
            logger.error(f"Error deleting channel: {e}")
            return f"Error deleting channel: {str(e)}"
    
    async def get_member_by_name_or_id(self, guild_id: int, member_identifier: str) -> Optional[discord.Member]:
        """
        Get a member by name, nickname, mention, or ID.
        
        Args:
            guild_id: The ID of the Discord server
            member_identifier: The name, nickname, mention, or ID of the member to find
            
        Returns:
            Optional[discord.Member]: The member object if found, None otherwise
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return None
            
            # Try to parse as ID first (if it's numeric or a mention)
            member_id = None
            
            # Handle Discord mentions like <@1234567890>
            if member_identifier.startswith('<@') and member_identifier.endswith('>'):
                try:
                    # Remove <@ and > and also remove ! if present (for nicknames)
                    clean_id = member_identifier[2:-1].replace('!', '')
                    member_id = int(clean_id)
                except ValueError:
                    pass
            # Handle direct ID numbers
            elif member_identifier.isdigit():
                member_id = int(member_identifier)
            
            # If we have an ID, try to get member by ID
            if member_id:
                member = guild.get_member(member_id)
                if member:
                    return member
            
            # Otherwise, search by name or nickname
            lower_identifier = member_identifier.lower()
            
            for member in guild.members:
                # Check username
                if member.name.lower() == lower_identifier:
                    return member
                
                # Check nickname
                if member.nick and member.nick.lower() == lower_identifier:
                    return member
                
                # Check full name with discriminator
                if str(member).lower() == lower_identifier:
                    return member
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting member by name or ID: {e}")
            return None
    
    async def create_channel(self, guild_id: int, channel_name: str, channel_type: str = "text", category: str = None) -> str:
        """
        Create a new channel in the Discord server.
        
        Args:
            guild_id: The ID of the Discord server
            channel_name: The name for the new channel
            channel_type: The type of channel ('text', 'voice', or 'category')
            category: Optional category name or ID to place the channel in
            
        Returns:
            str: Success or error message
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"❌ Error: Could not find guild with ID {guild_id}"
            
            # Check bot permissions
            bot_member = guild.get_member(self.bot.user.id)
            if not bot_member:
                return f"❌ Error: Bot is not a member of guild {guild.name}"
            
            # Check specific permissions needed
            required_perms = bot_member.guild_permissions
            if not required_perms.manage_channels:
                return f"❌ Error: Bot lacks 'Manage Channels' permission in {guild.name}. Please give the bot this permission."
            
            logger.info(f"Creating {channel_type} channel '{channel_name}' in guild {guild.name} (ID: {guild_id})")
            
            # Validate channel type
            if channel_type not in ["text", "voice", "category"]:
                return f"❌ Error: Invalid channel type '{channel_type}'. Must be 'text', 'voice', or 'category'."
            
            # Find category if specified
            target_category = None
            if category and channel_type != "category":
                for cat in guild.categories:
                    if cat.name.lower() == category.lower() or str(cat.id) == category:
                        target_category = cat
                        break
                
                if not target_category and category:
                    return f"❌ Error: Could not find category '{category}'"
            
            # Create the channel
            if channel_type == "category":
                new_channel = await guild.create_category(
                    name=channel_name,
                    reason=f"Created by AI bot for user {bot_member.display_name}"
                )
                logger.info(f"Successfully created category '{channel_name}' (ID: {new_channel.id})")
                return f"✅ Successfully created category '{channel_name}' (ID: {new_channel.id})"
            elif channel_type == "text":
                new_channel = await guild.create_text_channel(
                    name=channel_name,
                    category=target_category,
                    reason=f"Created by AI bot for user {bot_member.display_name}"
                )
                category_info = f" in category '{target_category.name}'" if target_category else ""
                logger.info(f"Successfully created text channel '{channel_name}' (ID: {new_channel.id}){category_info}")
                return f"✅ Successfully created text channel #{channel_name} (ID: {new_channel.id}){category_info}"
            elif channel_type == "voice":
                new_channel = await guild.create_voice_channel(
                    name=channel_name,
                    category=target_category,
                    reason=f"Created by AI bot for user {bot_member.display_name}"
                )
                category_info = f" in category '{target_category.name}'" if target_category else ""
                logger.info(f"Successfully created voice channel '{channel_name}' (ID: {new_channel.id}){category_info}")
                return f"✅ Successfully created voice channel 🔊{channel_name} (ID: {new_channel.id}){category_info}"
        
        except discord.Forbidden as e:
            error_msg = f"❌ Permission Error: Bot doesn't have permission to create channels in {guild.name if guild else 'unknown guild'}. Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except discord.HTTPException as e:
            error_msg = f"❌ Discord API Error: {str(e)}"
            logger.error(f"HTTP error creating channel: {e}")
            return error_msg
        except Exception as e:
            error_msg = f"❌ Unexpected error creating channel: {str(e)}"
            logger.error(f"Error creating channel: {e}")
            return error_msg
    
    # Other methods from original discord_tools.py
    async def create_role(self, guild_id: int, role_name: str, color: str = None, permissions: List[str] = None) -> str:
        """
        Create a new role in the Discord server.
        
        Args:
            guild_id: The ID of the Discord server
            role_name: Name for the new role
            color: Hex color code or color name
            permissions: List of permission names to grant
            
        Returns:
            str: Success message with role details
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            # Parse color
            role_color = discord.Color.default()
            if color:
                if color.startswith("#"):
                    # Hex color
                    try:
                        role_color = discord.Color(int(color[1:], 16))
                    except ValueError:
                        return f"Error: Invalid hex color '{color}'. Use format #RRGGBB"
                else:
                    # Named colors
                    color_map = {
                        "red": discord.Color.red(),
                        "blue": discord.Color.blue(),
                        "green": discord.Color.green(),
                        "yellow": discord.Color.yellow(),
                        "orange": discord.Color.orange(),
                        "purple": discord.Color.purple(),
                        "pink": discord.Color.from_rgb(255, 192, 203),
                        "white": discord.Color.from_rgb(255, 255, 255),
                        "black": discord.Color.from_rgb(0, 0, 0),
                        "gold": discord.Color.gold(),
                        "cyan": discord.Color.from_rgb(0, 255, 255),
                        "magenta": discord.Color.magenta()
                    }
                    role_color = color_map.get(color.lower(), discord.Color.default())
            
            # Set up permissions
            role_permissions = discord.Permissions.none()
            if permissions:
                for perm in permissions:
                    if hasattr(discord.Permissions, perm.lower()):
                        setattr(role_permissions, perm.lower(), True)
            
            # Create the role
            new_role = await guild.create_role(
                name=role_name,
                color=role_color,
                permissions=role_permissions,
                reason="Created by AI bot"
            )
            
            color_hex = f"#{role_color.value:06x}" if role_color != discord.Color.default() else "default"
            perm_list = [perm for perm, value in role_permissions if value] if permissions else ["none"]
            
            return f"✅ Successfully created role '{role_name}' (ID: {new_role.id})\nColor: {color_hex}\nPermissions: {', '.join(perm_list) if perm_list != ['none'] else 'none'}"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to create roles"
        except Exception as e:
            logger.error(f"Error creating role: {e}")
            return f"Error creating role: {str(e)}"
    
    async def list_roles(self, guild_id: int) -> str:
        """
        List all roles in a Discord server.
        
        Args:
            guild_id: The ID of the Discord server
            
        Returns:
            str: A formatted list of all roles with their IDs and permissions
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)
            
            output_lines = [f"Roles in {guild.name}:"]
            
            for role in roles:
                # Skip @everyone role in detailed listing but mention it
                if role.name == "@everyone":
                    output_lines.append(f"👥 @everyone (Default Role) - ID: {role.id} - Members: {len(role.members)}")
                    continue
                
                # Get role color
                color_hex = f"#{role.color.value:06x}" if role.color.value != 0 else "No color"
                
                # Count members with this role
                member_count = len(role.members)
                
                # Check if role is hoisted (displayed separately)
                hoist_status = "📌 Hoisted" if role.hoist else ""
                
                # Check if role is mentionable
                mention_status = "📢 Mentionable" if role.mentionable else ""
                
                # Combine status indicators
                status_indicators = " ".join(filter(None, [hoist_status, mention_status]))
                
                output_lines.append(
                    f"🎭 {role.name} - ID: {role.id} - Color: {color_hex} - Members: {member_count}"
                    + (f" - {status_indicators}" if status_indicators else "")
                )
            
            if len(roles) <= 1:  # Only @everyone
                output_lines.append("No custom roles found in this server.")
            
            return "\n".join(output_lines)
        
        except Exception as e:
            logger.error(f"Error listing roles: {e}")
            return f"Error listing roles: {str(e)}"
    
    async def kick_member(self, guild_id: int, member_identifier: str, reason: str = None) -> str:
        """
        Kick a member from the Discord server.
        
        Args:
            guild_id: The ID of the Discord server
            member_identifier: The name, nickname, or ID of the member to kick
            reason: Optional reason for the kick
            
        Returns:
            str: Success or error message
        """
        try:
            member = await self.get_member_by_name_or_id(guild_id, member_identifier)
            if not member:
                return f"Error: Member '{member_identifier}' not found"
            
            # Check if we can kick this member
            guild = self.bot.get_guild(guild_id)
            bot_member = guild.get_member(self.bot.user.id)
            
            if member.top_role.position >= bot_member.top_role.position:
                return "Error: Cannot kick members with higher or equal roles"
            
            if member.guild_permissions.administrator:
                return "Error: Cannot kick administrators"
            
            # Kick the member
            kick_reason = reason or "Kicked by AI bot"
            await member.kick(reason=kick_reason)
            
            return f"✅ Successfully kicked member '{member.display_name}' from the server"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to kick members"
        except Exception as e:
            logger.error(f"Error kicking member: {e}")
            return f"Error kicking member: {str(e)}"
    
    async def ban_member(self, guild_id: int, member_identifier: str, reason: str = None, delete_message_days: int = 0) -> str:
        """
        Ban a member from the Discord server.
        
        Args:
            guild_id: The ID of the Discord server
            member_identifier: The name, nickname, or ID of the member to ban
            reason: Optional reason for the ban
            delete_message_days: Number of days of messages to delete (0-7)
            
        Returns:
            str: Success or error message
        """
        try:
            member = await self.get_member_by_name_or_id(guild_id, member_identifier)
            if not member:
                return f"Error: Member '{member_identifier}' not found"
            
            # Check if we can ban this member
            guild = self.bot.get_guild(guild_id)
            bot_member = guild.get_member(self.bot.user.id)
            
            if member.top_role.position >= bot_member.top_role.position:
                return "Error: Cannot ban members with higher or equal roles"
            
            if member.guild_permissions.administrator:
                return "Error: Cannot ban administrators"
            
            # Validate delete_message_days
            if delete_message_days < 0 or delete_message_days > 7:
                delete_message_days = 0
            
            # Ban the member
            ban_reason = reason or "Banned by AI bot"
            await member.ban(reason=ban_reason, delete_message_days=delete_message_days)
            
            return f"✅ Successfully banned member '{member.display_name}' from the server"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to ban members"
        except Exception as e:
            logger.error(f"Error banning member: {e}")
            return f"Error banning member: {str(e)}"