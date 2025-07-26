import json
import logging
import asyncio
import discord
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from pydantic import BaseModel

from config import config
from discord_tools import DiscordTools, DANGEROUS_FUNCTIONS
from api_manager import APIManager

logger = logging.getLogger(__name__)

class FunctionCall(BaseModel):
    """Model for function call responses."""
    name: str
    args: Dict[str, Any]

class DiscordAgent:
    """AI agent that manages Discord server operations using multiple AI providers."""
    
    def __init__(self, bot: discord.Client, api_manager: APIManager):
        self.bot = bot
        self.discord_tools = DiscordTools(bot)
        self.api_manager = api_manager
        
        self.pending_confirmations: Dict[int, Dict[str, Any]] = {}
        self.confirmation_expiry_tasks: Dict[int, asyncio.Task] = {}
        
        # Track cross-server operations
        self.cross_server_data: Dict[int, Dict[str, Any]] = {}  # user_id -> stored data
        
        # Build the function schema 
        self.function_schemas = self._build_function_schemas()
    
    def _build_function_schemas(self) -> List[Dict[str, Any]]:
        """Build function schemas for AI providers based on available Discord tools."""
        schemas = [
            {
                "name": "list_channels",
                "description": "List all channels in a Discord server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        }
                    },
                    "required": ["guild_id"]
                }
            },
            {
                "name": "delete_channel",
                "description": "Delete a channel from the Discord server (DANGEROUS - requires confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "channel_identifier": {
                            "type": "string",
                            "description": "The name or ID of the channel to delete"
                        }
                    },
                    "required": ["guild_id", "channel_identifier"]
                }
            },
            {
                "name": "delete_category_and_channels",
                "description": "Delete an entire category and all its channels (DANGEROUS - requires confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "category_identifier": {
                            "type": "string",
                            "description": "The name or ID of the category to delete"
                        }
                    },
                    "required": ["guild_id", "category_identifier"]
                }
            },
            {
                "name": "create_channel",
                "description": "Create a new channel in the Discord server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "channel_name": {
                            "type": "string",
                            "description": "The name for the new channel"
                        },
                        "channel_type": {
                            "type": "string",
                            "description": "The type of channel ('text', 'voice', or 'category')",
                            "enum": ["text", "voice", "category"]
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category name or ID to place the channel in"
                        }
                    },
                    "required": ["guild_id", "channel_name"]
                }
            },
            {
                "name": "list_roles",
                "description": "List all roles in a Discord server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        }
                    },
                    "required": ["guild_id"]
                }
            },
            {
                "name": "create_role",
                "description": "Create a new role in the Discord server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "role_name": {
                            "type": "string", 
                            "description": "Name for the new role"
                        },
                        "color": {
                            "type": "string",
                            "description": "Hex color code (e.g., '#FF0000') or color name (e.g., 'red')"
                        },
                        "permissions": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of permission names to grant to the role"
                        }
                    },
                    "required": ["guild_id", "role_name"]
                }
            },
            {
                "name": "delete_role",
                "description": "Delete a role from the Discord server (DANGEROUS - requires confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "role_identifier": {
                            "type": "string",
                            "description": "The name or ID of the role to delete"
                        }
                    },
                    "required": ["guild_id", "role_identifier"]
                }
            },
            {
                "name": "kick_member",
                "description": "Kick a member from the Discord server (DANGEROUS - requires confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "member_identifier": {
                            "type": "string",
                            "description": "The name or ID of the member to kick"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Optional reason for the kick"
                        }
                    },
                    "required": ["guild_id", "member_identifier"]
                }
            },
            {
                "name": "ban_member",
                "description": "Ban a member from the Discord server (DANGEROUS - requires confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "member_identifier": {
                            "type": "string",
                            "description": "The name or ID of the member to ban"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Optional reason for the ban"
                        },
                        "delete_message_days": {
                            "type": "integer",
                            "description": "Number of days of messages to delete (0-7)"
                        }
                    },
                    "required": ["guild_id", "member_identifier"]
                }
            },
            {
                "name": "get_api_status",
                "description": "Get status information about the AI providers",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        return schemas
    
    async def process_command(self, message_or_interaction: Union[discord.Message, discord.Interaction], user_prompt: str) -> str:
        """
        Process a natural language command using the AI system.
        
        Args:
            message_or_interaction: Discord Message or Interaction object
            user_prompt: The user's natural language instruction
            
        Returns:
            str: The final response to send back to the user
        """
        try:
            # Extract info based on message type
            if isinstance(message_or_interaction, discord.Message):
                message = message_or_interaction
                author = message.author
                channel = message.channel
                guild = message.guild
                guild_id = guild.id if guild else None
            else:  # Interaction
                interaction = message_or_interaction
                author = interaction.user
                channel = interaction.channel
                guild = interaction.guild
                guild_id = guild.id if guild else None
            
            if not guild_id:
                return "Error: This command can only be used in a server, not in DMs."
            
            # Check if user is trying to operate in a different server than their session
            user_id = author.id
            bot_session_guild = getattr(self.bot, 'user_sessions', {}).get(user_id)
            
            # Allow cross-server operations for cloning or if session not set
            is_cross_server_operation = any(word in user_prompt.lower() for word in [
                'clone', 'duplicate', 'copy', 'transfer', 'from here to another', 'to another server'
            ])
            
            if bot_session_guild and bot_session_guild != guild_id and not is_cross_server_operation:
                current_guild = self.bot.get_guild(bot_session_guild)
                return f"I'm currently focused on server '{current_guild.name if current_guild else 'Unknown'}'. Please continue our conversation there, or use a cross-server command like 'clone' if you want to work between servers."
            
            # Store current user for cross-server operations
            self._current_user_id = user_id
            
            # Clear any pending confirmations when starting new command
            if user_id in self.pending_confirmations:
                if user_id in self.confirmation_expiry_tasks:
                    self.confirmation_expiry_tasks[user_id].cancel()
                    del self.confirmation_expiry_tasks[user_id]
                del self.pending_confirmations[user_id]
            
            # Create the system prompt with context
            system_prompt = f"""You are a Discord server management AI assistant. You have access to various Discord server management functions.

Current context:
- Server ID: {guild_id}
- Server Name: {guild.name}
- User: {author.display_name}

You can use the following functions to help manage the Discord server:
{json.dumps(self.function_schemas, indent=2)}

When a user asks you to perform an action, analyze their request and use the appropriate function(s). 
Be helpful and provide clear feedback about what actions you're taking.

IMPORTANT: Some functions are marked as DANGEROUS and require confirmation. If you need to use a dangerous function, explain what you're about to do clearly.

IMPORTANT: Reply with only a single response to the user's message. Don't generate follow-up messages or questions - the user will need to send a new message for each command."""
            
            # Start conversation with AI
            response = await self._call_ai_with_tools(system_prompt, user_prompt, message_or_interaction)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return f"An error occurred while processing your request: {str(e)}"
    
    async def _call_ai_with_tools(self, system_prompt: str, user_prompt: str, message_or_interaction: Union[discord.Message, discord.Interaction]) -> str:
        """
        Call AI API with function calling capabilities.
        
        Args:
            system_prompt: The system instruction
            user_prompt: The user's prompt
            message_or_interaction: Discord Message or Interaction object
            
        Returns:
            str: The final response from the AI
        """
        try:
            # Convert function schemas to tools format
            tools = []
            for schema in self.function_schemas:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": schema["name"],
                        "description": schema["description"],
                        "parameters": schema["parameters"]
                    }
                })
            
            # Make the request to the API manager with failover support
            response = await self.api_manager.call_api_with_fallback(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                tools=tools
            )
            
            # Track which provider was used
            provider_used = response.get("provider", "unknown")
            
            # Check if AI wants to call functions
            if response.get("tool_calls"):
                function_responses = []
                
                for tool_call in response["tool_calls"]:
                    function_name = tool_call["name"]
                    function_args = tool_call["args"]
                    
                    # Check if this is a dangerous function
                    if function_name in DANGEROUS_FUNCTIONS:
                        # Get the channel and user for confirmation
                        if isinstance(message_or_interaction, discord.Message):
                            channel = message_or_interaction.channel
                            user_id = message_or_interaction.author.id
                        else:  # Interaction
                            channel = message_or_interaction.channel
                            user_id = message_or_interaction.user.id
                        
                        confirmation_result = await self._request_confirmation(
                            function_name, function_args, channel, user_id
                        )
                        
                        if not confirmation_result["confirmed"]:
                            function_responses.append({
                                "tool_call_id": tool_call["id"],
                                "role": "tool",
                                "content": f"Error: {confirmation_result['message']}"
                            })
                            continue
                    
                    # Execute the function
                    try:
                        result = await self._execute_function(function_name, function_args)
                        function_responses.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool", 
                            "content": result
                        })
                    except Exception as e:
                        logger.error(f"Error executing function {function_name}: {e}")
                        function_responses.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "content": f"Error: {str(e)}"
                        })
                
                # Send function results back to get final response
                if function_responses:
                    # Convert our function responses to the format expected by the API
                    api_messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": response.get("content") or "", "tool_calls": response.get("tool_calls", [])}
                    ]
                    
                    # Add function responses
                    for fr in function_responses:
                        api_messages.append({
                            "role": "tool",
                            "tool_call_id": fr["tool_call_id"],
                            "content": fr["content"]
                        })
                    
                    # Make the follow-up API call
                    final_response = await self.api_manager.call_api_with_fallback(
                        system_prompt=system_prompt,
                        user_prompt=json.dumps(api_messages[1:])  # Send everything except system prompt
                    )
                    
                    response_text = final_response.get("content", "")
                    # Avoid duplicate responses by being concise
                    if response_text and len(response_text.strip()) > 0:
                        return f"{response_text.strip()}\n\n_via {provider_used}_"
                    else:
                        return f"Task completed successfully.\n\n_via {provider_used}_"
                
                return f"Task completed successfully.\n\n_via {provider_used}_"
            
            # No function calls, return the text response
            content = response.get("content") or "I'm sorry, I couldn't process your request. Please try again."
            return f"{content}\n\n_via {provider_used}_"
            
        except Exception as e:
            logger.error(f"Error calling AI API: {e}")
            return f"An error occurred while processing your request: {str(e)}"
    
    async def _execute_function(self, function_name: str, function_args: Dict[str, Any]) -> str:
        """
        Execute a Discord management function.
        
        Args:
            function_name: Name of the function to execute
            function_args: Arguments for the function
            
        Returns:
            str: Result of the function execution
        """
        # Special handling for cross-server functions that need user_id
        if function_name == "execute_cross_server_clone":
            if hasattr(self, '_current_user_id'):
                function_args["user_id"] = self._current_user_id
        
        # Special handling for the API status function
        if function_name == "get_api_status":
            if hasattr(self, 'api_manager'):
                status = self.api_manager.get_provider_status()
                return f"API Status:\n" + json.dumps(status, indent=2)
            return "API status information not available"
        
        # Special handling for category deletion
        if function_name == "delete_category_and_channels":
            return await self.delete_category_and_channels(**function_args)
        
        # Get the function from discord_tools
        if hasattr(self.discord_tools, function_name):
            func = getattr(self.discord_tools, function_name)
            if callable(func):
                return await func(**function_args)
        
        raise ValueError(f"Unknown function: {function_name}")
    
    async def delete_category_and_channels(self, guild_id: int, category_identifier: str) -> str:
        """
        Delete a category and all its channels.
        
        Args:
            guild_id: The ID of the Discord server
            category_identifier: The name or ID of the category to delete
            
        Returns:
            str: Result of the deletion operation
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            # Find the category
            target_category = None
            for cat in guild.categories:
                if cat.name.lower() == category_identifier.lower() or str(cat.id) == category_identifier:
                    target_category = cat
                    break
            
            if not target_category:
                return f"Error: Could not find category '{category_identifier}'"
            
            results = []
            
            # Delete all channels in the category
            for channel in target_category.channels:
                try:
                    await channel.delete(reason=f"Deleted as part of category deletion")
                    results.append(f"✅ Deleted channel: #{channel.name}")
                except Exception as e:
                    results.append(f"❌ Failed to delete channel #{channel.name}: {str(e)}")
            
            # Finally delete the category itself
            try:
                await target_category.delete(reason=f"Category deletion by AI")
                results.append(f"✅ Deleted category: {target_category.name}")
            except Exception as e:
                results.append(f"❌ Failed to delete category {target_category.name}: {str(e)}")
            
            return "\n".join(results)
        
        except Exception as e:
            logger.error(f"Error in delete_category_and_channels: {e}")
            return f"Error deleting category: {str(e)}"
    
    async def _request_confirmation(self, function_name: str, function_args: Dict[str, Any], channel: discord.TextChannel, owner_id: int) -> Dict[str, Any]:
        """
        Request confirmation for dangerous operations.
        
        Args:
            function_name: Name of the dangerous function
            function_args: Arguments for the function
            channel: Channel to send confirmation message
            owner_id: ID of the owner who needs to confirm
            
        Returns:
            Dict with 'confirmed' and 'message' keys
        """
        # Create a readable description of the function call
        description = self._format_function_description(function_name, function_args)
        
        confirmation_message = (
            f"⚠️ **DANGEROUS OPERATION** ⚠️\n\n"
            f"About to: {description}\n\n"
            f"React with ✅ to confirm or ❌ to cancel, or reply with 'confirm' to this message. (90 seconds)"
        )
        
        # Send confirmation message
        confirmation_msg = await channel.send(confirmation_message)
        
        # Add reaction options
        await confirmation_msg.add_reaction("✅")
        await confirmation_msg.add_reaction("❌")
        
        # Set up the confirmation future
        confirmation_future = asyncio.Future()
        
        # Define the checks
        def reaction_check(reaction, user):
            return (user.id == owner_id and 
                   reaction.message.id == confirmation_msg.id and
                   str(reaction.emoji) in ["✅", "❌"])
        
        def message_check(message):
            # Check if message is a reply to our confirmation
            if not hasattr(message, 'reference') or not message.reference:
                return False
            
            # Check if it's from the right user and is a reply to our message
            return (message.author.id == owner_id and
                   message.reference.message_id == confirmation_msg.id and
                   message.content.lower() == 'confirm')
        
        # Set up the tasks
        reaction_task = asyncio.create_task(
            self.bot.wait_for('reaction_add', check=reaction_check, timeout=90.0)
        )
        message_task = asyncio.create_task(
            self.bot.wait_for('message', check=message_check, timeout=90.0)
        )
        
        try:
            # Wait for either confirmation method
            done, pending = await asyncio.wait(
                [reaction_task, message_task],
                return_when=asyncio.FIRST_COMPLETED,
                timeout=90.0
            )
            
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
            
            if not done:
                # Timeout occurred
                await confirmation_msg.edit(content=f"{confirmation_message}\n\n⏰ **Timed out after 90 seconds**")
                return {"confirmed": False, "message": "Operation timed out"}
            
            # Get the result from the completed task
            completed_task = list(done)[0]
            
            try:
                result = completed_task.result()
                
                if completed_task == reaction_task:
                    reaction, user = result
                    if str(reaction.emoji) == "✅":
                        await confirmation_msg.edit(content=f"{confirmation_message}\n\n✅ **Confirmed - Proceeding...**")
                        return {"confirmed": True, "message": "Operation confirmed"}
                    else:
                        await confirmation_msg.edit(content=f"{confirmation_message}\n\n❌ **Cancelled**")
                        return {"confirmed": False, "message": "Operation cancelled by user"}
                else:  # message_task
                    message = result
                    await confirmation_msg.edit(content=f"{confirmation_message}\n\n✅ **Confirmed via reply - Proceeding...**")
                    return {"confirmed": True, "message": "Operation confirmed"}
                
            except asyncio.CancelledError:
                return {"confirmed": False, "message": "Operation cancelled"}
        
        except asyncio.TimeoutError:
            await confirmation_msg.edit(content=f"{confirmation_message}\n\n⏰ **Timed out after 90 seconds**")
            return {"confirmed": False, "message": "Operation timed out"}
        except Exception as e:
            logger.error(f"Error in confirmation process: {e}")
            await confirmation_msg.edit(content=f"{confirmation_message}\n\n❌ **Error in confirmation process: {str(e)}**")
            return {"confirmed": False, "message": f"Confirmation error: {str(e)}"}
    
    def _format_function_description(self, function_name: str, function_args: Dict[str, Any]) -> str:
        """
        Format a readable description of the function call.
        
        Args:
            function_name: Name of the function
            function_args: Function arguments
            
        Returns:
            str: Human-readable description
        """
        if function_name == "delete_channel":
            channel_id = function_args.get("channel_identifier", "unknown")
            return f"Delete channel '{channel_id}'"
        elif function_name == "delete_category_and_channels":
            category_id = function_args.get("category_identifier", "unknown")
            return f"Delete category '{category_id}' and ALL its channels"
        elif function_name == "delete_role":
            role_id = function_args.get("role_identifier", "unknown")
            return f"Delete role '{role_id}'"
        elif function_name == "kick_member":
            member_id = function_args.get("member_identifier", "unknown")
            reason = function_args.get("reason", "No reason provided")
            return f"Kick member '{member_id}' (Reason: {reason})"
        elif function_name == "ban_member":
            member_id = function_args.get("member_identifier", "unknown")
            reason = function_args.get("reason", "No reason provided")
            return f"Ban member '{member_id}' (Reason: {reason})"
        elif function_name == "execute_cross_server_clone":
            target_id = function_args.get("target_guild_id", "unknown")
            return f"Clone data to server ID {target_id}"
        elif function_name == "purge_messages":
            channel = function_args.get("channel_identifier", "unknown")
            limit = function_args.get("limit", 0)
            return f"Bulk delete {limit} messages from channel '{channel}'"
        else:
            return f"Execute {function_name} with parameters: {function_args}"