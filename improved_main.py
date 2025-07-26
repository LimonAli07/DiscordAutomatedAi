import discord
import asyncio
import logging
from typing import Dict, Optional
from discord.ext import commands
from discord import app_commands

from config import config
from ai_agent import DiscordAgent
from api_manager import APIManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DiscordBot(discord.Client):
    """Discord bot that uses AI for natural language server management with slash commands."""
    
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.ai_agent = None
        self.legacy_command_prefix = "¬askai"  # Keep for backward compatibility
        self.api_manager = None
        # Track user sessions to maintain server context
        self.user_sessions: Dict[int, int] = {}  # user_id -> current_guild_id
        # Store pending confirmations
        self.pending_confirmations: Dict[int, Dict[str, any]] = {}
        
    async def setup_hook(self):
        """Called when the client is done preparing data."""
        # Register global slash commands
        await self.tree.sync()
        logger.info("Slash commands synced globally")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f"Bot logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Bot is connected to {len(self.guilds)} guilds")
        
        # Initialize AI agent
        self.api_manager = APIManager()
        self.ai_agent = DiscordAgent(self, self.api_manager)
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"/askai commands"
            )
        )
        
        logger.info("Bot is ready and AI agent is initialized!")
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild."""
        logger.info(f"Bot joined guild: {guild.name} (ID: {guild.id})")
        try:
            # Try to sync commands to the new guild
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Synced slash commands to {guild.name}")
        except Exception as e:
            logger.error(f"Failed to sync slash commands to {guild.name}: {e}")
    
    async def on_guild_remove(self, guild):
        """Called when the bot leaves a guild."""
        logger.info(f"Bot left guild: {guild.name} (ID: {guild.id})")
        
        # Clean up any session data for users in this guild
        for user_id, guild_id in list(self.user_sessions.items()):
            if guild_id == guild.id:
                del self.user_sessions[user_id]
    
    async def on_message(self, message):
        """Handle incoming messages for legacy command support."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
        
        # Only respond to the owner for legacy commands
        if message.author.id != config.discord_owner_id:
            return
        
        # Check if the AI agent is initialized
        if not self.ai_agent:
            logger.error("AI agent not initialized")
            return
        
        # Check for the legacy askai command
        if message.content.startswith(self.legacy_command_prefix):
            # Update user session to current guild
            if message.guild:
                self.user_sessions[message.author.id] = message.guild.id
            
            # Clear any pending confirmations when starting new command
            if message.author.id in self.pending_confirmations:
                del self.pending_confirmations[message.author.id]
                
            await self.handle_legacy_askai_command(message)
    
    async def handle_legacy_askai_command(self, message):
        """
        Handle the legacy ¬askai command.
        
        Args:
            message (discord.Message): The Discord message containing the command
        """
        try:
            # Extract the prompt from the message
            command_content = message.content[len(self.legacy_command_prefix):].strip()
            
            if not command_content:
                await message.channel.send(
                    "Please provide a command after `¬askai`. "
                    "For example: `¬askai list all channels`\n"
                    "Pro tip: You can now use slash commands! Try `/askai` instead."
                )
                return
            
            # Show typing indicator
            async with message.channel.typing():
                # Log the command
                logger.info(
                    f"Processing legacy command from {message.author.name} "
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

    async def on_reaction_add(self, reaction, user):
        """Handle reaction confirmations for dangerous operations."""
        # Ignore bot's own reactions
        if user == self.user:
            return
            
        # Check if this is a confirmation reaction
        confirmation_data = self.pending_confirmations.get(user.id)
        if not confirmation_data:
            return
            
        # Check if this is the right message
        if reaction.message.id != confirmation_data.get('message_id'):
            return
            
        # Check if this is a valid reaction
        if str(reaction.emoji) == "✅":
            # Execute the confirmed action
            if callable(confirmation_data.get('confirm_callback')):
                try:
                    result = await confirmation_data['confirm_callback']()
                    await reaction.message.edit(
                        content=f"{reaction.message.content}\n\n✅ **Confirmed - Action completed:**\n{result}"
                    )
                except Exception as e:
                    logger.error(f"Error executing confirmed action: {e}")
                    await reaction.message.edit(
                        content=f"{reaction.message.content}\n\n❌ **Error executing action:** {str(e)}"
                    )
            # Remove from pending confirmations
            del self.pending_confirmations[user.id]
                
        elif str(reaction.emoji) == "❌":
            # Cancel the action
            await reaction.message.edit(
                content=f"{reaction.message.content}\n\n❌ **Action cancelled by user**"
            )
            # Remove from pending confirmations
            del self.pending_confirmations[user.id]

    async def on_message_reaction_add(self, reaction, user):
        """Alias for on_reaction_add for compatibility."""
        await self.on_reaction_add(reaction, user)

    async def register_slash_commands(self, guild=None):
        """Register the bot's slash commands, optionally for a specific guild."""
        try:
            if guild:
                await self.tree.sync(guild=discord.Object(id=guild.id))
            else:
                await self.tree.sync()
        except Exception as e:
            logger.error(f"Error registering slash commands: {e}")

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
        
        # Set up slash commands
        @bot.tree.command(name="askai", description="Ask the AI agent to perform an action")
        @app_commands.describe(
            command="The command or question for the AI agent"
        )
        async def askai(interaction: discord.Interaction, command: str):
            """Slash command for AI agent interaction."""
            try:
                # Update user session to current guild
                if interaction.guild:
                    bot.user_sessions[interaction.user.id] = interaction.guild.id
                
                # Check if the AI agent is initialized
                if not bot.ai_agent:
                    await interaction.response.send_message("AI agent not initialized. Please try again later.")
                    return
                
                # Defer response to allow for longer processing time
                await interaction.response.defer(thinking=True)
                
                # Process the command with AI
                response = await bot.ai_agent.process_command(interaction, command)
                
                # Send the response
                if len(response) > 2000:
                    # For longer responses, send follow-up messages
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    first_chunk = True
                    for chunk in chunks:
                        if first_chunk:
                            await interaction.followup.send(chunk)
                            first_chunk = False
                        else:
                            await interaction.followup.send(f"(continued...)\n{chunk}")
                else:
                    await interaction.followup.send(response)
            
            except Exception as e:
                logger.error(f"Error processing slash command: {e}")
                # Make sure we respond even if there's an error
                try:
                    await interaction.followup.send(f"❌ An error occurred: {str(e)}")
                except:
                    # If followup fails, try response
                    try:
                        await interaction.response.send_message(f"❌ An error occurred: {str(e)}")
                    except:
                        logger.error("Failed to send error response")
        
        # Command to delete a category and all its channels
        @bot.tree.command(name="deletecategory", description="Delete a category and all its channels")
        @app_commands.describe(
            category="The name or ID of the category to delete"
        )
        async def delete_category(interaction: discord.Interaction, category: str):
            """Delete a category and all its channels."""
            # Check if user has administrator permissions
            if not interaction.user.guild_permissions.administrator and interaction.user.id != config.discord_owner_id:
                await interaction.response.send_message("❌ You need administrator permissions to use this command.")
                return
            
            # Defer response to allow time for processing
            await interaction.response.defer(thinking=True)
            
            try:
                guild = interaction.guild
                # Find the category
                target_category = None
                for cat in guild.categories:
                    if cat.name.lower() == category.lower() or str(cat.id) == category:
                        target_category = cat
                        break
                
                if not target_category:
                    await interaction.followup.send(f"❌ Could not find category '{category}'")
                    return
                
                # Request confirmation
                confirm_msg = await interaction.followup.send(
                    f"⚠️ **DANGEROUS OPERATION** ⚠️\n\n"
                    f"You are about to delete the category '{target_category.name}' and ALL its channels.\n"
                    f"This will delete {len(target_category.channels)} channels.\n\n"
                    f"React with ✅ to confirm or ❌ to cancel (90 seconds)"
                )
                
                # Add reaction options
                await confirm_msg.add_reaction("✅")
                await confirm_msg.add_reaction("❌")
                
                # Store confirmation data with callback
                async def execute_deletion():
                    results = []
                    # Delete all channels in the category
                    for channel in target_category.channels:
                        try:
                            await channel.delete(reason=f"Deleted as part of category deletion by {interaction.user}")
                            results.append(f"✅ Deleted channel: #{channel.name}")
                        except Exception as e:
                            results.append(f"❌ Failed to delete channel #{channel.name}: {str(e)}")
                    
                    # Finally delete the category itself
                    try:
                        await target_category.delete(reason=f"Category deletion by {interaction.user}")
                        results.append(f"✅ Deleted category: {target_category.name}")
                    except Exception as e:
                        results.append(f"❌ Failed to delete category {target_category.name}: {str(e)}")
                    
                    return "\n".join(results)
                
                bot.pending_confirmations[interaction.user.id] = {
                    'message_id': confirm_msg.id,
                    'confirm_callback': execute_deletion
                }
                
                # We don't need to wait for the reaction here since it's handled in on_reaction_add
                
            except Exception as e:
                logger.error(f"Error in delete_category command: {e}")
                await interaction.followup.send(f"❌ An error occurred: {str(e)}")
        
        # Create role command
        @bot.tree.command(name="createrole", description="Create a new role in the server")
        @app_commands.describe(
            name="The name for the new role",
            color="Hex color code (e.g., #FF0000) or color name (red, blue, etc.)",
            permissions="Comma-separated list of permissions (e.g., kick_members,ban_members)"
        )
        async def create_role(interaction: discord.Interaction, name: str, color: Optional[str] = None, permissions: Optional[str] = None):
            """Create a new role with specified properties."""
            # Check if user has manage_roles permission
            if not interaction.user.guild_permissions.manage_roles and interaction.user.id != config.discord_owner_id:
                await interaction.response.send_message("❌ You need 'Manage Roles' permission to use this command.")
                return
            
            await interaction.response.defer(thinking=True)
            
            try:
                guild = interaction.guild
                
                # Parse permissions if provided
                perms_list = None
                if permissions:
                    perms_list = [p.strip() for p in permissions.split(',')]
                
                # Use discord tools for role creation
                if bot.ai_agent and bot.ai_agent.discord_tools:
                    result = await bot.ai_agent.discord_tools.create_role(
                        guild_id=guild.id,
                        role_name=name,
                        color=color,
                        permissions=perms_list
                    )
                    await interaction.followup.send(result)
                else:
                    await interaction.followup.send("❌ Bot services are not fully initialized. Please try again later.")
                
            except Exception as e:
                logger.error(f"Error in create_role command: {e}")
                await interaction.followup.send(f"❌ An error occurred: {str(e)}")
        
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