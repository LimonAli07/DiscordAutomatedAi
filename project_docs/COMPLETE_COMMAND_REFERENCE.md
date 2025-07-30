# ProjectChronos Discord Bot - Complete Command Reference

## Overview

This document provides a comprehensive reference for all available commands in the ProjectChronos Discord bot, organized by functionality and testing status.

## Bot Status

- **Status**: Running (python main.py active)
- **Total Commands Available**: 46+ commands across 11 categories
- **Command Types**: Slash commands + AI agent commands
- **Safety Features**: Confirmation required for dangerous operations

## Command Categories

### 1. Basic Functionality (4 commands)

Essential commands for bot operation and status checking.

| Command                   | Description                          | Safety Level |
| ------------------------- | ------------------------------------ | ------------ |
| `/askai get_api_status`   | Check status of all AI API providers | Safe         |
| `/askai help`             | Get help information                 | Safe         |
| `/askai list_channels`    | List all channels in server          | Safe         |
| `/askai get_server_stats` | Get detailed server statistics       | Safe         |

### 2. Channel Management (9 commands)

Commands for creating, modifying, and managing Discord channels.

| Command                                          | Description                          | Safety Level  |
| ------------------------------------------------ | ------------------------------------ | ------------- |
| `/askai list_channels`                           | List all channels with types and IDs | Safe          |
| `/askai create_channel <name> <type> [category]` | Create text/voice/category channels  | Safe          |
| `/askai set_slowmode <channel> <seconds>`        | Set slowmode (0-21600 seconds)       | Safe          |
| `/askai lock_channel <channel>`                  | Prevent @everyone from messaging     | Safe          |
| `/askai unlock_channel <channel>`                | Allow @everyone to message           | Safe          |
| `/askai purge_messages <channel> <limit> [user]` | Bulk delete messages (max 100)       | Moderate      |
| `/askai delete_channel <channel>`                | Delete a channel                     | **DANGEROUS** |

**Example Usage:**

```
/askai create_channel test-channel text
/askai create_channel test-voice voice
/askai create_channel test-category category
/askai set_slowmode general 5
/askai lock_channel spam-channel
```

### 3. Role Management (5 commands)

Commands for creating and managing Discord roles and permissions.

| Command                                               | Description                         | Safety Level  |
| ----------------------------------------------------- | ----------------------------------- | ------------- |
| `/askai list_roles`                                   | List all roles in server            | Safe          |
| `/askai create_role <name> [color] [permissions]`     | Create new role with properties     | Safe          |
| `/askai assign_role <member> <role>`                  | Assign role to member               | Safe          |
| `/askai remove_role <member> <role>`                  | Remove role from member             | Safe          |
| `/askai update_role_permissions <role> <permissions>` | Update role permissions             | **DANGEROUS** |
| `/askai delete_role <role>`                           | Delete a role                       | **DANGEROUS** |
| `/createrole <name> [color] [permissions]`            | Direct slash command to create role | Safe          |

**Example Usage:**

```
/askai create_role TestRole #FF0000 send_messages,read_messages
/askai create_role ModeratorRole #00FF00 kick_members,ban_members
/askai assign_role @username TestRole
/createrole AdvancedRole #FFFF00 administrator
```

### 4. Server Management (4 commands)

Commands for managing server-wide settings and configurations.

| Command                                            | Description                      | Safety Level  |
| -------------------------------------------------- | -------------------------------- | ------------- |
| `/askai get_server_stats`                          | Detailed server statistics       | Safe          |
| `/askai backup_server`                             | Create backup of server settings | Safe          |
| `/askai setup_auto_role <role>`                    | Auto-assign role to new members  | Safe          |
| `/askai setup_welcome_message <channel> <message>` | Set welcome message              | Safe          |
| `/askai restore_server [backup_id]`                | Restore from backup              | **DANGEROUS** |

**Example Usage:**

```
/askai backup_server
/askai setup_auto_role Member
/askai setup_welcome_message general Welcome {user} to {server}!
```

### 5. Moderation Commands (8 commands)

Commands for moderating members and managing behavior.

| Command                                             | Description                  | Safety Level  |
| --------------------------------------------------- | ---------------------------- | ------------- |
| `/askai timeout_member <member> <minutes> [reason]` | Timeout/mute member          | Moderate      |
| `/askai remove_timeout <member>`                    | Remove timeout from member   | Safe          |
| `/askai set_nickname <member> [nickname]`           | Change member nickname       | Safe          |
| `/askai unban_member <user> [reason]`               | Unban previously banned user | Moderate      |
| `/askai kick_member <member> [reason]`              | Kick member from server      | **DANGEROUS** |
| `/askai ban_member <member> [reason] [days]`        | Ban member from server       | **DANGEROUS** |

**Example Usage:**

```
/askai timeout_member @spammer 10 Spamming messages
/askai set_nickname @user NewNickname
/askai remove_timeout @user
```

### 6. Moderation Tools (3 commands)

Advanced moderation automation and tracking.

| Command                                                | Description              | Safety Level  |
| ------------------------------------------------------ | ------------------------ | ------------- |
| `/askai setup_word_filter <words> <action>`            | Auto-filter banned words | **DANGEROUS** |
| `/askai setup_anti_spam <threshold> <window> <action>` | Anti-spam protection     | **DANGEROUS** |
| `/askai track_member_activity [channel]`               | Enable activity tracking | Safe          |

