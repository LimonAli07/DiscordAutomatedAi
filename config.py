import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Config:
    """Configuration class to manage environment variables and secrets."""
    
    def __init__(self):
        self.discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.discord_owner_id = os.getenv("DISCORD_OWNER_ID")
        
        # Validate required environment variables
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required environment variables are present."""
        missing_vars = []
        
        if not self.discord_bot_token:
            missing_vars.append("DISCORD_BOT_TOKEN")
        
        if not self.gemini_api_key:
            missing_vars.append("GEMINI_API_KEY")
        
        if not self.discord_owner_id:
            missing_vars.append("DISCORD_OWNER_ID")
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Convert owner ID to integer
        try:
            self.discord_owner_id = int(self.discord_owner_id)
        except ValueError:
            raise ValueError("DISCORD_OWNER_ID must be a valid integer")
    
    @property
    def is_valid(self):
        """Check if configuration is valid."""
        return all([
            self.discord_bot_token,
            self.gemini_api_key,
            self.discord_owner_id
        ])

# Global config instance
config = Config()
