# Discord AI Server Management Bot

## Overview

This repository contains a Discord bot that provides AI-powered server management capabilities using Google's Gemini API. The bot accepts natural language commands from a designated server owner and translates them into Discord server management actions through an intelligent function-calling system.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

**July 24, 2025 - Enhanced ID-based Operations**
- Added support for managing channels, roles, and members by both name and ID
- Channel deletion now accepts Discord mentions (<#123456789>), direct IDs (123456789), or channel names
- Role deletion now accepts Discord mentions (<@&123456789>), direct IDs (123456789), or role names  
- Member kick/ban now accepts Discord mentions (<@123456789>), direct IDs (123456789), usernames, or display names
- Updated function schemas in AI agent to reflect new identifier parameters
- Fixed potential "genai not defined" errors by ensuring complete migration to DeepSeek model

## System Architecture

### Core Design Pattern
The application follows a modular, agent-based architecture where:
- A Discord client receives natural language commands
- An AI agent processes commands using Gemini's function calling capabilities
- A tools module provides Discord API abstractions
- A safety layer prevents dangerous operations without explicit confirmation

### Technology Stack
- **Python**: Primary programming language
- **discord.py**: Discord API integration
- **Google Gemini API**: Natural language processing and function calling
- **Pydantic**: Data validation and modeling
- **asyncio**: Asynchronous operations

## Key Components

### 1. Main Entry Point (`main.py`)
- **Purpose**: Discord bot initialization and event handling
- **Architecture**: Custom Discord client class with intents for message content, guilds, and members
- **Key Features**: 
  - Command prefix `¬askai` for AI interactions
  - Owner-only access control
  - Bot status management

### 2. AI Agent (`ai_agent.py`)
- **Purpose**: Interface between Discord and Gemini AI
- **Architecture**: Agent pattern with function schema generation
- **Key Features**:
  - Dynamic function schema building from Discord tools
  - Pending confirmation management for dangerous operations
  - Pydantic models for type safety

### 3. Discord Tools (`discord_tools.py`)
- **Purpose**: Discord API abstraction layer
- **Architecture**: Tool pattern with categorized function safety levels
- **Key Features**:
  - Channel management operations
  - Dangerous function classification
  - Comprehensive error handling

### 4. Configuration (`config.py`)
- **Purpose**: Environment variable management and validation
- **Architecture**: Configuration object pattern
- **Key Features**:
  - Required environment variable validation
  - Type conversion and error handling
  - Security-focused design

## Data Flow

### Command Processing Flow
1. User sends `¬askai [natural language command]` in Discord
2. Bot validates user is the designated owner
3. AI agent receives command and builds function schemas
4. Gemini API processes command and suggests function calls
5. If function is dangerous, confirmation is requested
6. Upon confirmation, function executes via Discord tools
7. Results are processed by Gemini and returned as natural language

### Safety Confirmation Flow
1. Dangerous function detected in AI response
2. Confirmation message sent to Discord with function details
3. 60-second timeout window for owner response
4. Only "yes" response proceeds with execution
5. All other responses or timeout cancels operation

## External Dependencies

### Required Environment Variables
- `DISCORD_BOT_TOKEN`: Discord bot authentication token
- `GEMINI_API_KEY`: Google Gemini API access key
- `DISCORD_OWNER_ID`: Numeric Discord user ID for authorized user

### API Integrations
- **Discord API**: Server management operations via discord.py
- **Google Gemini API**: Natural language processing and function calling
- **Replit Secrets**: Secure environment variable storage

### Python Packages
- `discord.py`: Discord bot framework
- `google-genai`: Google Gemini API client
- `pydantic`: Data validation and modeling
- `asyncio`: Asynchronous programming support

## Deployment Strategy

### Environment Setup
- Designed for Replit deployment with integrated secrets management
- No database requirements (stateless operation)
- Minimal resource requirements for small to medium Discord servers

### Security Considerations
- Hard-coded owner ID restriction prevents unauthorized access
- Dangerous function classification with mandatory confirmation
- Environment variable validation prevents misconfiguration
- No persistent data storage reduces attack surface

### Scalability Design
- Single-server focus (not designed for multi-guild operation)
- Function-based architecture allows easy extension
- Async operation prevents blocking on Discord API calls
- Modular design supports adding new Discord management capabilities

## Key Architectural Decisions

### Agent-Based AI Integration
- **Problem**: Need to translate natural language to Discord API calls
- **Solution**: Gemini function calling with dynamic schema generation
- **Rationale**: Provides flexibility while maintaining type safety and clear function boundaries

### Safety-First Design
- **Problem**: AI could execute destructive operations
- **Solution**: Dangerous function classification with mandatory human confirmation
- **Rationale**: Balances automation convenience with operational safety

### Owner-Only Access
- **Problem**: Prevent unauthorized server management
- **Solution**: Hard-coded owner ID validation
- **Rationale**: Simple, secure access control without complex permission systems

### Modular Tool Architecture
- **Problem**: Need extensible Discord management capabilities
- **Solution**: Separate tools module with standardized function signatures
- **Rationale**: Enables easy addition of new capabilities while maintaining consistent AI integration