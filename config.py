import os
import logging

# Load environment variables from .env file if it exists
try:
    from load_env import load_env_file
    load_env_file()
except ImportError:
    pass  # load_env.py not available, continue with system env vars

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Config:
    """Configuration class to manage environment variables and secrets."""
    
    def __init__(self):
        # Discord configuration
        self.discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
        self.discord_owner_id = os.getenv("DISCORD_OWNER_ID")
        
        # API keys
        self.gpt4all_api_key = os.getenv("GPT4ALL_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        self.google_ai_key = os.getenv("GOOGLE_AI_KEY")
        self.cerebras_api_key = os.getenv("CEREBRAS_API_KEY")
        self.samurai_api_key = os.getenv("SAMURAI_API_KEY")
        self.command_whitelist = [
            int(uid) for uid in os.getenv("COMMAND_WHITELIST", "").split(",") if uid.strip().isdigit()
        ]
        
        # Validate required environment variables
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required environment variables are present."""
        missing_vars = []
        
        if not self.discord_bot_token:
            missing_vars.append("DISCORD_BOT_TOKEN")
        
        if not self.discord_owner_id:
            missing_vars.append("DISCORD_OWNER_ID")
        
        # At least one API key is required
        if not any([self.gpt4all_api_key, self.openai_api_key, self.google_ai_key, self.cerebras_api_key, self.samurai_api_key]):
            missing_vars.append("GPT4ALL_API_KEY or OPENAI_API_KEY (or OPENROUTER_API_KEY) or GOOGLE_AI_KEY or CEREBRAS_API_KEY or SAMURAI_API_KEY")
        
        if missing_vars:
            logging.warning(f"Missing environment variables: {', '.join(missing_vars)}")
            if "DISCORD_BOT_TOKEN" in missing_vars or "DISCORD_OWNER_ID" in missing_vars:
                raise ValueError(f"Missing critical environment variables: {', '.join(missing_vars)}")
        
        # Convert owner ID to integer
        try:
            self.discord_owner_id = int(self.discord_owner_id)
        except (ValueError, TypeError):
            if self.discord_owner_id:
                raise ValueError("DISCORD_OWNER_ID must be a valid integer")
    
    @property
    def is_valid(self):
        """Check if configuration is valid."""
        return all([
            self.discord_bot_token,
            self.discord_owner_id,
            any([self.gpt4all_api_key, self.openai_api_key, self.google_ai_key, self.cerebras_api_key, self.samurai_api_key])
        ])
    
    @property
    def api_keys(self):
        """Return a dictionary of available API keys."""
        return {
            "gpt4all": self.gpt4all_api_key,
            "openai": self.openai_api_key,
            "google_ai": self.google_ai_key,
            "cerebras": self.cerebras_api_key,
            "samurai_api": self.samurai_api_key
        }

# Global config instance
config = Config()