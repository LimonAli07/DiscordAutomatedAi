import discord
import asyncio
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# List of dangerous functions that require confirmation
DANGEROUS_FUNCTIONS = [
    'delete_channel',
    'delete_role',
    'ban_member',
    'kick_member',
    'update_role_permissions',
    'delete_message_bulk',
    'create_invite_with_perms'
]

class DiscordTools:
    """Toolbox of Discord server management functions for the AI agent."""
    
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
            
            channels_info = []
            for channel in guild.channels:
                channel_type = str(channel.type).replace('_', ' ').title()
                channels_info.append(f"#{channel.name} ({channel_type}) - ID: {channel.id}")
            
            if not channels_info:
                return "No channels found in this server."
            
            return f"Channels in {guild.name}:\n" + "\n".join(channels_info)
        
        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            return f"Error listing channels: {str(e)}"
    
    async def get_channel_by_name(self, guild_id: int, channel_name: str) -> Optional[discord.abc.GuildChannel]:
        """
        Get a channel by its name.
        
        Args:
            guild_id (int): The ID of the Discord server
            channel_name (str): The name of the channel to find
            
        Returns:
            Optional[discord.abc.GuildChannel]: The channel object if found, None otherwise
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return None
            
            # Remove # prefix if present
            channel_name = channel_name.lstrip('#')
            
            for channel in guild.channels:
                if channel.name.lower() == channel_name.lower():
                    return channel
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting channel by name: {e}")
            return None
    
    async def delete_channel(self, guild_id: int, channel_name: str) -> str:
        """
        Delete a channel from the Discord server.
        
        Args:
            guild_id (int): The ID of the Discord server
            channel_name (str): The name of the channel to delete
            
        Returns:
            str: Success or error message
        """
        try:
            channel = await self.get_channel_by_name(guild_id, channel_name)
            if not channel:
                return f"Error: Channel '{channel_name}' not found"
            
            channel_name_display = channel.name
            await channel.delete(reason="Deleted by AI bot on owner's request")
            return f"Successfully deleted channel '#{channel_name_display}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to delete channels"
        except Exception as e:
            logger.error(f"Error deleting channel: {e}")
            return f"Error deleting channel: {str(e)}"
    
    async def list_roles(self, guild_id: int) -> str:
        """
        List all roles in a Discord server.
        
        Args:
            guild_id (int): The ID of the Discord server
            
        Returns:
            str: A formatted list of all roles with their IDs and member counts
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            roles_info = []
            for role in guild.roles:
                if role.name != "@everyone":  # Skip @everyone role
                    member_count = len(role.members)
                    roles_info.append(f"{role.name} - ID: {role.id} ({member_count} members)")
            
            if not roles_info:
                return "No custom roles found in this server."
            
            return f"Roles in {guild.name}:\n" + "\n".join(roles_info)
        
        except Exception as e:
            logger.error(f"Error listing roles: {e}")
            return f"Error listing roles: {str(e)}"
    
    async def get_role_by_name(self, guild_id: int, role_name: str) -> Optional[discord.Role]:
        """
        Get a role by its name.
        
        Args:
            guild_id (int): The ID of the Discord server
            role_name (str): The name of the role to find
            
        Returns:
            Optional[discord.Role]: The role object if found, None otherwise
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return None
            
            for role in guild.roles:
                if role.name.lower() == role_name.lower():
                    return role
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting role by name: {e}")
            return None
    
    async def create_channel(self, guild_id: int, channel_name: str, channel_type: str = "text") -> str:
        """
        Create a new channel in the Discord server.
        
        Args:
            guild_id (int): The ID of the Discord server
            channel_name (str): The name for the new channel
            channel_type (str): The type of channel ("text" or "voice")
            
        Returns:
            str: Success or error message
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            # Check if channel already exists
            existing_channel = await self.get_channel_by_name(guild_id, channel_name)
            if existing_channel:
                return f"Error: Channel '{channel_name}' already exists"
            
            if channel_type.lower() == "voice":
                channel = await guild.create_voice_channel(
                    name=channel_name,
                    reason="Created by AI bot on owner's request"
                )
            else:
                channel = await guild.create_text_channel(
                    name=channel_name,
                    reason="Created by AI bot on owner's request"
                )
            
            return f"Successfully created {channel_type} channel '#{channel.name}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to create channels"
        except Exception as e:
            logger.error(f"Error creating channel: {e}")
            return f"Error creating channel: {str(e)}"
    
    async def list_members(self, guild_id: int, limit: int = 50) -> str:
        """
        List members in a Discord server.
        
        Args:
            guild_id (int): The ID of the Discord server
            limit (int): Maximum number of members to list (default: 50)
            
        Returns:
            str: A formatted list of members
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            members_info = []
            count = 0
            
            for member in guild.members:
                if count >= limit:
                    break
                
                status = "Bot" if member.bot else "User"
                members_info.append(f"{member.display_name} ({member.name}) - {status} - ID: {member.id}")
                count += 1
            
            total_members = guild.member_count
            result = f"Members in {guild.name} (showing {len(members_info)} of {total_members}):\n"
            result += "\n".join(members_info)
            
            if total_members > limit:
                result += f"\n... and {total_members - limit} more members"
            
            return result
        
        except Exception as e:
            logger.error(f"Error listing members: {e}")
            return f"Error listing members: {str(e)}"
    
    async def get_server_info(self, guild_id: int) -> str:
        """
        Get general information about a Discord server.
        
        Args:
            guild_id (int): The ID of the Discord server
            
        Returns:
            str: Formatted server information
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            info = f"Server Information for {guild.name}:\n"
            info += f"ID: {guild.id}\n"
            info += f"Owner: {guild.owner.display_name if guild.owner else 'Unknown'}\n"
            info += f"Members: {guild.member_count}\n"
            info += f"Channels: {len(guild.channels)}\n"
            info += f"Roles: {len(guild.roles)}\n"
            info += f"Created: {guild.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            
            # Get verification level
            verification_levels = {
                discord.VerificationLevel.none: "None",
                discord.VerificationLevel.low: "Low",
                discord.VerificationLevel.medium: "Medium",
                discord.VerificationLevel.high: "High",
                discord.VerificationLevel.highest: "Highest"
            }
            info += f"Verification Level: {verification_levels.get(guild.verification_level, 'Unknown')}\n"
            
            return info
        
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            return f"Error getting server info: {str(e)}"
