# ProjectChronosBot


ProjectChronosBot is an advanced AI-powered Discord bot designed to streamline server management, enhance moderation, and engage communities with intelligent features. It leverages natural language understanding and slash commands to provide a seamless and powerful user experience.

**Note:** This project does not include any built-in API providers (such as OpenAI, GPT4All, Samurai, etc). You must add your own API provider(s) and keys in your `.env` file and code as needed. Please refer to the documentation for integration instructions.

## 🚀 Features

### 🤖 AI-Powered Interaction

- Natural language command processing via an integrated AI agent
- Legacy command support with `¬askai` prefix
- Slash command interface for modern Discord UX

### 🛠️ Server Management Tools

- List, create, and delete channels with safety confirmations
- Manage roles: assign, remove, and validate permissions
- Cross-server cloning and server reset/restore capabilities

### 🧹 Moderation Suite

- Word filtering with configurable actions: delete, warn, timeout, kick
- Anti-spam detection and mitigation
- Timeout and ban automation for rule enforcement

# ProjectChronosBot

ProjectChronosBot is an advanced AI-powered Discord bot designed to streamline server management, enhance moderation, and engage communities with intelligent features. It leverages natural language understanding and slash commands to provide a seamless and powerful user experience.

## 🚀 Features

### 🤖 AI-Powered Interaction

- Natural language command processing via an integrated AI agent
- Legacy command support with `¬askai` prefix
- Slash command interface for modern Discord UX

### 🛠️ Server Management Tools

- List, create, and delete channels with safety confirmations
- Manage roles: assign, remove, and validate permissions
- Cross-server cloning and server reset/restore capabilities

### 🧹 Moderation Suite

- Word filtering with configurable actions: delete, warn, timeout, kick
- Anti-spam detection and mitigation
- Timeout and ban automation for rule enforcement

### 🎉 Fun & Engagement

- Create interactive polls with emoji-based voting
- Timed poll results with automatic summary
- Customizable durations and options

### 🔐 Safety & Control

- Confirmation required for dangerous operations (e.g., delete all channels)
- Owner and whitelist-based command access
- Session tracking for contextual awareness

## 🧪 Testing & Validation

- Extensive test suite for all bot features
- Live and simulated test environments
- Validation scripts for schema and API integration


## 🛠️ Setup & Hosting

- `.env` configuration for secure token and your own API keys (no API keys or providers are included by default)
- `keep_alive.py` for persistent hosting (e.g., Replit)
- Hosting guide included in `KEEP_ALIVE_AND_HOSTING_GUIDE.md`

## 📄 Documentation

- [COMPLETE_COMMAND_REFERENCE.md](./project_docs/COMPLETE_COMMAND_REFERENCE.md)
- [DISCORD_INTERACTION_AND_API_FIXES.md](./project_docs/DISCORD_INTERACTION_AND_API_FIXES.md)
- [FIXES_APPLIED.md](./project_docs/FIXES_APPLIED.md)

## 📦 Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```
## 🛡️ License

MIT License
