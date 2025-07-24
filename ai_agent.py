import json
import logging
import asyncio
import discord
from typing import Dict, Any, List, Optional, Callable
from openai import OpenAI
from pydantic import BaseModel

from config import config
from discord_tools import DiscordTools, DANGEROUS_FUNCTIONS

logger = logging.getLogger(__name__)

class FunctionCall(BaseModel):
    """Model for function call responses from Gemini."""
    name: str
    args: Dict[str, Any]

class DiscordAgent:
    """AI agent that manages Discord server operations using Gemini AI."""
    
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.discord_tools = DiscordTools(bot)
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.openai_api_key
        )
        self.pending_confirmations: Dict[int, Dict[str, Any]] = {}
        
        # Build the function schema for OpenAI
        self.function_schemas = self._build_function_schemas()
    
    def _build_function_schemas(self) -> List[Dict[str, Any]]:
        """Build function schemas for Gemini AI based on available Discord tools."""
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
                            "description": "The name or ID of the channel to delete (supports Discord mentions like <#123456789>, direct IDs like '123456789', or channel names like 'general')"
                        }
                    },
                    "required": ["guild_id", "channel_identifier"]
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
                            "description": "The type of channel ('text' or 'voice')",
                            "enum": ["text", "voice"]
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
                "name": "list_members",
                "description": "List members in a Discord server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of members to list (default: 50)"
                        }
                    },
                    "required": ["guild_id"]
                }
            },
            {
                "name": "get_server_info",
                "description": "Get general information about a Discord server",
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
                            "description": "The name or ID of the role to delete (supports Discord mentions like <@&123456789>, direct IDs, or role names)"
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
                            "description": "The name or ID of the member to kick (supports Discord mentions like <@123456789>, direct IDs, usernames, or display names)"
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
                            "description": "The name or ID of the member to ban (supports Discord mentions like <@123456789>, direct IDs, usernames, or display names)"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Optional reason for the ban"
                        }
                    },
                    "required": ["guild_id", "member_identifier"]
                }
            }
        ]
        return schemas
    
    async def process_command(self, message: discord.Message, user_prompt: str) -> str:
        """
        Process a natural language command using Gemini AI.
        
        Args:
            message (discord.Message): The Discord message object
            user_prompt (str): The user's natural language instruction
            
        Returns:
            str: The final response to send back to the user
        """
        try:
            guild_id = message.guild.id if message.guild else None
            if not guild_id:
                return "Error: This command can only be used in a server, not in DMs."
            
            # Create the system prompt with context
            system_prompt = f"""You are a Discord server management AI assistant. You have access to various Discord server management functions.

Current context:
- Server ID: {guild_id}
- Server Name: {message.guild.name}
- User: {message.author.display_name}

You can use the following functions to help manage the Discord server:
{json.dumps(self.function_schemas, indent=2)}

When a user asks you to perform an action, analyze their request and use the appropriate function(s). 
Be helpful and provide clear feedback about what actions you're taking.

IMPORTANT: Some functions are marked as DANGEROUS and require confirmation. If you need to use a dangerous function, explain what you're about to do clearly."""
            
            # Start conversation with OpenAI
            response = await self._call_openai_with_tools(system_prompt, user_prompt, message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return f"An error occurred while processing your request: {str(e)}"
    
    async def _call_openai_with_tools(self, system_prompt: str, user_prompt: str, message: discord.Message) -> str:
        """
        Call OpenAI API (via OpenRouter) with function calling capabilities.
        
        Args:
            system_prompt (str): The system instruction
            user_prompt (str): The user's prompt
            
        Returns:
            str: The final response from the AI
        """
        try:
            # Convert function schemas to OpenAI tools format
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
            
            # Make the initial request to DeepSeek via OpenRouter
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=tools,
                tool_choice="auto"
            )
            
            message_content = response.choices[0].message
            
            # Check if AI wants to call functions
            if hasattr(message_content, 'tool_calls') and message_content.tool_calls:
                function_responses = []
                
                for tool_call in message_content.tool_calls:
                    function_name = tool_call.function.name
                    function_args = {}
                    
                    # Parse function arguments
                    if tool_call.function.arguments:
                        try:
                            import json
                            function_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing function arguments: {e}")
                            continue
                    
                    # Check if this is a dangerous function
                    if function_name in DANGEROUS_FUNCTIONS:
                        confirmation_result = await self._request_confirmation(
                            function_name, function_args, message.channel, message.author.id
                        )
                        
                        if not confirmation_result["confirmed"]:
                            function_responses.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "content": f"Error: {confirmation_result['message']}"
                            })
                            continue
                    
                    # Execute the function
                    try:
                        result = await self._execute_function(function_name, function_args)
                        function_responses.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool", 
                            "content": result
                        })
                    except Exception as e:
                        logger.error(f"Error executing function {function_name}: {e}")
                        function_responses.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "content": f"Error: {str(e)}"
                        })
                
                # Send function results back to get final response
                if function_responses:
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                        message_content,
                        *function_responses
                    ]
                    
                    final_response = self.client.chat.completions.create(
                        model="deepseek/deepseek-chat-v3-0324:free",
                        messages=messages
                    )
                    
                    return final_response.choices[0].message.content or "Task completed successfully."
                
                return "Task completed successfully."
            
            # No function calls, return the text response
            return message_content.content or "I'm sorry, I couldn't process your request. Please try again."
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return f"An error occurred while processing your request: {str(e)}"
    
    async def _execute_function(self, function_name: str, function_args: Dict[str, Any]) -> str:
        """
        Execute a Discord management function.
        
        Args:
            function_name (str): Name of the function to execute
            function_args (Dict[str, Any]): Arguments for the function
            
        Returns:
            str: Result of the function execution
        """
        # Get the function from discord_tools
        if hasattr(self.discord_tools, function_name):
            func = getattr(self.discord_tools, function_name)
            if callable(func):
                return await func(**function_args)
        
        raise ValueError(f"Unknown function: {function_name}")
    
    async def _request_confirmation(self, function_name: str, function_args: Dict[str, Any], channel: discord.TextChannel, owner_id: int) -> Dict[str, Any]:
        """
        Request confirmation for dangerous operations.
        
        Args:
            function_name (str): Name of the dangerous function
            function_args (Dict[str, Any]): Arguments for the function
            channel (discord.TextChannel): Channel to send confirmation message
            owner_id (int): ID of the owner who needs to confirm
            
        Returns:
            Dict[str, Any]: Confirmation result with 'confirmed' and 'message' keys
        """
        confirmation_message = (
            f"**⚠️ CONFIRMATION REQUIRED ⚠️**\n\n"
            f"I am about to execute `{function_name}` with arguments:\n"
            f"```json\n{json.dumps(function_args, indent=2)}\n```\n\n"
            f"This action may be irreversible. Do you want to proceed?\n"
            f"Reply with **yes** to confirm, or anything else to cancel.\n"
            f"You have 60 seconds to respond."
        )
        
        # Send confirmation message
        await channel.send(confirmation_message)
        
        # Store pending confirmation
        self.pending_confirmations[owner_id] = {
            "function_name": function_name,
            "function_args": function_args,
            "channel": channel,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Wait for response with timeout
        try:
            def check(message):
                return (message.author.id == owner_id and 
                       message.channel == channel and
                       owner_id in self.pending_confirmations)
            
            response_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            # Process the response
            response = response_message.content.lower().strip()
            
            # Clean up pending confirmation
            if owner_id in self.pending_confirmations:
                del self.pending_confirmations[owner_id]
            
            if response == "yes":
                return {
                    "confirmed": True,
                    "message": "Confirmation granted by user"
                }
            else:
                return {
                    "confirmed": False,
                    "message": "Operation cancelled by user"
                }
                
        except asyncio.TimeoutError:
            # Clean up pending confirmation
            if owner_id in self.pending_confirmations:
                del self.pending_confirmations[owner_id]
            
            await channel.send("⏰ Confirmation timeout. Operation cancelled for safety.")
            return {
                "confirmed": False,
                "message": "Operation cancelled due to timeout"
            }