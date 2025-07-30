import discord
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class FunFeatures:
    """Fun features for the Discord bot."""
    
    def __init__(self, bot: discord.Client):
        self.bot = bot
        
    async def create_poll(self, guild_id: int, channel_identifier: str, question: str, options: List[str], duration_minutes: int = 60) -> str:
        """
        Create a poll in a channel.
        
        Args:
            guild_id: The ID of the Discord server
            channel_identifier: The name or ID of the channel
            question: The poll question
            options: List of poll options (max 10)
            duration_minutes: How long the poll should last (0 for no time limit)
            
        Returns:
            str: Success or error message
        """
        try:
            from enhanced_discord_tools import DiscordTools
            tools = DiscordTools(self.bot)
            
            channel = await tools.get_channel_by_name_or_id(guild_id, channel_identifier)
            if not channel:
                return f"Error: Channel '{channel_identifier}' not found"
                
            # Check if the channel is a text channel
            if not isinstance(channel, discord.TextChannel):
                return f"Error: Cannot create poll in a {channel.type} channel"
                
            # Validate options
            if len(options) < 2:
                return "Error: Poll must have at least 2 options"
                
            if len(options) > 10:
                return "Error: Poll can have a maximum of 10 options"
                
            # Emoji numbers for options
            emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            # Format the poll message
            poll_lines = [f"📊 **POLL: {question}**\n"]
            for i, option in enumerate(options):
                poll_lines.append(f"{emoji_numbers[i]} {option}")
                
            if duration_minutes > 0:
                end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
                poll_lines.append(f"\nPoll ends: <t:{int(end_time.timestamp())}:R>")
                
            poll_message = "\n".join(poll_lines)
            
            # Send the poll
            poll = await channel.send(poll_message)
            
            # Add reactions for each option
            for i in range(len(options)):
                await poll.add_reaction(emoji_numbers[i])
                
            # Set up timer for ending the poll if duration is set
            if duration_minutes > 0 and hasattr(self.bot, "loop"):
                # Create a task to end the poll
                async def end_poll():
                    await asyncio.sleep(duration_minutes * 60)
                    
                    try:
                        # Get updated message
                        updated_poll = await channel.fetch_message(poll.id)
                        
                        # Count votes
                        results = {}
                        for reaction in updated_poll.reactions:
                            if str(reaction.emoji) in emoji_numbers:
                                # Subtract 1 for the bot's own reaction
                                option_index = emoji_numbers.index(str(reaction.emoji))
                                if option_index < len(options):
                                    results[options[option_index]] = max(0, reaction.count - 1)
                        
                        # Format results
                        result_lines = [f"📊 **POLL RESULTS: {question}**\n"]
                        
                        # Sort results by votes (descending)
                        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
                        total_votes = sum(results.values())
                        
                        for option, votes in sorted_results:
                            percentage = (votes / total_votes) * 100 if total_votes > 0 else 0
                            result_lines.append(f"{option}: {votes} votes ({percentage:.1f}%)")
                            
                        result_lines.append(f"\nTotal votes: {total_votes}")
                        
                        # Send results message
                        await channel.send("\n".join(result_lines))
                        
                        # Edit original poll to show it ended
                        await updated_poll.edit(content=updated_poll.content + "\n\n**Poll has ended**")
                        
                    except Exception as e:
                        logger.error(f"Error ending poll: {e}")
                
                # Start the task
                self.bot.loop.create_task(end_poll())
                
            return f"✅ Poll created in channel #{channel.name}"
            
        except Exception as e:
            logger.error(f"Error creating poll: {e}")
            return f"Error creating poll: {str(e)}"