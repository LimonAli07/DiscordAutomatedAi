import logging
from discord.ext import commands
from typing import Any, Dict, Optional

from role_management import RoleManagement
from server_management import ServerManagement
from moderation import ModerationTools
from fun_features import FunFeatures
from utility import UtilityTools

logger = logging.getLogger(__name__)

class BotIntegrator:
    """
    Integrates all the different bot features into the main bot
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.role_manager = RoleManagement(bot)
        self.server_manager = ServerManagement(bot)
        self.moderation = ModerationTools(bot)
        self.fun_features = FunFeatures(bot)
        self.utility = UtilityTools(bot)
        
    async def setup_handlers(self):
        """Set up all the event handlers for the features"""
        # Initialize moderation filters
        self.moderation._setup_event_handlers()
        
        # Initialize utility event checkers
        self.utility._setup_event_checkers()
        
        logger.info("Bot integrator: All feature handlers initialized")

    def get_function_handlers(self) -> Dict[str, Any]:
        """Get all function handlers for the enhanced_ai_agent"""
        from enhanced_discord_tools import DiscordTools
        discord_tools = DiscordTools(self.bot)
        
        handlers = {
            # Role Management
            "assign_role": self.role_manager.assign_role,
            "remove_role": self.role_manager.remove_role,
            "update_role_permissions": self.role_manager.update_role_permissions,
            
            # Server Management
            "setup_auto_role": self.server_manager.setup_auto_role,
            "setup_welcome_message": self.server_manager.setup_welcome_message,
            "backup_server": self.server_manager.backup_server,
            "restore_server": self.server_manager.restore_server,
            "get_server_stats": self.server_manager.get_server_stats,
            
            # Moderation
            "setup_word_filter": self.moderation.setup_word_filter,
            "setup_anti_spam": self.moderation.setup_anti_spam,
            "track_member_activity": self.moderation.track_member_activity,
            
            # Fun Features
            "create_poll": self.fun_features.create_poll,
            
            # Utility
            "set_reminder": self.utility.set_reminder,
            "schedule_event": self.utility.schedule_event,
            
            # Direct Discord Tools Functions
            "create_channel": discord_tools.create_channel,
            "list_channels": discord_tools.list_channels,
            "list_roles": discord_tools.list_roles
        }
        
        return handlers