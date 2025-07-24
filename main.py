import discord
import asyncio
import logging
from typing import Dict
from discord.ext import commands

from config import config
from ai_agent import DiscordAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DiscordBot(discord.Client):
    """Discord bot that uses AI for natural language server management."""
    
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(intents=intents)
        
        self.ai_agent = None
        self.command_prefix = "¬askai"
        # Track user sessions to maintain server context
        self.user_sessions: Dict[int, int] = {}  # user_id -> current_guild_id
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f"Bot logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Bot is connected to {len(self.guilds)} guilds")
        
        # Initialize AI agent
        self.ai_agent = DiscordAgent(self)
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{self.command_prefix} commands"
            )
        )
        
        logger.info("Bot is ready and AI agent is initialized!")
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild."""
        logger.info(f"Bot joined guild: {guild.name} (ID: {guild.id})")
    
    async def on_guild_remove(self, guild):
        """Called when the bot leaves a guild."""
        logger.info(f"Bot left guild: {guild.name} (ID: {guild.id})")
    
    async def on_message(self, message):
        """Handle incoming messages."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
        
        # Only respond to the owner
        if message.author.id != config.discord_owner_id:
            return
        
        # Check if the AI agent is initialized
        if not self.ai_agent:
            logger.error("AI agent not initialized")
            return
        
        # Check for the askai command
        if message.content.startswith(self.command_prefix):
            # Update user session to current guild
            if message.guild:
                self.user_sessions[message.author.id] = message.guild.id
            await self.handle_askai_command(message)
    
    async def handle_askai_command(self, message):
        """
        Handle the ¬askai command.
        
        Args:
            message (discord.Message): The Discord message containing the command
        """
        try:
            # Extract the prompt from the message
            command_content = message.content[len(self.command_prefix):].strip()
            
            if not command_content:
                await message.channel.send(
                    "Please provide a command after `¬askai`. "
                    "For example: `¬askai list all channels`"
                )
                return
            
            # Show typing indicator
            async with message.channel.typing():
                # Log the command
                logger.info(
                    f"Processing command from {message.author.name} "
                    f"in {message.guild.name if message.guild else 'DM'}: {command_content}"
                )
                
                # Process the command with AI
                response = await self.ai_agent.process_command(message, command_content)
                
                # Send the response
                if len(response) > 2000:
                    # Split long responses
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.channel.send(chunk)
                        else:
                            await message.channel.send(f"(continued...)\n{chunk}")
                else:
                    await message.channel.send(response)
        
        except Exception as e:
            logger.error(f"Error handling askai command: {e}")
            await message.channel.send(
                f"❌ An error occurred while processing your command: {str(e)}"
            )
    
    async def on_error(self, event, *args, **kwargs):
        """Handle general errors."""
        logger.exception(f"An error occurred in event {event}")

async def main():
    """Main function to run the bot."""
    try:
        # Validate configuration
        if not config.is_valid:
            logger.error("Configuration is invalid. Please check your environment variables.")
            return
        
        logger.info("Starting Discord bot...")
        logger.info(f"Owner ID: {config.discord_owner_id}")
        
        # Create and run the bot
        bot = DiscordBot()
        
        # Run the bot
        await bot.start(config.discord_bot_token)
    
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise
