import discord
import logging
from typing import List, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class RoleManagement:
    """Role management functions for the Discord bot."""
    
    def __init__(self, bot: discord.Client):
        self.bot = bot
    
    async def assign_role(self, guild_id: int, member_identifier: str, role_identifier: str) -> str:
        """
        Assign a role to a member.
        
        Args:
            guild_id: The ID of the Discord server
            member_identifier: The name or ID of the member
            role_identifier: The name or ID of the role
            
        Returns:
            str: Success or error message
        """
        try:
            from enhanced_discord_tools import DiscordTools
            tools = DiscordTools(self.bot)
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            # Get the member
            member = await tools.get_member_by_name_or_id(guild_id, member_identifier)
            if not member:
                return f"Error: Member '{member_identifier}' not found"
                
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
                return "Error: Cannot assign a role that is higher than or equal to the bot's highest role"
                
            # Add the role to the member
            if role in member.roles:
                return f"Member '{member.display_name}' already has the role '{role.name}'"
                
            await member.add_roles(role, reason="Role assigned by AI bot")
            return f"✅ Successfully assigned role '{role.name}' to '{member.display_name}'"
            
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to manage roles"
        except Exception as e:
            logger.error(f"Error assigning role: {e}")
            return f"Error assigning role: {str(e)}"
            
    async def remove_role(self, guild_id: int, member_identifier: str, role_identifier: str) -> str:
        """
        Remove a role from a member.
        
        Args:
            guild_id: The ID of the Discord server
            member_identifier: The name or ID of the member
            role_identifier: The name or ID of the role
            
        Returns:
            str: Success or error message
        """
        try:
            from enhanced_discord_tools import DiscordTools
            tools = DiscordTools(self.bot)
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
                
            # Get the member
            member = await tools.get_member_by_name_or_id(guild_id, member_identifier)
            if not member:
                return f"Error: Member '{member_identifier}' not found"
                
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
                return "Error: Cannot remove a role that is higher than or equal to the bot's highest role"
                
            # Remove the role from the member
            if role not in member.roles:
                return f"Member '{member.display_name}' doesn't have the role '{role.name}'"
                
            await member.remove_roles(role, reason="Role removed by AI bot")
            return f"✅ Successfully removed role '{role.name}' from '{member.display_name}'"
            
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to manage roles"
        except Exception as e:
            logger.error(f"Error removing role: {e}")
            return f"Error removing role: {str(e)}"
            
    async def update_role_permissions(self, guild_id: int, role_identifier: str, permissions: List[str], remove: bool = False) -> str:
        """
        Update permissions for a role.
        
        Args:
            guild_id: The ID of the Discord server
            role_identifier: The name or ID of the role
            permissions: List of permission names to grant or remove
            remove: If True, remove these permissions instead of adding them
            
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
                return "Error: Cannot modify a role that is higher than or equal to the bot's highest role"
                
            # Get the current permissions
            current_perms = role.permissions
            
            # Update permissions
            for perm in permissions:
                if hasattr(discord.Permissions, perm.lower()):
                    setattr(current_perms, perm.lower(), not remove)
                else:
                    return f"Error: Unknown permission '{perm}'"
                    
            # Update the role
            await role.edit(permissions=current_perms, reason=f"Permissions {'removed from' if remove else 'added to'} role by AI bot")
            
            action = "Removed" if remove else "Added"
            return f"✅ {action} permissions ({', '.join(permissions)}) {'from' if remove else 'to'} role '{role.name}'"
            
        except discord.Forbidden:
            return "Error: Bot doesn't have permission to manage roles"
        except Exception as e:
            logger.error(f"Error updating role permissions: {e}")
            return f"Error updating role permissions: {str(e)}"