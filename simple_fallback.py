#!/usr/bin/env python3
"""
Simple fallback AI for when all external APIs are down.
"""

import re
from typing import Dict, Any, List

class SimpleFallbackAI:
    """Simple AI fallback that can handle basic Discord commands."""
    
    def __init__(self):
        self.command_patterns = {
            r'create.*channel.*called\s+(\w+)': 'create_channel',
            r'list.*channel': 'list_channels',
            r'create.*role.*called\s+(\w+)': 'create_role',
            r'list.*role': 'list_roles',
            r'backup.*server': 'backup_server',
            r'get.*stats': 'get_server_stats',
            r'create.*poll': 'create_poll',
            r'set.*reminder': 'set_reminder',
            r'help': 'help',
            r'debug': 'debug'
        }
    
    def process_command(self, user_prompt: str, guild_id: int = None) -> Dict[str, Any]:
        """Process a user command and return function call data."""
        user_prompt_lower = user_prompt.lower()
        
        # Check for help requests
        if any(word in user_prompt_lower for word in ['help', 'how', 'usage', 'example']):
            return {
                "content": self._get_help_message(),
                "tool_calls": [],
                "provider": "simple_fallback"
            }
        
        # Check for debug requests
        if user_prompt_lower.startswith('debug'):
            return {
                "content": "🔧 **Debug Mode Active**\n\nThis is the simple fallback AI. External APIs are currently unavailable.\n\nAvailable commands:\n- Create channels\n- List channels\n- Create roles\n- List roles\n- Backup server\n- Get stats\n- Create polls\n- Set reminders",
                "tool_calls": [],
                "provider": "simple_fallback"
            }
        
        # Match command patterns
        for pattern, function_name in self.command_patterns.items():
            match = re.search(pattern, user_prompt_lower)
            if match:
                args = self._extract_args(user_prompt, function_name, match)
                # Set the guild_id dynamically if provided
                if guild_id is not None:
                    args["guild_id"] = guild_id
                return {
                    "content": f"I'll help you with that! Using simple fallback AI.",
                    "tool_calls": [{
                        "id": "fallback-call-1",
                        "name": function_name,
                        "args": args
                    }],
                    "provider": "simple_fallback"
                }
        
        # Default response
        return {
            "content": "I understand you want to do something with the server. I'm currently using a simple fallback AI since external APIs are unavailable. Try commands like:\n- Create a text channel called general\n- List all channels\n- Create a role called Moderator\n- Backup this server",
            "tool_calls": [],
            "provider": "simple_fallback"
        }
    
    def _extract_args(self, user_prompt: str, function_name: str, match) -> Dict[str, Any]:
        """Extract arguments from user prompt."""
        args = {}
        
        if function_name == "create_channel":
            channel_name = match.group(1) if match.groups() else "general"
            args.update({
                "channel_name": channel_name,
                "channel_type": "text"
            })
        elif function_name == "create_role":
            role_name = match.group(1) if match.groups() else "New Role"
            args.update({
                "role_name": role_name,
                "color": "blue"
            })
        
        return args
    
    def _get_help_message(self) -> str:
        """Get help message."""
        return """🤖 **Simple Fallback AI Help**

Since external APIs are unavailable, I'm using a simple fallback AI.

**Available Commands:**
- `create a text channel called [name]` - Create a new channel
- `list all channels` - List server channels  
- `create a role called [name]` - Create a new role
- `list all roles` - List server roles
- `backup this server` - Create server backup
- `get server stats` - Get server statistics
- `create a poll` - Create a poll
- `set a reminder` - Set a reminder
"""