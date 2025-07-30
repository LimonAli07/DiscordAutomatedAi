import json
import logging
import asyncio
import discord
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from pydantic import BaseModel

from config import config
from enhanced_discord_tools import DiscordTools, DANGEROUS_FUNCTIONS
from api_manager import APIManager

# Add additional dangerous functions from other modules
ADDITIONAL_DANGEROUS_FUNCTIONS = [
    'update_role_permissions',
    'restore_server',
    'setup_word_filter',
    'setup_anti_spam'
]

# Combine all dangerous functions
ALL_DANGEROUS_FUNCTIONS = DANGEROUS_FUNCTIONS + ADDITIONAL_DANGEROUS_FUNCTIONS

logger = logging.getLogger(__name__)

class FunctionCall(BaseModel):
    """Model for function call responses."""
    name: str
    args: Dict[str, Any]

class DiscordAgent:
    """AI agent that manages Discord server operations using multiple AI providers."""
    
    def _get_clean_model_name(self, provider: str, model: str = None) -> str:
        """Convert internal provider names to clean, user-friendly model names."""
        provider_model_map = {
            "gpt4all": "GPT-4 Mini",
            "openrouter": "Claude 3.5 Sonnet",
            "google_ai": "Gemini Pro",
            "cerebras": "Llama 3.3 70B",
            "samurai_api": "GPT-4 Mini",
            "simple_fallback": "AI Assistant"
        }
        
        # Return clean model name, fallback to generic if unknown
        return provider_model_map.get(provider, "AI Assistant")
    
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
            # Channel Management
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
            
            # Role Management
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
                            "description": "List of permission names to grant to the role",
                            "items": {
                                "type": "string"
                            }
                        },
                        "hoist": {
                            "type": "boolean",
                            "description": "Whether the role should be displayed separately in the member list"
                        },
                        "mentionable": {
                            "type": "boolean",
                            "description": "Whether the role should be mentionable"
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
                "name": "assign_role",
                "description": "Assign a role to a member",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "member_identifier": {
                            "type": "string",
                            "description": "The name, nickname, or ID of the member"
                        },
                        "role_identifier": {
                            "type": "string",
                            "description": "The name or ID of the role to assign"
                        }
                    },
                    "required": ["guild_id", "member_identifier", "role_identifier"]
                }
            },
            {
                "name": "remove_role",
                "description": "Remove a role from a member",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "member_identifier": {
                            "type": "string",
                            "description": "The name, nickname, or ID of the member"
                        },
                        "role_identifier": {
                            "type": "string",
                            "description": "The name or ID of the role to remove"
                        }
                    },
                    "required": ["guild_id", "member_identifier", "role_identifier"]
                }
            },
            {
                "name": "update_role_permissions",
                "description": "Update the permissions of a role (DANGEROUS - requires confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "role_identifier": {
                            "type": "string",
                            "description": "The name or ID of the role to update"
                        },
                        "permissions": {
                            "type": "array",
                            "description": "List of permission names to grant to the role",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["guild_id", "role_identifier", "permissions"]
                }
            },
            
            # Moderation
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
                            "description": "The name, nickname, or ID of the member to kick"
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
                            "description": "The name, nickname, or ID of the member to ban"
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
            
            # Server Management
            {
                "name": "setup_auto_role",
                "description": "Set up an auto-role that will be assigned to new members when they join",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "role_identifier": {
                            "type": "string",
                            "description": "The name or ID of the role to automatically assign"
                        }
                    },
                    "required": ["guild_id", "role_identifier"]
                }
            },
            {
                "name": "setup_welcome_message",
                "description": "Set up a welcome message to be sent when new members join",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "channel_identifier": {
                            "type": "string",
                            "description": "The name or ID of the channel to send welcome messages"
                        },
                        "welcome_message": {
                            "type": "string",
                            "description": "The message template to send (use {user}, {server}, {count} as placeholders)"
                        }
                    },
                    "required": ["guild_id", "channel_identifier", "welcome_message"]
                }
            },
            {
                "name": "backup_server",
                "description": "Create a backup of server settings including channels, roles, and permissions",
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
                "name": "restore_server",
                "description": "Restore a server from a backup (DANGEROUS - requires confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server to restore to"
                        },
                        "backup_id": {
                            "type": "integer",
                            "description": "Optional ID of the server backup to use (defaults to same server)"
                        }
                    },
                    "required": ["guild_id"]
                }
            },
            {
                "name": "get_server_stats",
                "description": "Get statistics about a Discord server",
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
            
            # Moderation Tools
            {
                "name": "setup_word_filter",
                "description": "Set up a word filter to automatically delete messages containing banned words (DANGEROUS - requires confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "banned_words": {
                            "type": "array",
                            "description": "List of words to filter out",
                            "items": {
                                "type": "string"
                            }
                        },
                        "action": {
                            "type": "string",
                            "description": "Action to take when banned words are found ('delete', 'warn', 'mute')",
                            "enum": ["delete", "warn", "mute"]
                        }
                    },
                    "required": ["guild_id", "banned_words"]
                }
            },
            {
                "name": "setup_anti_spam",
                "description": "Set up anti-spam protection (DANGEROUS - requires confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "max_messages_per_minute": {
                            "type": "integer",
                            "description": "Maximum messages allowed per minute per user"
                        },
                        "action": {
                            "type": "string",
                            "description": "Action to take when spam is detected ('warn', 'mute', 'kick')",
                            "enum": ["warn", "mute", "kick"]
                        }
                    },
                    "required": ["guild_id", "max_messages_per_minute"]
                }
            },
            {
                "name": "track_member_activity",
                "description": "Track member activity and provide statistics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "tracking_period": {
                            "type": "integer",
                            "description": "Number of days to track activity for"
                        }
                    },
                    "required": ["guild_id"]
                }
            },
            
            # Utility Tools
            {
                "name": "set_reminder",
                "description": "Set a reminder for a specific time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "channel_identifier": {
                            "type": "string",
                            "description": "The name or ID of the channel to send the reminder to"
                        },
                        "reminder_text": {
                            "type": "string",
                            "description": "The reminder message"
                        },
                        "reminder_time": {
                            "type": "string",
                            "description": "When to send the reminder (e.g., 'in 1 hour', 'tomorrow at 3pm')"
                        }
                    },
                    "required": ["guild_id", "channel_identifier", "reminder_text", "reminder_time"]
                }
            },
            {
                "name": "schedule_event",
                "description": "Schedule an event in the server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "event_name": {
                            "type": "string",
                            "description": "Name of the event"
                        },
                        "event_description": {
                            "type": "string",
                            "description": "Description of the event"
                        },
                        "event_time": {
                            "type": "string",
                            "description": "When the event will take place"
                        },
                        "channel_identifier": {
                            "type": "string",
                            "description": "The name or ID of the channel to announce the event in"
                        }
                    },
                    "required": ["guild_id", "event_name", "event_description", "event_time"]
                }
            },
            
            # Fun Features
            {
                "name": "create_poll",
                "description": "Create a poll in a channel",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "integer",
                            "description": "The ID of the Discord server"
                        },
                        "channel_identifier": {
                            "type": "string",
                            "description": "The name or ID of the channel to create the poll in"
                        },
                        "poll_question": {
                            "type": "string",
                            "description": "The poll question"
                        },
                        "poll_options": {
                            "type": "array",
                            "description": "List of poll options",
                            "items": {
                                "type": "string"
                            }
                        },
                        "duration_hours": {
                            "type": "integer",
                            "description": "How long the poll should run (in hours)"
                        }
                    },
                    "required": ["guild_id", "channel_identifier", "poll_question", "poll_options"]
                }
            },
            
            # API Status
            {
                "name": "get_api_status",
                "description": "Get the status of all API providers",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        return schemas
    
    async def process_command(self, message_or_interaction: Union[discord.Message, discord.Interaction], user_prompt: str, debug: bool = False) -> str:
        """
        Process a user command through the AI agent.
        
        Args:
            message_or_interaction: Discord Message or Interaction object
            user_prompt: The user's natural language command
            debug: Whether to output step-by-step debug info
            
        Returns:
            str: The response to send back to the user
        """
        debug_log = []
        
        # Get user and guild info
        if isinstance(message_or_interaction, discord.Message):
            author = message_or_interaction.author
            guild = message_or_interaction.guild
            guild_id = guild.id if guild else None
        else:  # Interaction
            author = message_or_interaction.user
            guild = message_or_interaction.guild
            guild_id = guild.id if guild else None
        
        if debug:
            debug_log.append(f"[DEBUG] User: {author} (ID: {author.id})")
            debug_log.append(f"[DEBUG] Guild: {guild} (ID: {guild_id})")
            debug_log.append(f"[DEBUG] Prompt: {user_prompt}")
        
        # --- ENHANCED HELP/USAGE LOGIC ---
        help_keywords = ["how do i", "how to", "how can i", "usage", "example", "help", "guide", "tutorial", "what commands", "commands can i"]
        lowered_prompt = user_prompt.lower()
        
        # Check for general help requests
        if any(kw in lowered_prompt for kw in help_keywords):
            # First check for common help patterns (prioritize comprehensive help)
            if any(phrase in lowered_prompt for phrase in ["make 2 channels", "create 2 channels", "multiple channels", "several channels", "make multiple", "create multiple"]):
                help_text = """**🔧 How to Create Multiple Channels**

**Single Channel:**
• `/askai create channel general`
• `/askai make a channel called announcements`

**Multiple Channels (Method 1 - Separate Commands):**
• `/askai create channel general`
• `/askai create channel announcements`

**Multiple Channels (Method 2 - One Command):**
• `/askai create channels general and announcements`
• `/askai make multiple channels called general, announcements, chat`

**Voice Channels:**
• `/askai create voice channel Gaming`
• `/askai make voice channels Music and Study`

**Categories:**
• `/askai create category General Channels`
• `/askai make a category called Voice Rooms`"""
                return ("\n".join(debug_log) + "\n\n" if debug else "") + help_text
            
            elif any(phrase in lowered_prompt for phrase in ["create role", "make role", "add role", "create a role", "make a role"]):
                help_text = """**👑 How to Create Roles**

**Basic Role:**
• `/askai create role Member`
• `/askai make a role called Moderator`

**Role with Color:**
• `/askai create role VIP with color red`
• `/askai make role Admin with color #FF0000`

**Multiple Roles:**
• `/askai create roles Member and VIP`
• `/askai make roles Moderator, Admin, Helper`

**Role Management:**
• `/askai list roles` - See all server roles
• `/askai delete role OldRole` - Remove a role"""
                return ("\n".join(debug_log) + "\n\n" if debug else "") + help_text
            
            elif any(phrase in lowered_prompt for phrase in ["list", "show", "see", "view"]):
                help_text = """**📋 How to View Server Information**

**Channels:**
• `/askai list channels` - Show all channels
• `/askai show channels` - Same as above

**Roles:**
• `/askai list roles` - Show all roles
• `/askai show roles` - Same as above

**Server Stats:**
• `/askai get server stats` - Member count, channels, etc.
• `/askai show server info` - Server overview

**Members:**
• `/askai list members` - Show server members
• `/askai get member count` - Just the count"""
                return ("\n".join(debug_log) + "\n\n" if debug else "") + help_text
            
            elif any(phrase in lowered_prompt for phrase in ["delete", "remove", "kick", "ban"]):
                help_text = """**⚠️ How to Use Moderation Commands**

**Delete Channels:**
• `/askai delete channel old-chat` ⚠️ *Requires confirmation*
• `/askai remove channel #unused` ⚠️ *Requires confirmation*

**Delete Roles:**
• `/askai delete role OldRole` ⚠️ *Requires confirmation*

**Member Moderation:**
• `/askai kick member @username` ⚠️ *Requires confirmation*
• `/askai ban member @username` ⚠️ *Requires confirmation*

**⚠️ Important Notes:**
- Dangerous operations require confirmation with ✅/❌ reactions
- You have 60 seconds to confirm
- These actions cannot be undone!"""
                return ("\n".join(debug_log) + "\n\n" if debug else "") + help_text
            
            # General help if no specific pattern matched
            else:
                help_text = """**🤖 Discord AI Bot - Quick Start Guide**

**📝 Channel Management:**
• `/askai create channel [name]` - Create a text channel
• `/askai create voice channel [name]` - Create a voice channel
• `/askai create channels [name1] and [name2]` - Create multiple channels
• `/askai list channels` - Show all channels

**👑 Role Management:**
• `/askai create role [name]` - Create a new role
• `/askai create role [name] with color [color]` - Role with color
• `/askai list roles` - Show all roles

**📊 Server Information:**
• `/askai get server stats` - Server statistics
• `/askai list members` - Show members

**⚠️ Moderation (Requires Confirmation):**
• `/askai delete channel [name]` - Delete a channel
• `/askai kick member @user` - Kick a member
• `/askai ban member @user` - Ban a member

**💡 Tips:**
- Use natural language: "make a channel called general"
- Multiple items: "create channels general, announcements, chat"
- Colors: "red", "#FF0000", or "0xFF0000"
- The bot executes commands immediately (except dangerous ones)

**🔧 Need specific help?** Ask: "how to create channels" or "help with roles" """
                return ("\n".join(debug_log) + "\n\n" if debug else "") + help_text
        # --- END ENHANCED HELP/USAGE LOGIC ---
        
        # Build the system prompt
        system_prompt = f"""You are a Discord server management AI assistant with access to Discord management functions.

🚨 CRITICAL EXECUTION RULES 🚨:
1. YOU MUST CALL THE APPROPRIATE FUNCTION FOR EVERY USER REQUEST
2. DO NOT ask for confirmation unless the function is explicitly marked as DANGEROUS
3. DO NOT explain what you would do - DO IT by calling the function immediately
4. For commands like "create role", "list channels", etc. - call the function RIGHT NOW
5. Your job is to EXECUTE Discord operations, not to chat about them

🛡️ SAFETY-FIRST EXECUTION ORDER 🛡️:
- ALWAYS do SAFE operations (create, list, get) BEFORE dangerous operations (delete, ban, kick)
- For "clone and delete": FIRST create the clone, THEN delete the original
- For "replace X with Y": FIRST create Y, THEN delete X
- NEVER delete something before creating its replacement

MANDATORY FUNCTION CALLING:
- User says "create channel X" -> YOU MUST call create_channel function
- User says "list channels" -> YOU MUST call list_channels function
- User says "create role X" -> YOU MUST call create_role function
- User says "get stats" -> YOU MUST call get_server_stats function

MULTIPLE OPERATIONS:
- User asks for "multiple channels" -> Call create_channel function MULTIPLE TIMES
- User says "create channels X, Y, Z" -> Call create_channel for EACH channel (X, then Y, then Z)
- User asks for "several roles" -> Call create_role function MULTIPLE TIMES
- ALWAYS create ALL requested items, not just the first one

CLONE OPERATIONS:
- User says "clone channel X" -> FIRST call create_channel with X-clone name, THEN optionally delete original if requested
- User says "clone and delete X" -> FIRST create_channel for clone, THEN delete_channel for original
- ALWAYS preserve data by creating before deleting

EXECUTION EXAMPLES:
❌ WRONG: "I'll create a role named 'TestRole' with the color red for you."
✅ CORRECT: [Calls create_role function with parameters]

❌ WRONG: "I can help you list the channels in this server."
✅ CORRECT: [Calls list_channels function immediately]

❌ WRONG: "I'll create channels hi and hello" (without calling functions)
✅ CORRECT: [Calls create_channel for "hi", then calls create_channel for "hello"]

❌ WRONG: [Calls delete_channel first, then create_channel] (DANGEROUS - data loss!)
✅ CORRECT: [Calls create_channel first, then delete_channel] (SAFE - preserves data)

Current server: {guild.name if guild else 'Unknown'} (ID: {guild_id})
Current user: {author.name} (ID: {author.id})

Available functions:
{chr(10).join(f"- {schema['name']}: {schema['description']}" for schema in self.function_schemas)}

FUNCTION CALL REQUIREMENTS:
- Always use guild_id {guild_id} for server operations
- Call functions immediately when user requests Discord operations
- For multiple items, call the function multiple times (once per item)
- SAFE operations (create, list) BEFORE dangerous operations (delete, ban)
- Only dangerous functions (marked as DANGEROUS) require confirmation
- Normal operations like creating channels/roles should execute instantly

EXECUTE FUNCTIONS NOW. DO NOT EXPLAIN. DO NOT ASK. JUST CALL THE FUNCTIONS."""

        # Process the command with AI
        response = await self._call_ai_with_tools(system_prompt, user_prompt, message_or_interaction, debug=debug, debug_log=debug_log)
        return response
    
    async def _call_ai_with_tools(self, system_prompt: str, user_prompt: str, message_or_interaction: Union[discord.Message, discord.Interaction], debug: bool = False, debug_log: list = None) -> str:
        """
        Call AI API with function calling capabilities.
        
        Args:
            system_prompt: The system instruction
            user_prompt: The user's prompt
            message_or_interaction: Discord Message or Interaction object
            debug: Whether to output step-by-step debug info
            debug_log: List to append debug messages to
            
        Returns:
            str: The final response from the AI
        """
        try:
            # Extract guild_id from message_or_interaction for function detection
            if isinstance(message_or_interaction, discord.Message):
                guild = message_or_interaction.guild
                guild_id = guild.id if guild else None
            else:  # Interaction
                guild = message_or_interaction.guild
                guild_id = guild.id if guild else None
            
            if debug and debug_log is not None:
                debug_log.append(f"[DEBUG] Calling AI API with tools.")
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
            try:
                response = await self.api_manager.call_api_with_fallback(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    tools=tools
                )
            except Exception as e:
                logger.error(f"All API providers failed: {e}")
                if debug and debug_log is not None:
                    debug_log.append(f"[DEBUG][ERROR] All API providers failed: {str(e)}")
                
                # Provide a helpful fallback response
                fallback_response = (
                    "⚠️ **API Service Temporarily Unavailable**\n\n"
                    "All AI providers are currently experiencing issues:\n"
                    "• **OpenRouter**: Rate limit exceeded (free tier limit reached)\n"
                    "• **Google AI**: Service temporarily unavailable\n"
                    "• **Cerebras**: Service configuration issue\n\n"
                    "**Solutions:**\n"
                    "1. **Wait a few minutes** and try again\n"
                    "2. **Add credits** to your OpenRouter account\n"
                    "3. **Check your API keys** in the environment variables\n\n"
                    "The bot is still running and will work once the APIs are available again."
                )
                return ("\n".join(debug_log) + "\n\n" if debug else "") + fallback_response
            
            # Track which provider was used and get clean model name
            provider_used = response.get("provider", "unknown")
            clean_model_name = self._get_clean_model_name(provider_used)
            if debug and debug_log is not None:
                debug_log.append(f"[DEBUG] AI provider used: {provider_used}")
                debug_log.append(f"[DEBUG] AI response: {response}")
            
            # Check if AI wants to call functions
            if response.get("tool_calls"):
                function_responses = []
                
                for tool_call in response["tool_calls"]:
                    function_name = tool_call["name"]
                    function_args = tool_call["args"]
                    if debug and debug_log is not None:
                        debug_log.append(f"[DEBUG] Tool call: {function_name} with args {function_args}")
                    
                    # Check if this is a dangerous function
                    if function_name in ALL_DANGEROUS_FUNCTIONS:
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
                            if debug and debug_log is not None:
                                debug_log.append(f"[DEBUG] Dangerous function not confirmed: {function_name}")
                            continue
                    
                    # Execute the function
                    try:
                        result = await self._execute_function(function_name, function_args, debug=debug, debug_log=debug_log)
                        function_responses.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool", 
                            "content": result
                        })
                        if debug and debug_log is not None:
                            debug_log.append(f"[DEBUG] Function {function_name} executed successfully.")
                    except Exception as e:
                        logger.error(f"Error executing function {function_name}: {e}")
                        function_responses.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "content": f"Error: {str(e)}"
                        })
                        if debug and debug_log is not None:
                            debug_log.append(f"[DEBUG][ERROR] Function {function_name} failed: {str(e)}")
                
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
                    try:
                        final_response = await self.api_manager.call_api_with_fallback(
                            system_prompt=system_prompt,
                            user_prompt=json.dumps(api_messages[1:])  # Send everything except system prompt
                        )
                    except Exception as e:
                        logger.error(f"Follow-up API call failed: {e}")
                        if debug and debug_log is not None:
                            debug_log.append(f"[DEBUG][ERROR] Follow-up API call failed: {str(e)}")
                        # Return the function results even if the final AI response fails
                        return ("\n".join(debug_log) + "\n\n" if debug else "") + "Task completed successfully, but AI response unavailable."
                    
                    response_text = final_response.get("content", "")
                    if debug and debug_log is not None:
                        debug_log.append(f"[DEBUG] Final AI response: {response_text}")
                    # Avoid duplicate responses by being concise
                    if response_text and len(response_text.strip()) > 0:
                        return ("\n".join(debug_log) + "\n\n" if debug else "") + f"{response_text.strip()}\n\n_— {clean_model_name}_"
                    else:
                        return ("\n".join(debug_log) + "\n\n" if debug else "") + f"Task completed successfully.\n\n_— {clean_model_name}_"
                
                return ("\n".join(debug_log) + "\n\n" if debug else "") + f"Task completed successfully.\n\n_— {clean_model_name}_"
            
            # No function calls, but check if we can detect a function from the text response
            content = response.get("content") or "I'm sorry, I couldn't process your request. Please try again."
            
            # Try to detect function calls from text response when function calling fails
            detected_function = self._detect_function_from_text(content, user_prompt, guild_id)
            if detected_function:
                try:
                    if debug and debug_log is not None:
                        debug_log.append(f"[DEBUG] Detected function from text: {detected_function['name']} with args {detected_function['args']}")
                    
                    # Handle special multiple channel creation
                    if detected_function["name"] == "create_multiple_channels":
                        results = []
                        channel_names = detected_function["args"]["channel_names"]
                        guild_id = detected_function["args"]["guild_id"]
                        channel_type = detected_function["args"]["channel_type"]
                        
                        for channel_name in channel_names:
                            try:
                                result = await self._execute_function(
                                    "create_channel",
                                    {
                                        "guild_id": guild_id,
                                        "channel_name": channel_name,
                                        "channel_type": channel_type
                                    },
                                    debug=debug,
                                    debug_log=debug_log
                                )
                                results.append(f"✅ {result}")
                            except Exception as e:
                                results.append(f"❌ Failed to create channel '{channel_name}': {str(e)}")
                        
                        combined_result = "\n".join(results)
                        return ("\n".join(debug_log) + "\n\n" if debug else "") + f"{combined_result}\n\n_— {clean_model_name}_"
                    else:
                        result = await self._execute_function(
                            detected_function["name"],
                            detected_function["args"],
                            debug=debug,
                            debug_log=debug_log
                        )
                        return ("\n".join(debug_log) + "\n\n" if debug else "") + f"{result}\n\n_— {clean_model_name}_"
                except Exception as e:
                    logger.error(f"Error executing detected function: {e}")
                    if debug and debug_log is not None:
                        debug_log.append(f"[DEBUG][ERROR] Detected function execution failed: {str(e)}")
            
            # If no function was detected but the AI response suggests it should have done something,
            # try a more aggressive detection based on user prompt
            if not detected_function:
                fallback_function = self._detect_function_from_user_prompt(user_prompt, guild_id)
                if fallback_function:
                    try:
                        if debug and debug_log is not None:
                            debug_log.append(f"[DEBUG] Fallback function detected from user prompt: {fallback_function['name']} with args {fallback_function['args']}")
                        
                        result = await self._execute_function(
                            fallback_function["name"],
                            fallback_function["args"],
                            debug=debug,
                            debug_log=debug_log
                        )
                        return ("\n".join(debug_log) + "\n\n" if debug else "") + f"{result}\n\n_— {clean_model_name}_"
                    except Exception as e:
                        logger.error(f"Error executing fallback function: {e}")
                        if debug and debug_log is not None:
                            debug_log.append(f"[DEBUG][ERROR] Fallback function execution failed: {str(e)}")
            
            return ("\n".join(debug_log) + "\n\n" if debug else "") + f"{content}\n\n_— {clean_model_name}_"
            
        except Exception as e:
            logger.error(f"Error calling AI API: {e}")
            if debug and debug_log is not None:
                debug_log.append(f"[DEBUG][ERROR] {str(e)}")
                return "\n".join(debug_log) + f"\nAn error occurred while processing your request: {str(e)}"
            return f"An error occurred while processing your request: {str(e)}"
    
    async def _execute_function(self, function_name: str, function_args: Dict[str, Any], debug: bool = False, debug_log: list = None) -> str:
        """
        Execute a Discord management function.
        
        Args:
            function_name: Name of the function to execute
            function_args: Arguments for the function
            debug: Whether to output step-by-step debug info
            debug_log: List to append debug messages to
            
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
            if debug and debug_log is not None:
                debug_log.append(f"[DEBUG] Calling delete_category_and_channels with args: {function_args}")
            return await self.delete_category_and_channels(**function_args)
        
        # Get the function from discord_tools (basic Discord operations)
        if hasattr(self.discord_tools, function_name):
            func = getattr(self.discord_tools, function_name)
            if callable(func):
                if debug and debug_log is not None:
                    debug_log.append(f"[DEBUG] Calling {function_name} with args: {function_args}")
                return await func(**function_args)
        
        # Handle role management functions
        if function_name in ["assign_role", "remove_role", "update_role_permissions"]:
            from role_management import RoleManagement
            role_manager = RoleManagement(self.bot)
            if hasattr(role_manager, function_name):
                func = getattr(role_manager, function_name)
                if callable(func):
                    if debug and debug_log is not None:
                        debug_log.append(f"[DEBUG] Calling role management function {function_name} with args: {function_args}")
                    return await func(**function_args)
        
        # Handle server management functions
        if function_name in ["setup_auto_role", "setup_welcome_message", "backup_server", "restore_server", "get_server_stats"]:
            from server_management import ServerManagement
            server_manager = ServerManagement(self.bot)
            if hasattr(server_manager, function_name):
                func = getattr(server_manager, function_name)
                if callable(func):
                    if debug and debug_log is not None:
                        debug_log.append(f"[DEBUG] Calling server management function {function_name} with args: {function_args}")
                    return await func(**function_args)
        
        # Handle moderation functions
        if function_name in ["setup_word_filter", "setup_anti_spam", "track_member_activity"]:
            from moderation import ModerationTools
            moderation = ModerationTools(self.bot)
            if hasattr(moderation, function_name):
                func = getattr(moderation, function_name)
                if callable(func):
                    if debug and debug_log is not None:
                        debug_log.append(f"[DEBUG] Calling moderation function {function_name} with args: {function_args}")
                    return await func(**function_args)
        
        # Handle utility functions
        if function_name in ["set_reminder", "schedule_event"]:
            from utility import UtilityTools
            utility = UtilityTools(self.bot)
            if hasattr(utility, function_name):
                func = getattr(utility, function_name)
                if callable(func):
                    if debug and debug_log is not None:
                        debug_log.append(f"[DEBUG] Calling utility function {function_name} with args: {function_args}")
                    return await func(**function_args)
        
        # Handle fun features
        if function_name in ["create_poll"]:
            from fun_features import FunFeatures
            fun_features = FunFeatures(self.bot)
            if hasattr(fun_features, function_name):
                func = getattr(fun_features, function_name)
                if callable(func):
                    if debug and debug_log is not None:
                        debug_log.append(f"[DEBUG] Calling fun feature function {function_name} with args: {function_args}")
                    return await func(**function_args)
        
        # If we get here, the function wasn't found
        available_functions = [schema["name"] for schema in self.function_schemas]
        return f"Error: Function '{function_name}' not found. Available functions: {', '.join(available_functions)}"
    
    async def delete_category_and_channels(self, guild_id: int, category_identifier: str) -> str:
        """
        Delete an entire category and all its channels.
        
        Args:
            guild_id: The Discord server ID
            category_identifier: The name or ID of the category to delete
            
        Returns:
            str: Result message
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return f"Error: Could not find guild with ID {guild_id}"
            
            # Find the category
            category = None
            try:
                category_id = int(category_identifier)
                category = guild.get_channel(category_id)
            except ValueError:
                # Try to find by name
                for cat in guild.categories:
                    if cat.name.lower() == category_identifier.lower():
                        category = cat
                        break
            
            if not category:
                return f"Error: Could not find category '{category_identifier}' in the server"
            
            # Check if we have permission to delete the category
            if not guild.me.guild_permissions.manage_channels:
                return "Error: I don't have permission to manage channels in this server"
            
            # Get all channels in the category
            channels_to_delete = list(category.channels)
            category_name = category.name
            
            # Delete all channels in the category
            deleted_channels = []
            for channel in channels_to_delete:
                try:
                    await channel.delete()
                    deleted_channels.append(channel.name)
                except Exception as e:
                    logger.error(f"Error deleting channel {channel.name}: {e}")
            
            # Delete the category itself
            try:
                await category.delete()
            except Exception as e:
                logger.error(f"Error deleting category {category_name}: {e}")
                return f"Deleted {len(deleted_channels)} channels from category '{category_name}', but failed to delete the category itself: {str(e)}"
            
            return f"Successfully deleted category '{category_name}' and {len(deleted_channels)} channels: {', '.join(deleted_channels)}"
            
        except Exception as e:
            logger.error(f"Error in delete_category_and_channels: {e}")
            return f"Error deleting category: {str(e)}"
    
    async def _request_confirmation(self, function_name: str, function_args: Dict[str, Any], channel: discord.TextChannel, owner_id: int) -> Dict[str, Any]:
        """
        Request confirmation for dangerous operations with reaction buttons.
        
        Args:
            function_name: Name of the function being called
            function_args: Arguments for the function
            channel: Channel to send confirmation message in
            owner_id: ID of the user who initiated the command
            
        Returns:
            Dict with 'confirmed' boolean and 'message' string
        """
        # Check if user has permission to perform dangerous operations
        guild = channel.guild
        user = guild.get_member(owner_id)
        
        # Allow bot owner or users with administrator permissions
        has_permission = (
            owner_id == config.discord_owner_id or
            (user and user.guild_permissions.administrator)
        )
        
        if not has_permission:
            return {
                "confirmed": False,
                "message": "❌ Only the bot owner or administrators can perform dangerous operations."
            }
        
        # Format the function description
        function_desc = self._format_function_description(function_name, function_args)
        
        # Create confirmation message with enhanced formatting
        embed = discord.Embed(
            title="⚠️ DANGEROUS OPERATION - CONFIRMATION REQUIRED",
            description=f"**{user.display_name if user else 'User'}**, you're about to perform a dangerous operation:",
            color=0xFF4444
        )
        embed.add_field(
            name="🎯 Operation",
            value=f"```{function_desc}```",
            inline=False
        )
        embed.add_field(
            name="⚠️ WARNING",
            value="**This action CANNOT be undone!**\nMake sure you really want to proceed.",
            inline=False
        )
        embed.add_field(
            name="🔘 How to Confirm",
            value="**✅ Click the ✅ reaction to PROCEED**\n**❌ Click the ❌ reaction to CANCEL**",
            inline=False
        )
        embed.add_field(
            name="⏰ Timeout",
            value="You have **60 seconds** to respond",
            inline=False
        )
        embed.set_footer(text=f"Requested by {user.display_name if user else 'Unknown User'}")
        
        # Send confirmation message
        confirmation_msg = await channel.send(f"<@{owner_id}>", embed=embed)
        
        # Try to add reaction options
        try:
            await confirmation_msg.add_reaction("✅")
            await confirmation_msg.add_reaction("❌")
            use_reactions = True
        except discord.Forbidden:
            # Fallback to text confirmation if bot can't add reactions
            await channel.send(f"**{user.display_name if user else 'User'}**, I can't add reactions. Please type:\n• `confirm` or `yes` to proceed\n• `cancel` or `no` to abort")
            use_reactions = False
        
        if use_reactions:
            # Wait for reaction
            def reaction_check(reaction, react_user):
                return (
                    react_user.id == owner_id and
                    reaction.message.id == confirmation_msg.id and
                    str(reaction.emoji) in ["✅", "❌"] and
                    not react_user.bot  # Ignore bot reactions
                )
            
            try:
                reaction, react_user = await self.bot.wait_for('reaction_add', timeout=60.0, check=reaction_check)
            except asyncio.TimeoutError:
                # Handle timeout for reaction confirmation
                embed.color = 0x888888
                embed.title = "⏰ CONFIRMATION TIMEOUT"
                embed.add_field(
                    name="🛑 Status",
                    value="**TIMEOUT** - No response received within 60 seconds",
                    inline=False
                )
                await confirmation_msg.edit(embed=embed)
                return {"confirmed": False, "message": "⏰ Confirmation timed out after 60 seconds. Operation cancelled."}
        else:
            # Wait for text message
            def message_check(msg):
                return (
                    msg.author.id == owner_id and
                    msg.channel.id == channel.id and
                    msg.content.lower() in ['confirm', 'yes', 'y', 'cancel', 'no', 'n']
                )
            
            try:
                message = await self.bot.wait_for('message', timeout=60.0, check=message_check)
                # Create a fake reaction object for consistency
                class FakeReaction:
                    def __init__(self, emoji):
                        self.emoji = emoji
                
                if message.content.lower() in ['confirm', 'yes', 'y']:
                    reaction = FakeReaction("✅")
                else:
                    reaction = FakeReaction("❌")
                react_user = message.author
            except asyncio.TimeoutError:
                # Handle timeout for text confirmation
                embed.color = 0x888888
                embed.title = "⏰ CONFIRMATION TIMEOUT"
                embed.add_field(
                    name="🛑 Status",
                    value="**TIMEOUT** - No response received within 60 seconds",
                    inline=False
                )
                await confirmation_msg.edit(embed=embed)
                return {"confirmed": False, "message": "⏰ Confirmation timed out after 60 seconds. Operation cancelled."}
        
        try:
            
            # Update the embed to show the result
            if str(reaction.emoji) == "✅":
                # Confirmed - update embed to show confirmation
                embed.color = 0x00FF00
                embed.title = "✅ OPERATION CONFIRMED"
                embed.add_field(
                    name="🚀 Status",
                    value="**CONFIRMED** - Executing operation now...",
                    inline=False
                )
                await confirmation_msg.edit(embed=embed)
                
                return {"confirmed": True, "message": f"✅ Operation confirmed by {react_user.display_name}"}
            else:
                # Cancelled - update embed to show cancellation
                embed.color = 0x888888
                embed.title = "❌ OPERATION CANCELLED"
                embed.add_field(
                    name="🛑 Status",
                    value="**CANCELLED** - Operation aborted by user",
                    inline=False
                )
                await confirmation_msg.edit(embed=embed)
                
                return {"confirmed": False, "message": f"❌ Operation cancelled by {react_user.display_name}"}
                
        except asyncio.TimeoutError:
            # Timeout - update embed to show timeout
            embed.color = 0x888888
            embed.title = "⏰ CONFIRMATION TIMEOUT"
            embed.add_field(
                name="🛑 Status",
                value="**TIMEOUT** - No response received within 60 seconds",
                inline=False
            )
            await confirmation_msg.edit(embed=embed)
            
            return {"confirmed": False, "message": "⏰ Confirmation timed out after 60 seconds. Operation cancelled."}
    
    def _format_function_description(self, function_name: str, function_args: Dict[str, Any]) -> str:
        """
        Format a function call into a human-readable description.
        
        Args:
            function_name: Name of the function
            function_args: Arguments for the function
            
        Returns:
            str: Human-readable description
        """
        descriptions = {
            "delete_channel": f"Delete channel: {function_args.get('channel_identifier', 'Unknown')}",
            "delete_category_and_channels": f"Delete category: {function_args.get('category_identifier', 'Unknown')}",
            "delete_role": f"Delete role: {function_args.get('role_identifier', 'Unknown')}",
            "kick_member": f"Kick member: {function_args.get('member_identifier', 'Unknown')}",
            "ban_member": f"Ban member: {function_args.get('member_identifier', 'Unknown')}",
            "update_role_permissions": f"Update role permissions: {function_args.get('role_identifier', 'Unknown')}",
            "restore_server": f"Restore server from backup",
            "setup_word_filter": f"Setup word filter with {len(function_args.get('banned_words', []))} banned words",
            "setup_anti_spam": f"Setup anti-spam protection: {function_args.get('max_messages_per_minute', 'Unknown')} msgs/min",
            "create_channel": f"Create {function_args.get('channel_type', 'text')} channel: '{function_args.get('channel_name', 'Unknown')}'"
        }
        
        return descriptions.get(function_name, f"Execute function: {function_name}") 
    
    def _detect_function_from_text(self, ai_response: str, user_prompt: str, guild_id: int) -> Optional[Dict[str, Any]]:
        """Detect function calls from AI text responses when function calling fails."""
        return self._detect_function_from_user_prompt(user_prompt, guild_id)
    
    def _detect_function_from_user_prompt(self, user_prompt: str, guild_id: int) -> Optional[Dict[str, Any]]:
        """Enhanced function detection from user prompts with better pattern matching."""
        try:
            logger.debug(f"Function detection for: '{user_prompt}' in guild {guild_id}")
            
            lower_prompt = user_prompt.lower().strip()
            words = user_prompt.split()
            
            # Channel operations
            if any(word in lower_prompt for word in ["create", "make", "add"]) and "channel" in lower_prompt:
                # Check for multiple channels
                import re
                
                # Look for multiple channel names separated by commas or "and"
                channel_names = []
                channel_type = "text"  # default
                
                # Handle multiple patterns:
                # "make channels called hi, hello"
                # "create channels hi and hello"
                # "make multiple channels one called hi, hello"
                
                if "multiple" in lower_prompt or "," in user_prompt or " and " in lower_prompt:
                    # Extract all potential channel names
                    # Look for names after "called", "named", or in comma-separated list
                    
                    # First try to find the list after "called" or "named"
                    called_match = re.search(r'(?:called|named)\s+([^,]+(?:,\s*[^,]+)*)', user_prompt, re.IGNORECASE)
                    if called_match:
                        names_text = called_match.group(1)
                        # Split by comma and "and", then clean up
                        names_text = names_text.replace(' and ', ', ')
                        potential_names = [name.strip().strip('"\'') for name in names_text.split(',')]
                        channel_names.extend([name for name in potential_names if name and len(name) > 0])
                    
                    # Also look for "and" separated names
                    if not channel_names:
                        and_match = re.search(r'channels?\s+([a-zA-Z0-9_-]+)\s+and\s+([a-zA-Z0-9_-]+)', user_prompt, re.IGNORECASE)
                        if and_match:
                            channel_names.extend([and_match.group(1), and_match.group(2)])
                    
                    # Also look for comma-separated names anywhere in the prompt
                    if not channel_names:
                        # Find words that might be channel names (after create/make and before end)
                        create_words = ["create", "make", "add"]
                        start_idx = -1
                        for i, word in enumerate(words):
                            if any(cw in word.lower() for cw in create_words):
                                start_idx = i
                                break
                        
                        if start_idx >= 0:
                            # Look for comma-separated names after the create word
                            remaining_text = " ".join(words[start_idx:])
                            comma_names = re.findall(r'\b([a-zA-Z0-9_-]+)\b(?:\s*,|\s*and\s*|\s*$)', remaining_text)
                            channel_names.extend([name for name in comma_names if name.lower() not in ["channel", "channels", "called", "named", "one", "multiple", "text", "voice"]])
                
                # If no multiple channels found, try single channel detection
                if not channel_names:
                    channel_name = None
                    
                    # Look for channel name after "channel", "called", "named"
                    for i, word in enumerate(words):
                        if word.lower() in ["channel", "called", "named"]:
                            if i + 1 < len(words):
                                channel_name = words[i + 1].strip('"\'')
                                break
                    
                    # If no name found, try to extract from context
                    if not channel_name:
                        # Look for quoted names or names after create
                        quoted_match = re.search(r'["\']([^"\']+)["\']', user_prompt)
                        if quoted_match:
                            channel_name = quoted_match.group(1)
                        else:
                            # Try to find name after create
                            create_idx = next((i for i, w in enumerate(words) if "create" in w.lower()), -1)
                            if create_idx >= 0 and create_idx + 2 < len(words):
                                channel_name = words[create_idx + 2]
                    
                    if channel_name:
                        channel_names = [channel_name]
                
                if "voice" in lower_prompt:
                    channel_type = "voice"
                elif "category" in lower_prompt:
                    channel_type = "category"
                
                # For multiple channels, return a special indicator that the AI should create multiple
                if len(channel_names) > 1:
                    # Return a special result that indicates multiple channels should be created
                    result = {
                        "name": "create_multiple_channels",
                        "args": {
                            "guild_id": guild_id,
                            "channel_names": channel_names,
                            "channel_type": channel_type
                        }
                    }
                    logger.debug(f"Detected multiple channels: {channel_names}")
                    return result
                elif channel_names:
                    result = {
                        "name": "create_channel",
                        "args": {
                            "guild_id": guild_id,
                            "channel_name": channel_names[0],
                            "channel_type": channel_type
                        }
                    }
                    logger.debug(f"Detected channel creation: {result}")
                    return result
        
            # Role operations
            if any(word in lower_prompt for word in ["create", "make", "add"]) and "role" in lower_prompt:
                role_name = None
                color = None
                
                # Look for role name after "role", "called", "named"
                for i, word in enumerate(words):
                    if word.lower() in ["role", "called", "named"]:
                        if i + 1 < len(words):
                            role_name = words[i + 1].strip('"\'')
                            if i + 2 < len(words) and words[i + 2].startswith("#"):
                                color = words[i + 2]
                            break
                
                # If no name found, try alternative extraction
                if not role_name:
                    import re
                    quoted_match = re.search(r'["\']([^"\']+)["\']', user_prompt)
                    if quoted_match:
                        role_name = quoted_match.group(1)
                    else:
                        create_idx = next((i for i, w in enumerate(words) if "create" in w.lower()), -1)
                        if create_idx >= 0 and create_idx + 2 < len(words):
                            role_name = words[create_idx + 2]
                    
                    # Look for color anywhere in the prompt
                    color_match = re.search(r'#[0-9A-Fa-f]{6}', user_prompt)
                    if color_match:
                        color = color_match.group(0)
                    elif any(c in lower_prompt for c in ["red", "blue", "green", "yellow", "purple", "orange", "pink"]):
                        for c in ["red", "blue", "green", "yellow", "purple", "orange", "pink"]:
                            if c in lower_prompt:
                                color = c
                                break
                
                if role_name:
                    args = {
                        "guild_id": guild_id,
                        "role_name": role_name
                    }
                    if color:
                        args["color"] = color
                    
                    result = {
                        "name": "create_role",
                        "args": args
                    }
                    logger.debug(f"Detected role creation: {result}")
                    return result
            
            # List operations
            if "list" in lower_prompt or "show" in lower_prompt or "get" in lower_prompt:
                if "channel" in lower_prompt:
                    result = {
                        "name": "list_channels",
                        "args": {"guild_id": guild_id}
                    }
                    logger.debug(f"Detected list channels: {result}")
                    return result
                elif "role" in lower_prompt:
                    result = {
                        "name": "list_roles",
                        "args": {"guild_id": guild_id}
                    }
                    logger.debug(f"Detected list roles: {result}")
                    return result
            
            # Server stats
            if any(word in lower_prompt for word in ["stats", "statistics", "server info", "server status", "info"]):
                result = {
                    "name": "get_server_stats",
                    "args": {"guild_id": guild_id}
                }
                logger.debug(f"Detected server stats: {result}")
                return result
            
            logger.debug(f"No function detected for prompt: '{user_prompt}'")
            return None
            
        except Exception as e:
            logger.error(f"Error in function detection: {e}")
            return None
        
        # Delete operations
        if "delete" in lower_prompt:
            if "channel" in lower_prompt:
                # Extract channel name
                channel_name = None
                for i, word in enumerate(words):
                    if word.lower() in ["channel", "called", "named"]:
                        if i + 1 < len(words):
                            channel_name = words[i + 1].strip('"\'')
                            break
                
                if channel_name:
                    return {
                        "name": "delete_channel",
                        "args": {
                            "guild_id": guild_id,
                            "channel_identifier": channel_name
                        }
                    }
            elif "role" in lower_prompt:
                # Extract role name
                role_name = None
                for i, word in enumerate(words):
                    if word.lower() in ["role", "called", "named"]:
                        if i + 1 < len(words):
                            role_name = words[i + 1].strip('"\'')
                            break
                
                if role_name:
                    return {
                        "name": "delete_role",
                        "args": {
                            "guild_id": guild_id,
                            "role_identifier": role_name
                        }
                    }
        
        # Backup operations
        if "backup" in lower_prompt and "server" in lower_prompt:
            return {
                "name": "backup_server",
                "args": {"guild_id": guild_id}
            }
        
        return None