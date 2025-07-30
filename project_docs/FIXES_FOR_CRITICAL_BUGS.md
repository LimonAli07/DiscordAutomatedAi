# Critical Bug Fixes for ProjectChronos Discord Bot

## Problem Analysis

Based on the logs and testing, there are two main issues:

1. **Discord Interaction Timeouts**: Slash commands fail with `404 Unknown interaction` and `400 Interaction already acknowledged`
2. **Function Calling Not Working**: AI responds with text instead of executing Discord functions

## Root Causes

### Issue 1: Discord Interaction Handling

- Discord interactions must be acknowledged within 3 seconds
- The bot takes 15+ seconds to respond due to AI processing time
- Multiple acknowledgment attempts cause errors

### Issue 2: Function Calling Problems

- Samurai API (Claude) may not be properly calling functions
- The AI is responding with confirmations instead of executing functions
- Function schemas may not be properly formatted for Claude

## Fixes Required

### Fix 1: Immediate Interaction Response

```python
# In main.py - askai command
async def askai(interaction: discord.Interaction, command: str):
    try:
        # Immediately defer the response
        await interaction.response.defer(thinking=True)

        # Process in background
        response = await bot.ai_agent.process_command(interaction, command, debug=debug_mode)

        # Send response via followup (never fails)
        if len(response) > 2000:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.followup.send(chunk)
                else:
                    await interaction.followup.send(f"(continued...)\n{chunk}")
        else:
            await interaction.followup.send(response)

    except Exception as e:
        logger.error(f"Error processing slash command: {e}")
        # Always use followup after defer
        try:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")
        except:
            logger.error("Failed to send error response")
```

### Fix 2: Force Function Execution

The AI needs to be instructed more clearly to call functions. Update the system prompt:

```python
# In ai_agent.py - process_command method
system_prompt = f"""You are a Discord server management AI assistant with access to Discord management functions.

CRITICAL INSTRUCTIONS:
1. You MUST call the appropriate function for user requests
2. DO NOT ask for confirmation unless the function is marked as dangerous
3. DO NOT explain what you would do - DO IT by calling the function
4. For commands like "create role", "list channels", etc. - call the function immediately

Current server: {guild.name if guild else 'Unknown'} (ID: {guild_id})
Current user: {author.name} (ID: {author.id})

Available functions:
{chr(10).join(f"- {schema['name']}: {schema['description']}" for schema in self.function_schemas)}

EXAMPLES:
User: "create role TestRole red" -> Call create_role function immediately
User: "list channels" -> Call list_channels function immediately
User: "get server stats" -> Call get_server_stats function immediately

Always use guild_id {guild_id} for server operations."""
```

### Fix 3: Fallback for Non-Function-Calling APIs

If the API doesn't support function calling, implement a text-parsing fallback:

```python
# In ai_agent.py - add after line 798
# If no function calls but the response suggests an action, try to parse it
if not response.get("tool_calls") and content:
    # Try to detect function calls from text response
    detected_function = self._detect_function_from_text(content, user_prompt, guild_id)
    if detected_function:
        try:
            result = await self._execute_function(
                detected_function["name"],
                detected_function["args"],
                debug=debug,
                debug_log=debug_log
            )
            return ("\n".join(debug_log) + "\n\n" if debug else "") + f"{result}\n\n_via {provider_used}_"
        except Exception as e:
            logger.error(f"Error executing detected function: {e}")
```

### Fix 4: Function Detection Method

```python
# Add to ai_agent.py
def _detect_function_from_text(self, ai_response: str, user_prompt: str, guild_id: int) -> Optional[Dict[str, Any]]:
    """Detect function calls from AI text responses when function calling fails."""
    lower_prompt = user_prompt.lower()
    lower_response = ai_response.lower()

    # Channel operations
    if "create" in lower_prompt and "channel" in lower_prompt:
        # Extract channel name and type
        words = user_prompt.split()
        channel_name = None
        channel_type = "text"  # default

        for i, word in enumerate(words):
            if word.lower() in ["channel", "create"]:
                if i + 1 < len(words):
                    channel_name = words[i + 1]
                    break

        if "voice" in lower_prompt:
            channel_type = "voice"
        elif "category" in lower_prompt:
            channel_type = "category"

        if channel_name:
            return {
                "name": "create_channel",
                "args": {
                    "guild_id": guild_id,
                    "channel_name": channel_name,
                    "channel_type": channel_type
                }
            }

    # Role operations
    if "create" in lower_prompt and "role" in lower_prompt:
        words = user_prompt.split()
        role_name = None
        color = None

        for i, word in enumerate(words):
            if word.lower() in ["role", "create"]:
                if i + 1 < len(words):
                    role_name = words[i + 1]
                if i + 2 < len(words) and words[i + 2].startswith("#"):
                    color = words[i + 2]
                    break

        if role_name:
            args = {
                "guild_id": guild_id,
                "role_name": role_name
            }
            if color:
                args["color"] = color

            return {
                "name": "create_role",
                "args": args
            }

    # List operations
    if "list" in lower_prompt:
        if "channel" in lower_prompt:
            return {
                "name": "list_channels",
                "args": {"guild_id": guild_id}
            }
        elif "role" in lower_prompt:
            return {
                "name": "list_roles",
                "args": {"guild_id": guild_id}
            }

    # Server stats
    if any(word in lower_prompt for word in ["stats", "statistics", "server info", "server status"]):
        return {
            "name": "get_server_stats",
            "args": {"guild_id": guild_id}
        }

    return None
```

## Implementation Priority

### Immediate (Critical):

1. Fix Discord interaction handling in `main.py`
2. Update system prompt to force function calling
3. Add function detection fallback

### High Priority:

1. Test with different API providers
2. Implement better error handling
3. Add timeout protection

### Medium Priority:

1. Optimize response times
2. Add debug logging for function calls
3. Improve user feedback

## Testing Plan

### Phase 1: Fix Interaction Handling

1. Apply Discord interaction fixes
2. Test basic slash commands
3. Verify no more timeout errors

### Phase 2: Fix Function Calling

1. Update system prompts
2. Add function detection fallback
3. Test channel/role creation commands

### Phase 3: Comprehensive Testing

1. Test all command categories
2. Verify dangerous operation confirmations
3. Test with multiple API providers

## Expected Results

After implementing these fixes:

- ✅ Slash commands will respond within 3 seconds
- ✅ Functions will be called properly
- ✅ Users will see actual Discord operations (channels created, roles assigned, etc.)
- ✅ Error messages will be clear and helpful

## Files to Modify

1. **`main.py`** - Fix interaction handling
2. **`ai_agent.py`** - Update system prompt and add function detection
3. **`api_manager.py`** - Verify function calling support (already looks correct)

---

_These fixes address the core issues preventing the bot from functioning properly_
