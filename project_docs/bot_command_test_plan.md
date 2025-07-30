# Discord Bot Command Test Plan

## Overview

This document outlines all available commands in the ProjectChronos Discord bot and provides a systematic testing approach.

## Available Commands

### 1. Slash Commands (Direct Discord Commands)

- `/askai <command>` - Main AI agent interaction command
- `/deletecategory <category>` - Delete a category and all its channels (DANGEROUS)
- `/createrole <name> [color] [permissions]` - Create a new role

### 2. AI Agent Commands (via /askai)

#### Channel Management

- `list_channels` - List all channels in the server
- `create_channel` - Create text/voice/category channels
- `delete_channel` - Delete a channel (DANGEROUS)
- `delete_category_and_channels` - Delete category and all channels (DANGEROUS)
- `lock_channel` - Prevent @everyone from sending messages
- `unlock_channel` - Allow @everyone to send messages
- `set_slowmode` - Set slowmode delay (0-21600 seconds)
- `purge_messages` - Bulk delete messages (max 100)

#### Role Management

- `list_roles` - List all roles in the server
- `create_role` - Create a new role with permissions/color
- `delete_role` - Delete a role (DANGEROUS)
- `assign_role` - Assign role to a member
- `remove_role` - Remove role from a member
- `update_role_permissions` - Update role permissions (DANGEROUS)

#### Moderation

- `kick_member` - Kick a member (DANGEROUS)
- `ban_member` - Ban a member (DANGEROUS)
- `unban_member` - Unban a previously banned user
- `timeout_member` - Timeout/mute a member
- `remove_timeout` - Remove timeout from a member
- `set_nickname` - Change a member's nickname

#### Server Management

- `setup_auto_role` - Set role to auto-assign to new members
- `setup_welcome_message` - Set welcome message for new members
- `backup_server` - Create backup of server settings
- `restore_server` - Restore server from backup (DANGEROUS)
- `get_server_stats` - Get detailed server statistics

#### Utility Tools

- `set_reminder` - Set a reminder for a specific time
- `schedule_event` - Schedule an event in the server

#### Moderation Tools

- `setup_word_filter` - Set up automatic word filtering (DANGEROUS)
- `setup_anti_spam` - Set up anti-spam protection (DANGEROUS)
- `track_member_activity` - Enable member activity tracking

#### Fun Features

- `create_poll` - Create a poll with multiple options

#### API Status

- `get_api_status` - Get status of all AI API providers

## Test Categories

### Basic Functionality Tests

1. Bot connection and status
2. Slash command registration
3. Basic /askai command response

### Channel Management Tests

1. List all channels
2. Create text channel
3. Create voice channel
4. Create category
5. Lock/unlock channels
6. Set slowmode
7. Purge messages
8. Delete channel (with confirmation)

### Role Management Tests

1. List all roles
2. Create role with color and permissions
3. Assign role to member
4. Remove role from member
5. Update role permissions
6. Delete role (with confirmation)

### Moderation Tests

1. Timeout member
2. Remove timeout
3. Set nickname
4. Kick member (with confirmation)
5. Ban member (with confirmation)
6. Unban member

### Server Management Tests

1. Get server statistics
2. Setup auto-role
3. Setup welcome message
4. Create server backup
5. Test restore server (preparation only)

### Utility Tests

1. Set reminder
2. Schedule event
3. Create poll

### Moderation Tools Tests

1. Setup word filter
2. Setup anti-spam protection
3. Enable activity tracking

### API and Debug Tests

1. Get API status
2. Debug mode commands (owner only)

## Test Execution Plan

### Phase 1: Basic Commands

- Test bot responsiveness
- Test basic /askai functionality
- Test simple information commands

### Phase 2: Safe Operations

- Channel listing and creation
- Role listing and creation
- Server statistics
- Polls and utilities

### Phase 3: Moderation Features

- Timeout/nickname changes
- Message purging
- Anti-spam and word filters

### Phase 4: Dangerous Operations (with confirmation)

- Channel/role deletion
- Member kicks/bans
- Category deletion

## Safety Notes

- All DANGEROUS operations require confirmation via reaction
- Test on a dedicated test server
- Have backup plans for restoration
- Test with appropriate permissions