**Example Usage:**

```
/askai setup_word_filter badword1,badword2 delete
/askai setup_anti_spam 5 3 timeout
/askai track_member_activity mod-logs
```

### 7. Utility Commands (3 commands)

Helpful utility features for server management.

| Command                                                        | Description             | Safety Level |
| -------------------------------------------------------------- | ----------------------- | ------------ |
| `/askai set_reminder <channel> <message> <time>`               | Set timed reminder      | Safe         |
| `/askai schedule_event <name> <description> <time> [channel]`  | Schedule server event   | Safe         |
| `/askai create_poll <channel> <question> <options> [duration]` | Create interactive poll | Safe         |

**Example Usage:**

```
/askai set_reminder general Meeting in 5 minutes +5m
/askai schedule_event Game Night Weekly gaming session +1h events
/askai create_poll general Favorite color? Red,Blue,Green,Yellow 60
```

### 8. Message Management (2 commands)

Commands for managing messages in channels.

| Command                                          | Description                        | Safety Level |
| ------------------------------------------------ | ---------------------------------- | ------------ |
| `/askai purge_messages <channel> <limit>`        | Delete multiple messages           | Moderate     |
| `/askai purge_messages <channel> <limit> <user>` | Delete messages from specific user | Moderate     |

### 9. Dangerous Operations (8 commands)

High-risk commands that require confirmation via reaction.

| Command                                               | Description                             | Confirmation Required |
| ----------------------------------------------------- | --------------------------------------- | --------------------- |
| `/askai delete_channel <channel>`                     | Delete channel                          | ✅ Yes                |
| `/askai delete_role <role>`                           | Delete role                             | ✅ Yes                |
| `/askai kick_member <member> [reason]`                | Kick member                             | ✅ Yes                |
| `/askai ban_member <member> [reason]`                 | Ban member                              | ✅ Yes                |
| `/askai delete_category_and_channels <category>`      | Delete category + channels              | ✅ Yes                |
| `/deletecategory <category>`                          | Direct slash command to delete category | ✅ Yes                |
| `/askai restore_server [backup_id]`                   | Restore server from backup              | ✅ Yes                |
| `/askai update_role_permissions <role> <permissions>` | Modify role permissions                 | ✅ Yes                |

### 10. Advanced Features (2 commands)

Advanced server management capabilities.

| Command                                               | Description                                | Safety Level  |
| ----------------------------------------------------- | ------------------------------------------ | ------------- |
| `/askai update_role_permissions <role> <permissions>` | Advanced permission management             | **DANGEROUS** |
| `/createrole <name> <color> <permissions>`            | Direct role creation with full permissions | Moderate      |

### 11. Debug Commands (2 commands)

Owner-only debugging and diagnostic commands.

| Command                       | Description                  | Access Level |
| ----------------------------- | ---------------------------- | ------------ |
| `/askai debug get_api_status` | Debug API status information | Owner Only   |
| `/askai debug list_channels`  | Debug channel listing        | Owner Only   |

## Testing Priority

### Phase 1: Essential Commands (Test First)

```
/askai get_api_status
/askai list_channels
/askai list_roles
/askai get_server_stats
/askai create_channel test-text text
/askai create_role TestRole #FF0000
/askai create_poll general Test poll? Yes,No 5
```

### Phase 2: Safe Operations

- Channel creation and management
- Role creation and assignment
- Server statistics and backups
- Utility commands (reminders, events, polls)

### Phase 3: Moderation Features

- Timeouts and nickname changes
- Message purging
- Anti-spam and word filters

### Phase 4: Dangerous Operations (Test Last)

- Channel/role deletion
- Member kicks/bans
- Category deletion
- Server restoration

## Safety Features

### Confirmation System

All dangerous operations require user confirmation via Discord reactions:

- ✅ to confirm and execute
- ❌ to cancel operation
- 90-second timeout for confirmations

### Permission Checks

- Bot validates its own permissions before executing commands
- Role hierarchy respected (can't modify higher roles)
- Administrator permissions required for dangerous operations

### Error Handling

- Comprehensive error messages for invalid operations
- Graceful handling of missing permissions
- Detailed logging for debugging

## Command Syntax Notes

### Parameter Types

- `<required>` - Required parameter
- `[optional]` - Optional parameter
- `<member>` - Can be @mention, username, nickname, or user ID
- `<channel>` - Can be #mention, channel name, or channel ID
- `<role>` - Can be role name or role ID
- `<time>` - Relative (+5m, +1h, +2d) or ISO format

### Color Formats

- Hex codes: `#FF0000`, `#00FF00`
- Color names: `red`, `blue`, `green`, `yellow`, `orange`, `purple`, `pink`, `white`, `black`, `gold`, `cyan`, `magenta`

### Permission Names

Common permissions for roles:

- `send_messages`, `read_messages`, `manage_messages`
- `kick_members`, `ban_members`, `manage_roles`
- `manage_channels`, `manage_guild`, `administrator`

## Files Generated

- `bot_command_test_plan.md` - Detailed testing methodology
- `test_all_commands.py` - Automated test plan generator
- `bot_test_plan.json` - Machine-readable test plan
- `COMPLETE_COMMAND_REFERENCE.md` - This comprehensive reference

## Total Command Count: 46+ Commands

The bot provides extensive functionality across all major Discord server management areas, with proper safety measures and comprehensive testing coverage.
