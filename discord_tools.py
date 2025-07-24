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
    'create_invite_with_perms',
    'execute_cross_server_clone'
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
    
    async def get_channel_by_name_or_id(self, guild_id: int, channel_identifier: str) -> Optional[discord.abc.GuildChannel]:
        """
        Get a channel by its name or ID.
        
        Args:
            guild_id (int): The ID of the Discord server
            channel_identifier (str): The name or ID of the channel to find
            
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
    
    async def get_role_by_name_or_id(self, guild_id: int, role_identifier: str) -> Optional[discord.Role]:
        """
        Get a role by its name or ID.
        
        Args:
            guild_id (int): The ID of the Discord server
            role_identifier (str): The name or ID of the role to find
            
        Returns:
            Optional[discord.Role]: The role object if found, None otherwise
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return None
            
            # Try to parse as ID first (if it's numeric or a mention)
            role_id = None
            
            # Handle Discord mentions like <@&1234567890>
            if role_identifier.startswith('<@&') and role_identifier.endswith('>'):
                try:
                    role_id = int(role_identifier[3:-1])
                except ValueError:
                    pass
            # Handle direct ID numbers
            elif role_identifier.isdigit():
                role_id = int(role_identifier)
            
            # If we have an ID, try to get role by ID
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    return role
            
            # Otherwise, search by name
            for role in guild.roles:
                if role.name.lower() == role_identifier.lower():
                    return role
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting role by name or ID: {e}")
            return None
    
    async def delete_role(self, guild_id: int, role_identifier: str) -> str:
        """
        Delete a role from the Discord server by name or ID.
        
        Args:
            guild_id (int): The ID of the Discord server
            role_identifier (str): The name or ID of the role to delete
            
        Returns:
            str: Success or error message
        """
        try:
            role = await self.get_role_by_name_or_id(guild_id, role_identifier)
            if not role:
                return f"Error: Role '{role_identifier}' not found"
            
            if role.name == "@everyone":
                return "Error: Cannot delete the @everyone role"
            
            role_name_display = role.name
            await role.delete(reason="Deleted by AI bot on owner's request")
            return f"Successfully deleted role '{role_name_display}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to delete roles"
        except Exception as e:
            logger.error(f"Error deleting role: {e}")
            return f"Error deleting role: {str(e)}"
    
    async def get_member_by_name_or_id(self, guild_id: int, member_identifier: str) -> Optional[discord.Member]:
        """
        Get a member by their name, display name, or ID.
        
        Args:
            guild_id (int): The ID of the Discord server
            member_identifier (str): The name, display name, or ID of the member to find
            
        Returns:
            Optional[discord.Member]: The member object if found, None otherwise
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return None
            
            # Try to parse as ID first (if it's numeric or a mention)
            member_id = None
            
            # Handle Discord mentions like <@1234567890> or <@!1234567890>
            if member_identifier.startswith('<@') and member_identifier.endswith('>'):
                try:
                    # Remove <@ and > and handle optional !
                    id_str = member_identifier[2:-1].lstrip('!')
                    member_id = int(id_str)
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
            
            # Otherwise, search by name or display name
            for member in guild.members:
                if (member.name.lower() == member_identifier.lower() or 
                    member.display_name.lower() == member_identifier.lower()):
                    return member
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting member by name or ID: {e}")
            return None
    
    async def kick_member(self, guild_id: int, member_identifier: str, reason: str = None) -> str:
        """
        Kick a member from the Discord server by name or ID.
        
        Args:
            guild_id (int): The ID of the Discord server
            member_identifier (str): The name or ID of the member to kick
            reason (str): Optional reason for the kick
            
        Returns:
            str: Success or error message
        """
        try:
            member = await self.get_member_by_name_or_id(guild_id, member_identifier)
            if not member:
                return f"Error: Member '{member_identifier}' not found"
            
            if member.guild_permissions.administrator:
                return "Error: Cannot kick administrators"
            
            member_name = member.display_name
            kick_reason = reason or "Kicked by AI bot on owner's request"
            await member.kick(reason=kick_reason)
            return f"Successfully kicked member '{member_name}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to kick members"
        except Exception as e:
            logger.error(f"Error kicking member: {e}")
            return f"Error kicking member: {str(e)}"
    
    async def ban_member(self, guild_id: int, member_identifier: str, reason: str = None) -> str:
        """
        Ban a member from the Discord server by name or ID.
        
        Args:
            guild_id (int): The ID of the Discord server
            member_identifier (str): The name or ID of the member to ban
            reason (str): Optional reason for the ban
            
        Returns:
            str: Success or error message
        """
        try:
            member = await self.get_member_by_name_or_id(guild_id, member_identifier)
            if not member:
                return f"Error: Member '{member_identifier}' not found"
            
            if member.guild_permissions.administrator:
                return "Error: Cannot ban administrators"
            
            member_name = member.display_name
            ban_reason = reason or "Banned by AI bot on owner's request"
            await member.ban(reason=ban_reason)
            return f"Successfully banned member '{member_name}'"
        
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to ban members"
        except Exception as e:
            logger.error(f"Error banning member: {e}")
            return f"Error banning member: {str(e)}"
    
    async def prepare_cross_server_clone(self, source_guild_id: int, clone_type: str) -> str:
        """
        Prepare cross-server cloning by storing source server data.
        
        Args:
            source_guild_id (int): The ID of the source Discord server
            clone_type (str): What to clone ("channels", "roles", or "both")
            
        Returns:
            str: Success message with data summary
        """
        try:
            guild = self.bot.get_guild(source_guild_id)
            if not guild:
                return f"Error: Could not find source server with ID {source_guild_id}"
            
            clone_data = {
                "source_guild_id": source_guild_id,
                "source_guild_name": guild.name,
                "clone_type": clone_type,
                "channels": [],
                "roles": []
            }
            
            if clone_type in ["channels", "both"]:
                for channel in guild.channels:
                    if isinstance(channel, discord.TextChannel):
                        clone_data["channels"].append({
                            "name": channel.name,
                            "type": "text",
                            "topic": channel.topic,
                            "position": channel.position,
                            "category": channel.category.name if channel.category else None
                        })
                    elif isinstance(channel, discord.VoiceChannel):
                        clone_data["channels"].append({
                            "name": channel.name,
                            "type": "voice",
                            "user_limit": channel.user_limit,
                            "position": channel.position,
                            "category": channel.category.name if channel.category else None
                        })
            
            if clone_type in ["roles", "both"]:
                for role in guild.roles:
                    if role.name != "@everyone" and not role.managed:
                        clone_data["roles"].append({
                            "name": role.name,
                            "color": role.color.value,
                            "permissions": role.permissions.value,
                            "hoist": role.hoist,
                            "mentionable": role.mentionable,
                            "position": role.position
                        })
            
            # Store the data in agent's cross_server_data (we'll access it via bot reference)
            if hasattr(self.bot, 'ai_agent') and hasattr(self.bot.ai_agent, 'cross_server_data'):
                # This will be set by the caller with user_id
                self.bot.ai_agent._temp_clone_data = clone_data
            
            channel_count = len(clone_data["channels"])
            role_count = len(clone_data["roles"])
            
            return f"✅ Prepared to clone from '{guild.name}':\n" + \
                   f"- {channel_count} channels\n" + \
                   f"- {role_count} roles\n\n" + \
                   f"Now use the command in your target server to execute the clone."
        
        except Exception as e:
            logger.error(f"Error preparing cross-server clone: {e}")
            return f"Error preparing clone: {str(e)}"
    
    async def execute_cross_server_clone(self, target_guild_id: int, user_id: int) -> str:
        """
        Execute the prepared cross-server clone operation.
        
        Args:
            target_guild_id (int): The ID of the target Discord server
            user_id (int): The user ID to get stored clone data
            
        Returns:
            str: Success or error message
        """
        try:
            # Get stored clone data
            if not (hasattr(self.bot, 'ai_agent') and 
                   hasattr(self.bot.ai_agent, '_temp_clone_data')):
                return "Error: No clone data prepared. Please use 'prepare clone' first in the source server."
            
            clone_data = self.bot.ai_agent._temp_clone_data
            target_guild = self.bot.get_guild(target_guild_id)
            
            if not target_guild:
                return f"Error: Could not find target server with ID {target_guild_id}"
            
            results = []
            
            # Clone channels
            if clone_data["clone_type"] in ["channels", "both"]:
                for channel_data in clone_data["channels"]:
                    try:
                        if channel_data["type"] == "text":
                            await target_guild.create_text_channel(
                                name=channel_data["name"],
                                topic=channel_data["topic"]
                            )
                        elif channel_data["type"] == "voice":
                            await target_guild.create_voice_channel(
                                name=channel_data["name"],
                                user_limit=channel_data["user_limit"]
                            )
                        results.append(f"✅ Created channel: {channel_data['name']}")
                    except Exception as e:
                        results.append(f"❌ Failed to create channel {channel_data['name']}: {str(e)}")
            
            # Clone roles
            if clone_data["clone_type"] in ["roles", "both"]:
                for role_data in clone_data["roles"]:
                    try:
                        await target_guild.create_role(
                            name=role_data["name"],
                            color=discord.Color(role_data["color"]),
                            permissions=discord.Permissions(role_data["permissions"]),
                            hoist=role_data["hoist"],
                            mentionable=role_data["mentionable"]
                        )
                        results.append(f"✅ Created role: {role_data['name']}")
                    except Exception as e:
                        results.append(f"❌ Failed to create role {role_data['name']}: {str(e)}")
            
            # Clear the temporary data
            if hasattr(self.bot.ai_agent, '_temp_clone_data'):
                delattr(self.bot.ai_agent, '_temp_clone_data')
            
            summary = f"🎉 Clone operation completed from '{clone_data['source_guild_name']}' to '{target_guild.name}':\n\n"
            summary += "\n".join(results)
            
            return summary
        
        except Exception as e:
            logger.error(f"Error executing cross-server clone: {e}")
            return f"Error executing clone: {str(e)}"
    
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
